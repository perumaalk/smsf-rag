from llama_index.core.query_engine import RouterQueryEngine
from llama_index.core.selectors import LLMSingleSelector
from llama_index.core.tools import QueryEngineTool

def get_smsf_query_engine(fund_id: str):
    # 1. Tool for General Law (SIS Act & ATO)
    general_tool = QueryEngineTool.from_defaults(
        query_engine=public_index.as_query_engine(),
        description="Useful for questions about SIS Act regulations and ATO tax rulings."
    )
    
    # 2. Tool for Private Deed (Filtered by Fund ID)
    # This ensures the LLM ONLY sees the deed for THIS specific fund
    deed_tool = QueryEngineTool.from_defaults(
        query_engine=private_index.as_query_engine(
            filters=MetadataFilters(filters=[
                ExactMatchFilter(key="fund_id", value=fund_id)
            ])
        ),
        description="Useful for checking specific powers granted by the client's Trust Deed."
    )

    # 3. The Router joins them
    return RouterQueryEngine(
        selector=LLMSingleSelector.from_defaults(),
        query_engine_tools=[general_tool, deed_tool]
    )