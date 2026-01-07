# To call it from your API (app/api/ingestion_endpoints.py):

import os
import shutil
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException

# Import the logic from your ingestion folder
from ingestion.ato_ruling import ingest_ato_ruling
from ingestion.trust_deed import process_trust_deed_upload

# Initialize the router
router = APIRouter(prefix="/ingest", tags=["Ingestion"])

@router.post("/ruling")
async def api_ingest_ruling(
    ruling_id: str, 
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Endpoint for ATO Rulings. 
    Saves a local temp copy and triggers the ingestion logic.
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    # Create a local path for processing
    temp_dir = "./data/temp_uploads"
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, f"ruling_{file.filename}")
    
    # Save the uploaded file locally
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Trigger logic from the ingestion folder in the background
    background_tasks.add_task(ingest_ato_ruling, temp_path, ruling_id)
    
    return {
        "status": "Accepted", 
        "ruling_id": ruling_id, 
        "message": "Ruling ingestion started in background."
    }

@router.post("/trust-deed/{fund_id}")
async def api_ingest_trust_deed(
    fund_id: str, 
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Endpoint for Trust Deeds.
    """
    temp_dir = "./data/temp_uploads"
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, f"deed_{fund_id}_{file.filename}")

    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    background_tasks.add_task(process_trust_deed_upload, temp_path, fund_id)
    
    return {"status": "Accepted", "fund_id": fund_id}