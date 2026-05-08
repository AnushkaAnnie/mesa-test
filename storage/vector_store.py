import os
from dotenv import load_dotenv

load_dotenv()

USE_PINECONE = bool(os.getenv("PINECONE_API_KEY"))

if USE_PINECONE:
    from storage.pinecone_store import save_pr, search_similar
    print("[VectorStore] Using Pinecone")
else:
    import chromadb
    import voyageai

    voyage = voyageai.Client(api_key=os.getenv("VOYAGE_API_KEY"))
    chroma_client = chromadb.Client()
    collection = chroma_client.get_or_create_collection("past_prs")

    def embed_text(text: str):
        result = voyage.embed([text], model="voyage-code-2")
        return result.embeddings[0]

    def save_pr(pr_id: str, text: str, metadata: dict = {}):
        embedding = embed_text(text)
        collection.add(
            embeddings=[embedding],
            documents=[text],
            ids=[pr_id],
            metadatas=[metadata],
        )
        print(f"[ChromaDB] Saved PR {pr_id}")

    def search_similar(query: str, n: int = 3):
        query_embedding = embed_text(query)
        return collection.query(query_embeddings=[query_embedding], n_results=n)

    print("[VectorStore] Using ChromaDB (local)")


if __name__ == "__main__":
    save_pr("pr_1", "Added input validation to user login endpoint")
    save_pr("pr_2", "Removed authentication check from admin route")
    results = search_similar("authentication and security changes")
    print("Results:", results["documents"])
