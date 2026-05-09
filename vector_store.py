import json
import os
import pickle
import numpy as np

_index = None
_catalog = None
_model = None

def get_resources():
    global _index, _catalog, _model
    if _index is None:
        import faiss
        from sentence_transformers import SentenceTransformer
        _index = faiss.read_index("faiss_index/index.bin")
        with open("faiss_index/catalog.pkl", "rb") as f:
            _catalog = pickle.load(f)
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _index, _catalog, _model

def build_index():
    try:
        import faiss
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("Install : pip install faiss-cpu sentence-transformers")
        return

    
    if not os.path.exists("shl_product_catalog.json"):
        print("catalog.json not found! First run scraper.py.")
        return

    with open("shl_product_catalog.json", "r", encoding="utf-8") as f:
        raw_catalog = json.load(f)

    catalog = []
    texts = []
    for item in raw_catalog:
        mapped = {
            "name": item.get("name", ""),
            "url": item.get("link", ""),
            "description": item.get("description", ""),
            "test_types": item.get("keys", []),
            "remote_testing": item.get("remote") == "yes",
            "adaptive": item.get("adaptive") == "yes"
        }
        catalog.append(mapped)

        text = f"{mapped['name']}. "
        if mapped.get("description"):
            text += mapped["description"]
        if mapped.get("test_types"):
            text += f" Test types: {', '.join(mapped['test_types'])}."
        if mapped.get("remote_testing"):
            text += " Remote testing available."
        if mapped.get("adaptive"):
            text += " Adaptive/IRT."
        texts.append(text)


    print("Embeddings creating...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model.encode(texts, show_progress_bar=True, normalize_embeddings=True)

    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(np.array(embeddings, dtype="float32"))

    os.makedirs("faiss_index", exist_ok=True)
    faiss.write_index(index, "faiss_index/index.bin")
    with open("faiss_index/catalog.pkl", "wb") as f:
        pickle.dump(catalog, f)
    with open("faiss_index/texts.pkl", "wb") as f:
        pickle.dump(texts, f)

    print(f"FAISS index saved in faiss_index/ folder!")
    print(f"Total vectors: {index.ntotal}")


def search(query: str, top_k: int = 10):
    try:
        import faiss
        from sentence_transformers import SentenceTransformer
    except ImportError:
        return []

    if not os.path.exists("faiss_index/index.bin"):
        print("Index not found! First run vector_store.py.")
        return []

    index, catalog, model = get_resources()
    q_embed = model.encode([query], normalize_embeddings=True)

    scores, indices = index.search(np.array(q_embed, dtype="float32"), top_k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < len(catalog):
            item = catalog[idx].copy()
            item["score"] = float(score)
            results.append(item)

    return results


if __name__ == "__main__":
    build_index()
    print("\nTest search: 'Java developer'")
    results = search("Java developer programming test")
    for r in results[:3]:
        print(f"  - {r['name']} (score: {r['score']:.3f})")
