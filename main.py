from contextlib import asynccontextmanager
from fastapi import FastAPI
import qdrant_client
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.vector_stores.qdrant import QdrantVectorStore

# Correct Absolute Imports
from app.api.routes import query
from app.api.routes import health
from app.api.routes import storage
# from app.api.routes.storage import router as storage_router
from app.core.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP
    try:
        client = qdrant_client.QdrantClient(
            url=settings.QDRANT_URL, 
            api_key=settings.QDRANT_API_KEY
        )
        
        vector_store = QdrantVectorStore(
            client=client, 
            collection_name="smsf_documents" # Ensure this matches your setup
        )
        
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        index = VectorStoreIndex.from_vector_store(
            vector_store=vector_store, 
            storage_context=storage_context
        )
        
        app.state.vector_index = index
        print("Successfully connected to Qdrant Index.")
        
    except Exception as e:
        print(f"CRITICAL: Failed to initialize Qdrant Index: {e}")
        raise e
        
    yield
    # SHUTDOWN
    app.state.vector_index = None

app = FastAPI(
    title="SMSF RAG API",
    version="1.0.0",
    lifespan=lifespan
)

# Include Routers with consistent prefixing
app.include_router(query.router, prefix="/api", tags=["Query"])
app.include_router(health.router, prefix="/api", tags=["System"])
app.include_router(storage.router, prefix="/api", tags=["Storage"])

@app.get("/")
async def root():
    return {"message": "SMSF RAG API is running. Visit /docs for API documentation."}