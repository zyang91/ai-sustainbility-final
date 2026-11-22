"""Settings for the research assistant (Vision Part 2)."""
from penn_ocr.config import CORPUS, WORK

RAG = WORK / "rag"                       # derived, git-ignored
PASSAGES = RAG / "passages.jsonl"
DB_DIR = RAG / "chroma"
COLLECTION = "penn_plans"

# Retrieval embeddings run in-process with sentence-transformers; the same
# vectors can be reused by the semantic analysis (Vision 1.5).
EMBED_MODEL = "BAAI/bge-base-en-v1.5"
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

# The language model runs locally in Ollama.
OLLAMA_URL = "http://127.0.0.1:11434"
LLM_MODEL = "llama3.1:8b"                # must support tool calls for the agent

PASSAGE_CHARS = 1000      # target passage length
PASSAGE_MAX = 1600        # a longer block is split at sentence ends
TOP_K = 6                 # passages given to the model for one search
PER_REPORT = 2            # passages per report when a question compares periods
TEMPERATURE = 0.1
NUM_CTX = 16384           # Ollama's default window is too small for 30 passages and cuts them off silently

PARAGRAPHS = CORPUS / "paragraphs.jsonl"
