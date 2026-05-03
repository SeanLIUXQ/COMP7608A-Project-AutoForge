# shared/constants.py - global constants imported by all modules.
import os

# Model configuration. Defaults can be overridden through .env.
LLM_PROVIDER: str = "deepseek"
LLM_MODEL_NAME: str = "deepseek-chat"
LLM_TEMPERATURE: float = 0.0

# Local embedding model. No API key is required.
EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"

# ChromaDB configuration.
CHROMA_PERSIST_DIR: str = "./data/chromadb"
CHROMA_COLLECTION_NAME: str = "autoforge_tools"

# Routing threshold.
SIMILARITY_THRESHOLD: float = 0.75

# Maximum ReAct/forge retries.
MAX_FORGE_RETRIES: int = 5

# Sandbox configuration.
SANDBOX_TIMEOUT_SECONDS: int = 30
# Default to local execution so the MVP works without Docker.
SANDBOX_BACKEND: str = "local"

# FastAPI.
BACKEND_HOST: str = "0.0.0.0"
BACKEND_PORT: int = 8000
BACKEND_SKILLS_DIR: str = os.getenv("AUTOFORGE_SKILLS_DIR", "skills")
RETRIEVAL_TOP_K: int = 5
DEFAULT_QUERY_STRATEGY: str = "full"

# Evaluation.
EVAL_DATASET_PATH: str = "evaluation/benchmark/dataset.json"
EVAL_RESULTS_DIR: str = "evaluation/results"
FUZZY_MATCH_TOLERANCE: float = 0.01
