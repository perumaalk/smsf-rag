from fastapi import APIRouter, status
import qdrant_client
from app.core.config import settings

router = APIRouter()

@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    health_status = {"status": "healthy", "checks": {}}
    
    # 1. Check Vector DB Connection (Qdrant)
    try:
        client = qdrant_client.QdrantClient(url=settings.QDRANT_URL)
        client.get_collections() # Simple ping
        health_status["checks"]["vector_db"] = "connected"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["vector_db"] = f"error: {str(e)}"
        
    # 2. Add other checks (e.g., OpenAI API reachability)
    
    return health_status