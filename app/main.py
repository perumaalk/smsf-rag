from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api import query, health
from app.core.config import settings
from app.engine.query_engine import get_smsf_query_engine
# We store the engine here to avoid re-initializing it on every request
engine_container = {}

import qdrant_client
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.vector_stores.qdrant import QdrantVectorStore

@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP
    try:
        # 1. Initialize the Qdrant Client
        client = qdrant_client.QdrantClient(
            url=settings.QDRANT_URL, 
            api_key=settings.QDRANT_API_KEY # Use your env variable name
        )
        
        # 2. Setup the Vector Store for your specific collection
        vector_store = QdrantVectorStore(
            client=client, 
            collection_name="your_collection_name" # Update this
        )
        
        # 3. Connect the Index to the existing Vector Store
        # This does NOT re-index your data; it just connects to it
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        index = VectorStoreIndex.from_vector_store(
            vector_store=vector_store, 
            storage_context=storage_context
        )
        
        # 4. Store it in app.state so other files can find it
        app.state.vector_index = index
        print("Successfully connected to Qdrant Index.")
        
    except Exception as e:
        print(f"CRITICAL: Failed to initialize Qdrant Index: {e}")
        raise e
        
    yield
    # SHUTDOWN
    app.state.vector_index = None
    
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # # STARTUP: Connect to Qdrant & build the Query Engine
#     # print(f"Connecting to Qdrant at {settings.QDRANT_URL}...")
#     # engine_container["query_engine"] = get_smsf_query_engine()
#     # yield
#     # # SHUTDOWN: Clean up resources if necessary
#     # engine_container.clear()
#     # STARTUP
#     try:
#         print(f"Connecting to Qdrant at {settings.QDRANT_URL}...")
#         # This calls your updated helper function
#         engine_container["query_engine"] = get_smsf_query_engine()
#         print("Query engine initialized successfully.")
#     except Exception as e:
#         print(f"CRITICAL: Failed to initialize query engine: {e}")
#         # On Render, failing here will show up clearly in logs
#         raise e 
#     yield
#     # SHUTDOWN
#     engine_container.clear()

app = FastAPI(
    title="SMSF RAG API",
    version="1.0.0",
    lifespan=lifespan
)

# Include Routers
app.include_router(query.router, prefix="/api", tags=["Query"])
app.include_router(health.router, prefix="/api", tags=["System"])

@app.get("/")
async def root():
    return {"message": "SMSF RAG API is running. Visit /docs for API documentation."}