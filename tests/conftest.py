import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RAG_SERVICE_PATH = REPO_ROOT / "services" / "rag-service"

if str(RAG_SERVICE_PATH) not in sys.path:
    sys.path.insert(0, str(RAG_SERVICE_PATH))
