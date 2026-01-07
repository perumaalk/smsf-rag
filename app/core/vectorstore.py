import qdrant_client
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core import VectorStoreIndex, StorageContext
from app.core.config import settings

# 1. Initialize the Actual Qdrant Client (pointing to Cloud)
client = qdrant_client.QdrantClient(
    url=settings.QDRANT_URL,
    api_key=settings.QDRANT_API_KEY,
    timeout=60
)

# 2. Define the Vector Store
# This is where the 'not defined' error was happening
vector_store = QdrantVectorStore(
    client=client, 
    collection_name="smsf_docs"
)

# 3. Setup Storage Context
storage_context = StorageContext.from_defaults(vector_store=vector_store)

# 4. Initialize Index
# If you already have data in the cloud, use 'from_vector_store' 
# to avoid re-uploading every time Render restarts.
index = VectorStoreIndex.from_vector_store(
    vector_store=vector_store,
    storage_context=storage_context
)

# 5. Query Engine with Filters
query_engine = index.as_query_engine(
    similarity_top_k=6,
    filters=None # We will define metadata filters during actual queries
)