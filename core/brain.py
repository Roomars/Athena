import hashlib
from pathlib import Path
from typing import Optional

import chromadb
import httpx

VAULT_PATH = Path.home() / "Library/CloudStorage/GoogleDrive-roberto.verzeletti.87@gmail.com/Il mio Drive/AI_Brain"
CHROMA_PATH = Path(__file__).parent.parent / "brain" / "chroma"
EMBED_MODEL = "nomic-embed-text"
OLLAMA_BASE = "http://localhost:11434"

# Cartelle da ignorare nel vault
SKIP_DIRS = {".obsidian", "Output"}

_client: Optional[chromadb.ClientAPI] = None
_collection = None


def _get_collection():
    global _client, _collection
    if _collection is None:
        CHROMA_PATH.mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(path=str(CHROMA_PATH))
        _collection = _client.get_or_create_collection(
            name="athena_brain",
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def _embed(text: str) -> list[float]:
    response = httpx.post(
        f"{OLLAMA_BASE}/api/embeddings",
        json={"model": EMBED_MODEL, "prompt": text},
        timeout=30.0,
    )
    response.raise_for_status()
    return response.json()["embedding"]


def _chunk(text: str, size: int = 500, overlap: int = 50) -> list[str]:
    words = text.split()
    chunks, i = [], 0
    while i < len(words):
        chunks.append(" ".join(words[i : i + size]))
        i += size - overlap
    return chunks


def _file_id(path: Path, chunk_idx: int) -> str:
    return hashlib.md5(f"{path}:{chunk_idx}".encode()).hexdigest()


def index_file(path: Path) -> int:
    """Embeds a markdown file into ChromaDB. Returns number of chunks indexed."""
    try:
        text = path.read_text(encoding="utf-8", errors="ignore").strip()
    except Exception:
        return 0
    if not text:
        return 0

    col = _get_collection()
    ambito = path.parts[len(VAULT_PATH.parts)] if len(path.parts) > len(VAULT_PATH.parts) else "root"
    chunks = _chunk(text)

    ids, embeddings, documents, metadatas = [], [], [], []
    for i, chunk in enumerate(chunks):
        ids.append(_file_id(path, i))
        embeddings.append(_embed(chunk))
        documents.append(chunk)
        metadatas.append({
            "source": str(path.relative_to(VAULT_PATH)),
            "ambito": ambito,
            "file": path.name,
        })

    col.upsert(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)
    return len(chunks)


def remove_file(path: Path) -> None:
    """Removes all chunks of a file from ChromaDB."""
    col = _get_collection()
    results = col.get(where={"source": str(path.relative_to(VAULT_PATH))})
    if results["ids"]:
        col.delete(ids=results["ids"])


def search(query: str, n_results: int = 4) -> list[dict]:
    """Returns the top n_results chunks most relevant to the query."""
    col = _get_collection()
    if col.count() == 0:
        return []
    embedding = _embed(query)
    results = col.query(
        query_embeddings=[embedding],
        n_results=min(n_results, col.count()),
        include=["documents", "metadatas", "distances"],
    )
    out = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        if dist < 0.7:  # filtra risultati troppo distanti
            out.append({"text": doc, "source": meta["source"], "ambito": meta["ambito"]})
    return out


def index_vault() -> int:
    """Initial full index of the vault. Returns total chunks indexed."""
    total = 0
    for md_file in VAULT_PATH.rglob("*.md"):
        if any(skip in md_file.parts for skip in SKIP_DIRS):
            continue
        total += index_file(md_file)
    return total


def stats() -> dict:
    col = _get_collection()
    return {"chunks": col.count(), "vault": str(VAULT_PATH)}
