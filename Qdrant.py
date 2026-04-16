from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from main import embedding

QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "ICKAS"
VECTOR_DIM = 384  

client = QdrantClient(url=QDRANT_URL)


def ensure_collection():
    """Create collection if it doesn't exist with correct dimensions."""
    existing = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME not in existing:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_DIM, distance=Distance.COSINE),
        )


# Vectorstore
def store_documents(docs):
    ensure_collection()
    QdrantVectorStore.from_documents(
        documents=docs,
        embedding=embedding,
        url=QDRANT_URL,
        collection_name=COLLECTION_NAME,
    )


# Retriever - Get retriever from Qdrant
def get_retriever():
    ensure_collection()
    vectorstore = QdrantVectorStore(
        client=client,
        collection_name=COLLECTION_NAME,
        embedding=embedding,
    )
    return vectorstore.as_retriever() 

