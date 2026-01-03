from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api import query, health
from app.core.config import settings
from app.engine.query_engine import get_smsf_query_engine
# We store the engine here to avoid re-initializing it on every request
engine_container = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP: Connect to Qdrant & build the Query Engine
    print(f"Connecting to Qdrant at {settings.QDRANT_URL}...")
    engine_container["query_engine"] = get_smsf_query_engine()
    yield
    # SHUTDOWN: Clean up resources if necessary
    engine_container.clear()

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