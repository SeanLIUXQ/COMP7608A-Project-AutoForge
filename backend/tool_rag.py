from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Any, Optional

from shared.constants import CHROMA_COLLECTION_NAME, CHROMA_PERSIST_DIR, EMBEDDING_MODEL_NAME
from shared.schemas import ToolSchema


@dataclass
class RetrievalHit:
    tool_id: str
    similarity: float
    tool: ToolSchema


class EmbeddingModel:
    """Lazy-loaded sentence-transformers encoder (thread-safe)."""

    def __init__(self, model_name: str = EMBEDDING_MODEL_NAME) -> None:
        self._model_name = model_name
        self._model = None
        self._lock = Lock()

    def encode(self, text: str) -> list[float]:
        with self._lock:
            if self._model is None:
                from sentence_transformers import SentenceTransformer

                self._model = SentenceTransformer(self._model_name)
        vec = self._model.encode([text], normalize_embeddings=True)[0]
        return vec.tolist()


def _tool_from_metadata(meta: dict[str, Any]) -> ToolSchema:
    raw_schema = meta.get("json_schema") or "{}"
    if isinstance(raw_schema, str):
        json_schema = json.loads(raw_schema)
    else:
        json_schema = dict(raw_schema)
    from shared.schemas import ToolParameter

    params_raw = meta.get("parameters_json") or "[]"
    if isinstance(params_raw, str):
        plist = json.loads(params_raw)
    else:
        plist = params_raw
    parameters = [ToolParameter(**p) for p in plist]
    return ToolSchema(
        tool_id=str(meta["tool_id"]),
        name=str(meta["name"]),
        description=str(meta.get("description") or ""),
        parameters=parameters,
        source_code=str(meta.get("source_code") or ""),
        json_schema=json_schema,
    )


def _metadata_for_tool(tool: ToolSchema) -> dict[str, str]:
    return {
        "tool_id": tool.tool_id,
        "name": tool.name,
        "description": tool.description,
        "source_code": tool.source_code,
        "json_schema": json.dumps(tool.json_schema, ensure_ascii=False),
        "parameters_json": json.dumps([p.model_dump() for p in tool.parameters], ensure_ascii=False),
    }


class ToolRAG:
    """ChromaDB-backed semantic index over tool descriptions (docstrings)."""

    def __init__(
        self,
        persist_dir: str | Path = CHROMA_PERSIST_DIR,
        collection_name: str = CHROMA_COLLECTION_NAME,
    ) -> None:
        try:
            import chromadb
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "chromadb is required for ToolRAG. Install dependencies from requirements.txt."
            ) from exc
        self._persist_dir = Path(persist_dir)
        self._persist_dir.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=str(self._persist_dir))
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        self._embedder = EmbeddingModel()

    def embed_query(self, text: str) -> list[float]:
        return self._embedder.encode(text)

    def upsert_tool(self, tool: ToolSchema) -> None:
        emb = self._embedder.encode(tool.description)
        self._collection.upsert(
            ids=[tool.tool_id],
            documents=[tool.description],
            embeddings=[emb],
            metadatas=[_metadata_for_tool(tool)],
        )

    def delete_tool(self, tool_id: str) -> None:
        try:
            self._collection.delete(ids=[tool_id])
        except Exception:
            pass

    def similarity_from_distance(self, distance: float) -> float:
        # Chroma cosine space: distance = 1 - cosine_similarity for normalized vectors.
        return max(0.0, min(1.0, 1.0 - float(distance)))

    def retrieve_best(self, query_text: str) -> Optional[RetrievalHit]:
        emb = self._embedder.encode(query_text)
        res = self._collection.query(
            query_embeddings=[emb],
            n_results=1,
            include=["distances", "metadatas"],
        )
        ids = res.get("ids") or []
        if not ids or not ids[0]:
            return None
        dists = res.get("distances") or []
        metas = res.get("metadatas") or []
        if not dists or not dists[0] or not metas or not metas[0]:
            return None
        meta = metas[0][0]
        if not meta:
            return None
        dist = dists[0][0]
        sim = self.similarity_from_distance(dist)
        tool = _tool_from_metadata(meta)
        return RetrievalHit(tool_id=tool.tool_id, similarity=sim, tool=tool)

    def load_all_tools(self) -> list[ToolSchema]:
        data = self._collection.get(include=["metadatas"])
        metas = data.get("metadatas") or []
        out: list[ToolSchema] = []
        for m in metas:
            if not m:
                continue
            try:
                out.append(_tool_from_metadata(m))
            except Exception:
                continue
        return out
