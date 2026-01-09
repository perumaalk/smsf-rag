from fastapi import Request, HTTPException
from app.storage.do_spaces import DOSpacesHandler

from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader
import os

API_KEY_NAME = "X-Internal-Api-Key"
api_key_header = APIKeyHeader(name="INTERNAL_API_KEY", auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key == os.getenv("INTERNAL_API_KEY"):
        return api_key
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, 
        detail="Could not validate credentials"
    )

def get_index(request: Request):
    """
    Retrieves the LlamaIndex from the app state.
    The index is initialized in main.py during lifespan startup.
    """
    index = getattr(request.app.state, "vector_index", None)
    if index is None:
        raise HTTPException(status_code=500, detail="Vector Index not initialized")
    return index

def get_storage_handler():
    """
    Returns an instance of the DigitalOcean Spaces handler.
    """
    return DOSpacesHandler()