from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.engine.query_engine import get_smsf_query_engine

# 1. This defines the 'router' attribute that Render is looking for
router = APIRouter()

# 2. Define what a 'Question' looks like (Data Validation)
class QueryRequest(BaseModel):
    fund_id: str
    question: str

@router.post("/ask")
async def ask_smsf_question(request: QueryRequest):
    """
    Takes a question and a fund_id, and returns a verified 
    answer from the SIS Act or the specific Trust Deed.
    """
    try:
        # Get the engine (which already has the Qdrant filters applied)
        engine = get_smsf_query_engine(request.fund_id)
        
        # Query the LLM/Vector Store
        response = engine.query(request.question)
        
        return {
            "answer": str(response),
            "fund_id": request.fund_id,
            "sources": [n.node.get_content()[:200] for n in response.source_nodes]
        }
    except Exception as e:
        # If Qdrant is down or OpenAI fails, return a 500 error
        raise HTTPException(status_code=500, detail=f"RAG Error: {str(e)}")