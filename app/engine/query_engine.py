from llama_index.core.query_engine import RouterQueryEngine, CustomQueryEngine, RetrievalQueryEngine
from llama_index.core.selectors import LLMSingleSelector
from llama_index.core.tools import QueryEngineTool
from llama_index.llms.openai import OpenAI
from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter
from app.prompts.smsf_templates import SMSF_FALLBACK_PROMPT

# Import your configured index and the new templates
from app.core.vectorstore import index as vector_index
from app.prompts.smsf_templates import SMSF_QA_PROMPT, SMSF_REFINE_PROMPT

def get_smsf_query_engine(fund_id: str):
    """
    Creates a router that switches between Public Law and Private Fund data
    using specialized compliance prompts.
    """
    
    # 1. Setup the Base Query Engine with your Custom Prompts
    # We create a helper function to avoid repeating prompt logic
    def create_compliant_engine(filters):
        return vector_index.as_query_engine(
            similarity_top_k=5,
            filters=filters,
            text_qa_template=SMSF_QA_PROMPT,
            refine_template=SMSF_REFINE_PROMPT
        )

    # 2. Public Law Tool
    public_filters = MetadataFilters(filters=[
        ExactMatchFilter(key="doc_type", value="legislation")
    ])
    public_tool = QueryEngineTool.from_defaults(
        query_engine=create_compliant_engine(public_filters),
        description="Search here for SIS Act regulations, ATO tax rulings, and general superannuation law."
    )
    
    # 3. Private Deed Tool (Fund Specific)
    private_filters = MetadataFilters(filters=[
        ExactMatchFilter(key="fund_id", value=fund_id),
        ExactMatchFilter(key="doc_type", value="trust_deed")
    ])
    deed_tool = QueryEngineTool.from_defaults(
        query_engine=create_compliant_engine(private_filters),
        description=f"Search here for specific powers, rules, and clauses within the Trust Deed for Fund ID {fund_id}."
    )

    # 4. Setup the Fallback Tool
    # This uses the LLM directly without searching your Qdrant database
    # fallback_engine = OpenAI(model="gpt-4o-mini")
    
    # fallback_tool = QueryEngineTool.from_defaults(
    #     query_engine=fallback_engine.as_query_engine(),
    #     description=(
    #         "Useful for general greetings, general superannuation definitions, "
    #         "or questions that do NOT require searching specific legal documents."
    #     )
    # )

    llm = OpenAI(model="gpt-4o-mini")
    
    fallback_engine = llm.as_query_engine(
        text_qa_template=SMSF_FALLBACK_PROMPT
    )
    
    fallback_tool = QueryEngineTool.from_defaults(
        query_engine=fallback_engine,
        description=(
            "Use this ONLY for greetings (hello/hi) or general questions about "
            "superannuation that are NOT found in specific fund deeds or laws."
        )
    )

    # 4. The Router
    return RouterQueryEngine(
        selector=LLMSingleSelector.from_defaults(),
        query_engine_tools=[
            public_tool, 
            deed_tool,
            fallback_tool # The router now has a 'catch-all' option
            ], 
        verbose=True  # Highly recommended for debugging Render deployments
    )