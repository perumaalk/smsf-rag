from fastapi import APIRouter, Depends, HTTPException, Query
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
    # JSON will look like this:from datetime import datetime
    # {
    # "files": [
    #     {
    #     "name": "SIS_Act_VOL_01_2025.pdf",
    #     "path": "legislation/SIS_Act_VOL_01_2025.pdf",
    #     "size": 1349284,
    #     "last_modified": "2026-01-06T06:43:18+00:00",
    #     "download_url": "https://your-bucket.nyc3.digitaloceanspaces.com/legislation/SIS_Act_VOL_01_2025.pdf?AWSAccessKeyId=..."
    #     }
    # ]
    # }

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

@router.get("/download")
async def get_file_download_link(
    file_key: str = Query(..., description="The full path of the file to download"),
    handler: DOSpacesHandler = Depends(get_storage_handler) ):
    url = handler.generate_download_url(file_key)
    
    if not url:
        raise HTTPException(status_code=500, detail="Could not generate download link")
        
    return {"download_url": url}

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
    # 1. Get (Returns template if file doesn't exist)
    registry = handler.get_registry()
    
    # 2. Modify
    new_entry = {
        "name": file_key,
        "indexed_at": datetime.utcnow().isoformat(),
        "status": status,
        "metadata": {"upsert_type": "qdrant_vector_index"}
    }
    
    # Update existing or add new
    registry["indexed_files"] = [f for f in registry["indexed_files"] if f["name"] != file_key]
    registry["indexed_files"].append(new_entry)
    
    # 3. Save
    if not handler.save_registry(registry):
        raise HTTPException(status_code=500, detail="Failed to write registry to cloud")
    
    return {"status": "success", "file": file_key}

@router.delete("/files/delete")
async def delete_file_and_registry_entry(
    file_key: str, 
    handler: DOSpacesHandler = Depends(get_storage_handler)
):
    # 1. Delete the physical file from DigitalOcean
    # Note: S3 delete_object returns success even if the file doesn't exist
    physical_delete_success = handler.delete_file(file_key)
    
    if not physical_delete_success:
        raise HTTPException(status_code=500, detail="Failed to delete file from storage")

    # 2. Update the registry
    registry = handler.get_registry()
    
    # Check if the file actually exists in the registry
    original_count = len(registry.get("indexed_files", []))
    
    # Filter out the deleted file
    registry["indexed_files"] = [
        f for f in registry.get("indexed_files", []) 
        if f["name"] != file_key
    ]
    
    # 3. Save the updated registry back to the Space
    if len(registry["indexed_files"]) != original_count:
        save_success = handler.save_registry(registry)
        if not save_success:
            raise HTTPException(status_code=500, detail="File deleted, but failed to update registry")
    
    return {
        "status": "success", 
        "message": f"Deleted {file_key} from storage and registry"
    }
# How to call it
# Use a DELETE request in your API client (like Postman or your frontend): 
# DELETE /files/delete?file_key=legislation/SIS_Act_VOL_01_2025.pdf
