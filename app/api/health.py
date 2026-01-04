from fastapi import APIRouter, status
import qdrant_client
from app.core.config import settings

router = APIRouter()

@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    health_status = {"status": "healthy", "checks": {}}
    
    try:
        # CORRECTION: You must pass the api_key here!
        client = qdrant_client.QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY  # This was missing
        )
        client.get_collections() 
        health_status["checks"]["vector_db"] = "connected"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["vector_db"] = f"error: {str(e)}"
        
    return health_status