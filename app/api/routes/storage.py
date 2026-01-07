from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from app.api.dependencies import get_storage_handler, get_index
from app.storage.do_spaces import DOSpacesHandler
from llama_index.core import Document

router = APIRouter()

@router.get("/files")
async def list_available_files(
    handler: DOSpacesHandler = Depends(get_storage_handler)):
    # 'handler' is automatically provided by the dependency
    files = handler.list_files()
    return {"files": files}

# @router.post("/process-selected")
# async def process_file(
#     file_key: str, 
#     index = Depends(get_index), 
#     handler = Depends(get_storage_handler)
# ):
#     # Now you have access to both the storage and the RAG index!
#     content = handler.get_file_content(file_key)
#     # logic to update index...
#     return {"message": f"Processing {file_key}"}
@router.post("/process-selected")
async def process_file(
    file_key: str, 
    index = Depends(get_index), 
    handler: DOSpacesHandler = Depends(get_storage_handler)
):
    """
    1. Downloads file from DigitalOcean Spaces.
    2. Indexes content into Qdrant vector store.
    3. Automatically updates registry.json on success.
    """
    # 1. Fetch file content
    content = handler.get_file_content(file_key)
    if not content:
        raise HTTPException(status_code=404, detail=f"File {file_key} not found.")

    try:
        # 2. Index into Qdrant using LlamaIndex
        # (Assuming text content; update parser if using PDFs)
        text_content = content.decode('utf-8')
        doc = Document(
            text=text_content, 
            metadata={
                "file_name": file_key,
                "category": "smsf_document",
                "processed_at": datetime.utcnow().isoformat()
            }
        )
        
        # Upsert to Qdrant via the index
        index.insert(doc)
        
        # 3. SUCCESS: Update the registry.json file
        registry = handler.get_registry()
        
        # Remove old entry if it exists to avoid duplicates
        registry["indexed_files"] = [f for f in registry.get("indexed_files", []) if f["name"] != file_key]
        
        # Add new entry
        new_entry = {
            "name": file_key,
            "indexed_at": datetime.utcnow().isoformat(),
            "status": "completed",
            "metadata": {
                "source": "digitalocean_spaces",
                "target": "qdrant_collection"
            }
        }
        registry["indexed_files"].append(new_entry)
        
        # Save back to Spaces
        handler.save_registry(registry)
        
        return {
            "message": f"Successfully indexed {file_key} and updated registry.",
            "status": "success"
        }

    except Exception as e:
        # Log error and return failure
        print(f"Error during processing: {e}")
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")

@router.get("/registry")
async def get_index_registry(handler: DOSpacesHandler = Depends(get_storage_handler)):
    """Returns the list of files already indexed in Qdrant."""
    return handler.get_registry()

@router.post("/registry/update")
async def update_registry_status(
    file_key: str, 
    status: str = "completed",
    handler: DOSpacesHandler = Depends(get_storage_handler)
):
    """
    Updates the registry.json with a new indexed file entry.
    """
    registry = handler.get_registry()
    
    # Check if file already exists in registry to avoid duplicates
    existing_entry = next((f for f in registry["indexed_files"] if f["name"] == file_key), None)
    
    new_entry = {
        "name": file_key,
        "indexed_at": datetime.utcnow().isoformat(),
        "status": status,
        "provider": "digitalocean_spaces",
        "metadata": {
            "upsert_type": "qdrant_vector_index"
        }
    }

    if existing_entry:
        registry["indexed_files"].remove(existing_entry)
    
    registry["indexed_files"].append(new_entry)
    
    success = handler.save_registry(registry)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update registry file")
    
    return {"message": f"Registry updated for {file_key}", "entry": new_entry}