

from app.prompts.smsf_templates import SMSF_FALLBACK_PROMPT

from app.core.vectorstore import index as vector_index
from app.prompts.smsf_templates import SMSF_QA_PROMPT, SMSF_REFINE_PROMPT
########################
from llama_index.core.query_engine import RouterQueryEngine
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.core.selectors import LLMSingleSelector
from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter
from llama_index.llms.openai import OpenAI
from llama_index.core import Settings

from llama_index.core import PromptTemplate

SMSF_QA_PROMPT_TEXT = (
    "Context information is below.\n"
    "---------------------\n"
    "{context_str}\n"
    "---------------------\n"
    "You are a highly senior SMSF (Self-Managed Superannuation Fund) Compliance Auditor. "
    "Your goal is to provide technical, accurate, and evidence-based answers regarding "
    "Australian superannuation law (SIS Act/Regs) and specific Trust Deed provisions.\n\n"
    
    "STRICT RULES:\n"
    "1. ONLY use the provided context to answer. Do not use outside general knowledge.\n"
    "2. If the answer is not in the context, state: 'The provided documents do not contain "
    "information to answer this specific query.'\n"
    "3. ALWAYS cite the specific section (e.g., 'SIS Act Section 62') or Deed clause if present.\n"
    "4. If there is a conflict between the Trust Deed and the Law, prioritize the Law but "
    "mention the Deed's specific rule.\n"
    "5. Do NOT provide financial or personal advice; maintain a technical, compliance-focused tone.\n\n"
    
    "Query: {query_str}\n"
    "Answer: "
)

SMSF_QA_PROMPT = PromptTemplate(SMSF_QA_PROMPT_TEXT)
SMSF_REFINE_PROMPT_TEXT = (
    "The original query is as follows: {query_str}\n"
    "We have provided an existing answer: {existing_answer}\n"
    "We have the opportunity to refine the existing answer "
    "(only if needed) with some more context below.\n"
    "------------\n"
    "{context_msg}\n"
    "------------\n"
    "Given the new context, refine the original answer to be more accurate, "
    "comprehensive, or to provide specific citations from the additional text.\n\n"
    
    "STRICT AUDITOR GUIDELINES:\n"
    "1. If the new context isn't useful, return the existing answer exactly.\n"
    "2. If the new context provides a more specific clause or a contradictory "
    "legal rule, update the answer to reflect this precision.\n"
    "3. Maintain the technical, compliance-focused tone of a senior auditor.\n"
    "4. Do not mention that you are 'refining' or 'updating' the answer in the "
    "final output; simply provide the improved compliance response.\n\n"
    
    "Refined Answer: "
)

SMSF_REFINE_PROMPT = PromptTemplate(SMSF_REFINE_PROMPT_TEXT)

def get_smsf_query_engine(fund_id: str, vector_index):
    """
    Creates a router that switches between Public Law and Private Fund data.
    The vector_index is passed in from the FastAPI app state.
    """
    
    # Configure global LLM settings
    llm = OpenAI(model="gpt-4o-mini")
    Settings.llm = llm

    # Helper to build the underlying engine for each tool
    def create_compliant_engine(filters):
        # This returns a RetrieverQueryEngine instance
        return vector_index.as_query_engine(
            similarity_top_k=5,
            filters=filters,
            # Ensure these prompt variables are imported or defined in this file
            # text_qa_template=SMSF_QA_PROMPT,
            # refine_template=SMSF_REFINE_PROMPT
            text_qa_template=SMSF_QA_PROMPT,
            refine_template=SMSF_REFINE_PROMPT
        )

    # 1. Public Law Tool
    public_filters = MetadataFilters(filters=[
        ExactMatchFilter(key="doc_type", value="legislation")
    ])
    public_tool = QueryEngineTool(
        query_engine=create_compliant_engine(public_filters),
        metadata=ToolMetadata(
            name="public_law",
            description="Search here for SIS Act regulations and general superannuation law."
        )
    )
    
    # 2. Private Deed Tool (Fund Specific)
    private_filters = MetadataFilters(filters=[
        ExactMatchFilter(key="fund_id", value=fund_id),
        ExactMatchFilter(key="doc_type", value="trust_deed")
    ])
    deed_tool = QueryEngineTool(
        query_engine=create_compliant_engine(private_filters),
        metadata=ToolMetadata(
            name="private_deed",
            description=f"Search here for specific rules within the Trust Deed for Fund {fund_id}."
        )
    )

    # 3. Fallback Tool for General Greetings/Questions
    fallback_engine = llm.as_query_engine()
    fallback_tool = QueryEngineTool(
        query_engine=fallback_engine,
        metadata=ToolMetadata(
            name="fallback",
            description="Use this for greetings or general superannuation questions."
        )
    )

    # 4. Final Router
    return RouterQueryEngine(
        selector=LLMSingleSelector.from_defaults(),
        query_engine_tools=[public_tool, deed_tool, fallback_tool],
        verbose=True
    )
