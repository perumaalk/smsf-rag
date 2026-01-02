# 1.2 Vector Store (Qdrant) (app/core/vectorstore.py)
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

client = QdrantClient(
    url="http://localhost:6333",
    timeout=60
)

vector_store = QdrantVectorStore(
    client=client,
    collection_name="smsf_legal_docs"
)

# 1.3 Index Construction
from llama_index.core import VectorStoreIndex, StorageContext

storage_context = StorageContext.from_defaults(
    vector_store=vector_store
)

index = VectorStoreIndex.from_documents(
    documents,
    storage_context=storage_context,
    show_progress=True
)

# 1.4 Query Engine (Compliance-Safe)
query_engine = index.as_query_engine(
    similarity_top_k=6,
    response_mode="compact",
    node_postprocessors=[],
    filters={
        "doc_type": ["legislation", "ato_ruling", "trust_deed"]
    }
)
