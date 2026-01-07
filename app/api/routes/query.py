from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from app.engine.query_engine import get_smsf_query_engine

router = APIRouter()

class QueryRequest(BaseModel):
    fund_id: str
    question: str

# 1. We define the logic ONCE in this shared function
async def execute_rag_logic(query_data: QueryRequest, request: Request):
    try:
        vector_index = getattr(request.app.state, "vector_index", None)
        if vector_index is None:
            raise HTTPException(status_code=500, detail="Index not initialized")

        engine = get_smsf_query_engine(
            fund_id=query_data.fund_id, 
            vector_index=vector_index
        )
        
        response = engine.query(query_data.question)
        
        return {
            "answer": str(response),
            "fund_id": query_data.fund_id,
            "sources": [n.node.get_content()[:200] for n in response.source_nodes]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 2. Map BOTH routes to that same logic
@router.post("/ask")
async def ask_endpoint(query_data: QueryRequest, request: Request):
    return await execute_rag_logic(query_data, request)

@router.post("/query")
async def query_endpoint(query_data: QueryRequest, request: Request):
    return await execute_rag_logic(query_data, request)