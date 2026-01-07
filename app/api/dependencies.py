from fastapi import Request, HTTPException
from app.storage.do_spaces import DOSpacesHandler

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