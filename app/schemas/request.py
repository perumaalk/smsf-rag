from pydantic import BaseModel, Field

class QueryRequest(BaseModel):
    query: str = Field(..., example="Does my deed allow for limited recourse borrowing?")
    fund_id: str = Field(..., example="SMSF_12345") # Mandatory for Trust Deed lookups
    use_ato_rulings: bool = True