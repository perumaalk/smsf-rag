from llama_index.core.query_engine import RouterQueryEngine
from llama_index.core.selectors import LLMSingleSelector
from llama_index.core.tools import QueryEngineTool
# Correct imports for Metadata Filters in v0.10+
from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter

# Import your pre-configured index from your vectorstore file
from app.core.vectorstore import index as vector_index

def get_smsf_query_engine(fund_id: str):
    """
    Creates a router that switches between Public Law and Private Fund data.
    """
    
    # 1. Public Law Tool (Filtered for legislation and rulings)
    public_filters = MetadataFilters(filters=[
        ExactMatchFilter(key="doc_type", value="legislation") # or "ato_ruling"
    ])
    
    public_tool = QueryEngineTool.from_defaults(
        query_engine=vector_index.as_query_engine(filters=public_filters),
        description="Useful for questions about SIS Act regulations and ATO tax rulings."
    )
    
    # 2. Private Deed Tool (Filtered by specific Fund ID)
    # This is the "Data Residency/Privacy" layer
    private_filters = MetadataFilters(filters=[
        ExactMatchFilter(key="fund_id", value=fund_id),
        ExactMatchFilter(key="doc_type", value="trust_deed")
    ])
    
    deed_tool = QueryEngineTool.from_defaults(
        query_engine=vector_index.as_query_engine(filters=private_filters),
        description="Useful for checking specific powers granted by the client's Trust Deed."
    )

    # 3. The Router joins them
    # It will choose the 'deed_tool' if the user mentions "the trust deed" 
    # and 'public_tool' if they ask about "SIS regulations".
    return RouterQueryEngine(
        selector=LLMSingleSelector.from_defaults(),
        query_engine_tools=[public_tool, deed_tool]
    )