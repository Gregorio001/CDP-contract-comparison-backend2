import os
import chromadb
from chromadb.api.models import Collection
import httpx
from statistics import mean
from typing import List, Dict, Any, Optional
from chromadb import PersistentClient  # Usa questo!

from app.config import HUGGINGFACE_API_KEY

# Configurazione modello Hugging Face
HF_EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
HF_API_URL = (
    "https://router.huggingface.co/hf-inference/models/"
    + HF_EMBED_MODEL
    + "/pipeline/feature-extraction"
)

_collection: Optional[Collection] = None


def _get_collection():
    global _collection
    if _collection is None:
        print("INFO: Connecting to Vector DB...")

        client = PersistentClient(path="cdb_storage")  # <-- corretto ora
        _collection = client.get_or_create_collection(name="historical_clauses")
    return _collection


def _embed_text_remote(text: str) -> List[float]:
    headers = {
        "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {"inputs": text}
    resp = httpx.post(HF_API_URL, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    embedding = resp.json()

    if isinstance(embedding[0], float):
        return embedding

    return [mean(dim_vals) for dim_vals in zip(*embedding)]


def find_similar_clauses(query_text: str, n_results: int = 3) -> List[Dict[str, Any]]:
    embedding = _embed_text_remote(query_text)
    collection = _get_collection()
    results = collection.query(query_embeddings=[embedding], n_results=n_results)

    formatted: List[Dict[str, Any]] = []
    if not results or not results.get("ids") or not results["ids"][0]:
        return formatted

    ids = results["ids"][0]
    distances = results["distances"][0]
    metadatas = results["metadatas"][0]
    documents = results["documents"][0]

    for idx, hist_id in enumerate(ids):
        formatted.append(
            {
                "historical_id": hist_id,
                "text": documents[idx],
                "metadata": metadatas[idx],
                "similarity_score": 1.0 - distances[idx],
            }
        )

    return formatted
