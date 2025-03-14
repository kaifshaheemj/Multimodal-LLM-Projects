from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

client = QdrantClient(url="http://localhost:6333")
collection_lst = client.get_collections()

print(len(collection_lst.collections))
for i in range(len(collection_lst.collections)):
    print(collection_lst.collections[i])

def create_user_collection(user_id):
    collection_name = f"{user_id}"
    client.recreate_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size= 1024, distance=Distance.DOT, on_disk=True)
    )
    print(f"Collection {collection_name} created.")

def store_chunk_embedding_in_db(collection_name, chunk_embeddings, chunk_texts):
    points = [
        PointStruct(
            id = i,
            vector = embedding,
            payload={"text": chunk_texts[i]}
        )
        for i, embedding in enumerate(chunk_embeddings)
    ]
    client.upsert(collection_name=collection_name, points=points)
    print(f"Stored {len(chunk_embeddings)} chunks in collection {collection_name}.")

def retrieve_from_qdrant(collection_name, query_embedding, top_k=5):
    search_results = client.search(
        collection_name=collection_name,
        query_vector=query_embedding,
        limit=top_k,
        with_payload=True
    )
    retrieved_Chunks = [
        {"text": result.payload["text"], "score": result.score} for result in search_results
    ]

    return retrieved_Chunks


