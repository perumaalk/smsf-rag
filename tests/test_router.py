
# To run these tests from the terminal
# uv run pytest tests/test_router.py

import pytest
from llama_index.core.llms import MockLLM
from llama_index.core import Settings
from app.engine.query_engine import get_smsf_query_engine

@pytest.fixture(autouse=True)
def setup_mock_settings():
    """
    This fixture overrides the global Settings with a MockLLM 
    before every test to ensure no real API calls are made.
    """
    Settings.llm = MockLLM(max_tokens=50)
    # We also mock the embedding model to avoid calls there
    from llama_index.core.embeddings import MockEmbedding
    Settings.embed_model = MockEmbedding(embed_dim=1536)

@pytest.mark.asyncio
async def test_router_selection_logic():
    """
    Verifies the router correctly identifies which tool to use.
    """
    # Initialize the engine (it will use our MockLLM from Settings)
    fund_id = "test_fund_123"
    engine = get_smsf_query_engine(fund_id)
    
    # 1. Test Legislation Routing
    query_legis = "What does the SIS Act say about borrowing?"
    response_legis = engine.query(query_legis)
    
    # The MockLLM will return a generic string, but we check the 'selector_result'
    # to see which tool the Router CHOSE to call.
    selection = response_legis.metadata.get("selector_result")
    assert selection is not None
    # Check if index 0 (Public Law) was selected
    assert selection.selections[0].index == 0
    
    # 2. Test Trust Deed Routing
    query_deed = "Does my specific fund allow property purchase?"
    response_deed = engine.query(query_deed)
    
    selection_deed = response_deed.metadata.get("selector_result")
    assert selection_deed.selections[0].index == 1

@pytest.mark.asyncio
async def test_fund_id_filter_application():
    """
    Ensures that the fund_id passed to the engine is actually 
    included in the metadata filters.
    """
    fund_id = "SECRET_FUND_789"
    engine = get_smsf_query_engine(fund_id)
    
    # We look at the 'deed_tool' inside the router to verify its filters
    # The tools are stored in the query_engine_tools list
    deed_tool = engine._query_engine_tools[1] 
    filters = deed_tool.query_engine._retriever._filters
    
    # Verify the ExactMatchFilter is set to our fund_id
    fund_filter = next(f for f in filters.filters if f.key == "fund_id")
    assert fund_filter.value == fund_id