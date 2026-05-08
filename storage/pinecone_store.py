from pinecone import Pinecone, ServerlessSpec
import voyageai
import os
from dotenv import load_dotenv

load_dotenv()

voyage = voyageai.Client(api_key=os.getenv("VOYAGE_API_KEY"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))


def get_index():
    if "past-prs" not in pc.list_indexes().names():
        pc.create_index(
            "past-prs",
            dimension=1024,
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
    return pc.Index("past-prs")


def embed_text(text: str):
    result = voyage.embed([text], model="voyage-code-2")
    return result.embeddings[0]


def save_pr(pr_id: str, text: str, metadata: dict = {}):
    index = get_index()
    embedding = embed_text(text)
    index.upsert(
        vectors=[{
            "id": pr_id,
            "values": embedding,
            "metadata": {**metadata, "text": text[:1000]},
        }]
    )
    print(f"[Pinecone] Saved PR {pr_id}")


def search_similar(query: str, n: int = 3):
    index = get_index()
    embedding = embed_text(query)
    results = index.query(vector=embedding, top_k=n, include_metadata=True)
    return {
        "documents": [[m["metadata"].get("text", "") for m in results["matches"]]]
    }
