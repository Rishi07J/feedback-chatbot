import faiss
import numpy as np
from sentence_transformers import SentenceTransformer, util
from mongo_utils import get_upvoted_prompt_response_pairs

# Load embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# Global index and prompt-response map
faiss_index = None
prompt_response_map = []

def build_faiss_index():
    """Build FAISS index from feedback data."""
    global faiss_index, prompt_response_map
    print("📡 Rebuilding FAISS index from feedback...")

    pairs = get_upvoted_prompt_response_pairs()
    prompt_response_map = pairs

    if not pairs:
        print("⚠️ No feedback data found.")
        return

    prompts = [p for p, _ in pairs]
    embeddings = embedding_model.encode(prompts, convert_to_numpy=True)

    dimension = embeddings.shape[1]
    faiss_index = faiss.IndexFlatL2(dimension)
    faiss_index.add(embeddings)

    print(f"✅ Built FAISS index with {len(prompts)} entries.")

def initialize_faiss():
    build_faiss_index()

def search_similar_prompt(query: str, top_k: int = 5, similarity_threshold: float = 0.6) -> str | None:
    """
    Search top-k prompts via FAISS, re-rank using cosine similarity.
    Returns best response if cosine similarity exceeds threshold.
    """
    global faiss_index, prompt_response_map

    if faiss_index is None or not prompt_response_map:
        print("⚠️ Empty FAISS index. Rebuilding...")
        build_faiss_index()
        if faiss_index is None:
            return None

    # Step 1: Retrieve top_k from FAISS
    query_vec = embedding_model.encode([query], convert_to_numpy=True)
    distances, indices = faiss_index.search(query_vec, top_k)

    print("\n🔍 Top results from FAISS:")
    for rank, (idx, dist) in enumerate(zip(indices[0], distances[0])):
        if idx < len(prompt_response_map):
            print(f"{rank+1}. \"{prompt_response_map[idx][0][:60]}...\" (L2 distance: {dist:.4f})")

    # Step 2: Extract candidate prompt-response pairs
    candidates = [(prompt_response_map[idx][0], prompt_response_map[idx][1])
                  for idx in indices[0] if idx < len(prompt_response_map)]

    if not candidates:
        return None

    # Step 3: Rerank using cosine similarity
    query_tensor = embedding_model.encode(query, convert_to_tensor=True)
    candidate_prompts = [p for p, _ in candidates]
    candidate_tensors = embedding_model.encode(candidate_prompts, convert_to_tensor=True)

    cosine_scores = util.pytorch_cos_sim(query_tensor, candidate_tensors)[0]
    best_idx = int(np.argmax(cosine_scores))
    best_score = float(cosine_scores[best_idx])

    print("\n🔁 Reranked (cosine similarity):")
    for i, (p, _) in enumerate(candidates):
        print(f"{i+1}. \"{p[:60]}...\" (cosine: {cosine_scores[i]:.4f})")

    # Threshold check
    if best_score < similarity_threshold:
        print(f"⛔ Best cosine similarity {best_score:.4f} is below threshold {similarity_threshold}")
        return None

    print(f"✅ Selected response with cosine similarity: {best_score:.4f}")
    return candidates[best_idx][1]

def add_to_faiss_index(prompt: str, response: str):
    """Add a new prompt-response pair to the FAISS index."""
    global faiss_index, prompt_response_map

    new_embedding = embedding_model.encode([prompt], convert_to_numpy=True)

    if faiss_index is None:
        print("⚠️ FAISS index missing. Creating new one...")
        dimension = new_embedding.shape[1]
        faiss_index = faiss.IndexFlatL2(dimension)
        prompt_response_map = []

    faiss_index.add(new_embedding)
    prompt_response_map.append((prompt, response))
    print("➕ New entry added to FAISS index.")

def get_all_prompt_vectors(preview: bool = True):
    """
    Return all stored prompts and their vectors for inspection.
    If `preview=True`, prints first few entries.
    """
    prompts = [p for p, _ in prompt_response_map]
    vectors = embedding_model.encode(prompts, convert_to_numpy=True)

    zipped = list(zip(prompts, vectors))

    if preview:
        print("\n📊 Stored Prompt Vectors (first 5):")
        for i, (p, vec) in enumerate(zipped[:5]):
            print(f"{i+1}. \"{p[:60]}...\" → vector[:5] = {vec[:5]}")
        print(f"Total vectors stored: {len(zipped)}")

    return zipped

def get_top_similar_prompts(query: str, top_k: int = 3) -> list[str]:
    """Return top-k most similar prompts (not responses)."""
    global faiss_index, prompt_response_map

    if faiss_index is None or not prompt_response_map:
        build_faiss_index()

    query_vec = embedding_model.encode([query], convert_to_numpy=True)
    distances, indices = faiss_index.search(query_vec, top_k)
    return [prompt_response_map[i][0] for i in indices[0] if i < len(prompt_response_map)]
