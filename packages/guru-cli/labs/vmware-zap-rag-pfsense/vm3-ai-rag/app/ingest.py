"""
THMD-Guru LAB — VM3: nạp kho tri thức (kb/) vào Qdrant bằng embedding của Ollama.
Chạy lại mỗi khi thêm tài liệu vào kb/:   python3 -m app.ingest
"""
import os
import sys

from .rag_engine import KnowledgeBase, Ollama, http_json

QDRANT = os.environ.get("QDRANT_URL", "http://127.0.0.1:6333").rstrip("/")
COLLECTION = "thmd_lab_kb"


def main() -> None:
    kb = KnowledgeBase()
    ol = Ollama(os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434"),
                os.environ.get("LLM_MODEL", "qwen2.5:3b"), os.environ.get("EMBED_MODEL", "nomic-embed-text"))
    try:
        vectors = [ol.embed(c["text"]) for c in kb.chunks]
    except Exception as e:  # noqa: BLE001
        sys.exit(f"[ERR] Không lấy được embedding từ Ollama ({e}). Đã 'ollama pull {ol.embed_model}' chưa?")
    dim = len(vectors[0])
    try:  # tạo lại collection sạch
        http_json(f"{QDRANT}/collections/{COLLECTION}", method="DELETE")
    except Exception:  # noqa: BLE001
        pass
    http_json(f"{QDRANT}/collections/{COLLECTION}", {"vectors": {"size": dim, "distance": "Cosine"}}, method="PUT")
    points = [{"id": i, "vector": v, "payload": {"chunk_id": c["id"], "cwe_id": c.get("cwe_id", ""), "text": c["text"]}}
              for i, (c, v) in enumerate(zip(kb.chunks, vectors))]
    http_json(f"{QDRANT}/collections/{COLLECTION}/points?wait=true", {"points": points}, method="PUT")
    print(f"[OK] Đã nạp {len(points)} đoạn tri thức (dim={dim}) vào Qdrant {QDRANT}/collections/{COLLECTION}")


if __name__ == "__main__":
    main()
