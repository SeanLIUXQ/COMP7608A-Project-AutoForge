from __future__ import annotations

import json
import math
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agents.packager import create_skill_bundle
from backend.default_tools import ensure_default_skill_bundles
from shared.constants import (
    BACKEND_SKILLS_DIR,
    CHROMA_COLLECTION_NAME,
    CHROMA_PERSIST_DIR,
    EMBEDDING_MODEL_NAME,
    RETRIEVAL_TOP_K,
)
from shared.schemas import ToolParameter, ToolSchema, ToolSummary


_QUERY_STOPWORDS = {
    "a",
    "an",
    "and",
    "as",
    "by",
    "compute",
    "for",
    "from",
    "given",
    "in",
    "only",
    "payload",
    "return",
    "the",
    "then",
    "to",
    "with",
    "where",
}


@dataclass
class RegistrySearchHit:
    tool: ToolSchema
    bundle_path: Path
    score: float


class ToolRegistry:
    def __init__(
        self,
        skills_dir: str = BACKEND_SKILLS_DIR,
        chroma_persist_dir: str = CHROMA_PERSIST_DIR,
        collection_name: str = CHROMA_COLLECTION_NAME,
        embedding_model_name: str = EMBEDDING_MODEL_NAME,
        enable_vector_store: bool | None = None,
    ) -> None:
        self.skills_dir = Path(skills_dir)
        self.chroma_persist_dir = chroma_persist_dir
        self.collection_name = collection_name
        self.embedding_model_name = embedding_model_name
        if enable_vector_store is None:
            enable_vector_store = os.getenv("AUTOFORGE_ENABLE_VECTOR_STORE", "0").lower() in {
                "1",
                "true",
                "yes",
                "on",
            }
        self.enable_vector_store = enable_vector_store
        self._tools_by_id: dict[str, tuple[ToolSchema, Path, str]] = {}
        self._tool_documents: dict[str, str] = {}
        self._retrieval_backend = "lexical"
        self._encoder = None
        self._collection = None
        self._try_init_vector_store()

    @property
    def retrieval_backend(self) -> str:
        return self._retrieval_backend

    def _try_init_vector_store(self) -> None:
        if not self.enable_vector_store:
            self._retrieval_backend = "lexical"
            self._encoder = None
            self._collection = None
            return
        try:
            import chromadb
            from sentence_transformers import SentenceTransformer
        except Exception:
            self._retrieval_backend = "lexical"
            self._encoder = None
            self._collection = None
            return

        client = chromadb.PersistentClient(path=self.chroma_persist_dir)
        self._collection = client.get_or_create_collection(name=self.collection_name)
        self._encoder = SentenceTransformer(self.embedding_model_name)
        self._retrieval_backend = "chroma"

    def _load_schema(self, bundle_dir: Path) -> dict[str, Any]:
        schema_path = bundle_dir / "schema.json"
        if not schema_path.exists():
            return {}
        return json.loads(schema_path.read_text(encoding="utf-8"))

    def _read_parameters(self, schema: dict[str, Any]) -> list[ToolParameter]:
        params = schema.get("parameters", {})
        properties = params.get("properties", {})
        required = set(params.get("required", []))
        output: list[ToolParameter] = []
        for name, spec in properties.items():
            output.append(
                ToolParameter(
                    name=name,
                    type=str(spec.get("type", "string")),
                    description=str(spec.get("description", "")),
                    required=name in required,
                )
            )
        return output

    def _load_tool_from_bundle(self, bundle_dir: Path) -> tuple[ToolSchema, str]:
        metadata_path = bundle_dir / "metadata.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        source_path = bundle_dir / str(metadata.get("source_file", "tool.py"))
        source_code = source_path.read_text(encoding="utf-8")
        json_schema = self._load_schema(bundle_dir)
        parameters = self._read_parameters(json_schema)
        schema = ToolSchema(
            tool_id=str(metadata["tool_id"]),
            name=str(metadata["name"]),
            description=str(metadata.get("description", "")),
            parameters=parameters,
            source_code=source_code,
            json_schema=json_schema,
        )
        keywords = metadata.get("keywords", [])
        examples = metadata.get("examples", [])
        readme_path = bundle_dir / str(metadata.get("readme_file", "README.md"))
        readme_text = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""
        document = " ".join(
            [
                schema.name,
                schema.description,
                " ".join(str(item) for item in keywords),
                " ".join(str(item) for item in examples),
                readme_text,
            ]
        ).strip()
        return schema, document

    def _prefer_bundle(
        self,
        candidate_tool: ToolSchema,
        candidate_dir: Path,
        existing_tool: ToolSchema,
        existing_dir: Path,
    ) -> bool:
        """Choose a deterministic bundle when stale duplicate tool_ids exist on disk."""
        candidate_exact = candidate_dir.name == candidate_tool.name
        existing_exact = existing_dir.name == existing_tool.name
        if candidate_exact != existing_exact:
            return candidate_exact
        return str(candidate_dir).lower() < str(existing_dir).lower()

    def sync(self) -> None:
        ensure_default_skill_bundles(str(self.skills_dir))
        self.skills_dir.mkdir(parents=True, exist_ok=True)

        tools_by_id: dict[str, tuple[ToolSchema, Path, str]] = {}
        tool_documents: dict[str, str] = {}

        for metadata_path in self.skills_dir.rglob("metadata.json"):
            bundle_dir = metadata_path.parent
            try:
                tool, document = self._load_tool_from_bundle(bundle_dir)
            except Exception:
                continue
            existing = tools_by_id.get(tool.tool_id)
            if existing is not None:
                existing_tool, existing_dir, _existing_document = existing
                if not self._prefer_bundle(tool, bundle_dir, existing_tool, existing_dir):
                    continue
            tools_by_id[tool.tool_id] = (tool, bundle_dir, document)
            tool_documents[tool.tool_id] = document

        self._tools_by_id = tools_by_id
        self._tool_documents = tool_documents
        self._sync_vector_collection()

    def _sync_vector_collection(self) -> None:
        if not self._collection or not self._encoder:
            return
        if not self._tool_documents:
            return
        ids = list(self._tool_documents.keys())
        documents = [self._tool_documents[tool_id] for tool_id in ids]
        embeddings = self._encoder.encode(documents).tolist()
        metadatas = [{"tool_id": tool_id} for tool_id in ids]
        self._collection.upsert(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)

    def total_tools(self) -> int:
        return len(self._tools_by_id)

    def list_tools(self) -> list[ToolSummary]:
        output: list[ToolSummary] = []
        for tool_id, (tool, bundle_dir, _) in sorted(self._tools_by_id.items(), key=lambda item: item[1][0].name):
            metadata_path = bundle_dir / "metadata.json"
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            output.append(
                ToolSummary(
                    tool_id=tool_id,
                    name=tool.name,
                    description=tool.description,
                    parameters=tool.parameters,
                    keywords=[str(item) for item in metadata.get("keywords", [])],
                    metadata_version=metadata.get("metadata_version"),
                    tool_origin=metadata.get("tool_origin") or ("seeded" if metadata.get("seeded") else ("forged" if metadata.get("forged") else None)),
                    tool_status=metadata.get("tool_status"),
                )
            )
        return output

    def get_tool(self, tool_id: str) -> tuple[ToolSchema, Path] | None:
        payload = self._tools_by_id.get(tool_id)
        if not payload:
            return None
        tool, bundle_dir, _ = payload
        return tool, bundle_dir

    def get_tool_by_name(self, name: str) -> tuple[ToolSchema, Path] | None:
        for tool, bundle_dir, _document in self._tools_by_id.values():
            if tool.name == name:
                return tool, bundle_dir
        return None

    def save_tool(self, tool: ToolSchema, metadata_extra: dict[str, Any] | None = None) -> Path:
        bundle_path = create_skill_bundle(tool, base_dir=str(self.skills_dir), metadata_extra=metadata_extra)
        self.sync()
        return bundle_path

    def all_tools(self) -> list[ToolSchema]:
        return [tool for tool, _bundle_dir, _document in self._tools_by_id.values()]

    def tool_document(self, tool_id: str) -> str | None:
        return self._tool_documents.get(tool_id)

    def _strip_query_literals(self, text: str) -> str:
        """Keep retrieval focused on user intent instead of benchmark payload values."""
        without_quotes = re.sub(r"'[^']*'|\"[^\"]*\"", " ", text)
        without_brackets = re.sub(r"\[[^\]]*\]|\{[^}]*\}", " ", without_quotes)
        return without_brackets

    def _tokenize(self, text: str, *, strip_literals: bool = False) -> set[str]:
        normalized = self._strip_query_literals(text) if strip_literals else text
        tokens = set(re.findall(r"[a-z0-9_]+", normalized.lower()))
        return {token for token in tokens if not token.isdigit() and token not in _QUERY_STOPWORDS}

    def _lexical_score(self, query: str, document: str) -> float:
        query_tokens = self._tokenize(query, strip_literals=True)
        document_tokens = self._tokenize(document)
        if not query_tokens or not document_tokens:
            return 0.0
        overlap = len(query_tokens & document_tokens) / len(query_tokens)
        length_ratio = min(len(query_tokens), len(document_tokens)) / max(len(query_tokens), len(document_tokens))
        return round((overlap * 0.8) + (length_ratio * 0.2), 4)

    def _vector_search(self, query: str, top_k: int) -> list[RegistrySearchHit]:
        if not self._collection or not self._encoder or not self._tool_documents:
            return []
        embedding = self._encoder.encode([query]).tolist()
        result = self._collection.query(query_embeddings=embedding, n_results=min(top_k, len(self._tool_documents)))
        ids = result.get("ids", [[]])[0]
        distances = result.get("distances", [[]])[0]
        hits: list[RegistrySearchHit] = []
        for tool_id, distance in zip(ids, distances):
            payload = self._tools_by_id.get(tool_id)
            if not payload:
                continue
            tool, bundle_dir, _ = payload
            score = max(0.0, 1.0 - float(distance))
            hits.append(RegistrySearchHit(tool=tool, bundle_path=bundle_dir, score=round(score, 4)))
        return hits

    def _lexical_search(self, query: str, top_k: int) -> list[RegistrySearchHit]:
        ranked: list[RegistrySearchHit] = []
        for tool_id, (tool, bundle_dir, document) in self._tools_by_id.items():
            ranked.append(
                RegistrySearchHit(
                    tool=tool,
                    bundle_path=bundle_dir,
                    score=self._lexical_score(query, document),
                )
            )
        ranked.sort(key=lambda item: (-item.score, item.tool.name))
        return ranked[:top_k]

    def debug_scores(self, query: str, tool_ids: list[str] | None = None) -> dict[str, dict[str, float]]:
        """
        Return per-backend scores for debugging/trace views.

        Keys:
          - lexical: intent-focused overlap score (always available)
          - chroma: vector score in [0,1] when the vector store is active; else empty
        """
        if not self._tools_by_id:
            self.sync()
        allowed = set(tool_ids) if tool_ids else None

        lexical: dict[str, float] = {}
        for tool_id, (_tool, _bundle_dir, document) in self._tools_by_id.items():
            if allowed is not None and tool_id not in allowed:
                continue
            lexical[tool_id] = self._lexical_score(query, document)

        chroma: dict[str, float] = {}
        if self._collection and self._encoder:
            # Query top_k large enough to cover all requested tools when possible.
            top_k = len(allowed) if allowed is not None else RETRIEVAL_TOP_K
            for hit in self._vector_search(query, top_k=max(1, min(top_k, max(1, len(self._tool_documents))))):
                if allowed is not None and hit.tool.tool_id not in allowed:
                    continue
                chroma[hit.tool.tool_id] = hit.score

        return {"lexical": lexical, "chroma": chroma}

    def search(self, query: str, top_k: int = RETRIEVAL_TOP_K) -> list[RegistrySearchHit]:
        if not self._tools_by_id:
            self.sync()
        hits = self._vector_search(query, top_k) if self._retrieval_backend == "chroma" else []
        if hits:
            return hits
        self._retrieval_backend = "lexical" if not self._collection else self._retrieval_backend
        return self._lexical_search(query, top_k)
