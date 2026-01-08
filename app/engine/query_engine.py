

from app.core.vectorstore import index as vector_index

from llama_index.core.query_engine import RouterQueryEngine
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.core.selectors import LLMSingleSelector
from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter
from llama_index.llms.openai import OpenAI
from llama_index.core import Settings

from llama_index.core import PromptTemplate

SMSF_QA_PROMPT_TEXT = (
    "### ROLE\n"
    "You are a highly precise SMSF Compliance Specialist and Legal Researcher. [cite: 1]\n\n"
    
    "### HIERARCHY OF AUTHORITY\n"
    "1. MANDATORY LAW: If the SIS Act or SIS Regulations prohibit an action, it is prohibited regardless of what the Trust Deed or ATO Rulings say. [cite: 3]\n"
    "2. TRUST DEED: A Trust Deed can be MORE restrictive than the SIS Act, but it cannot be LESS restrictive. [cite: 4]\n"
    "3. ATO RULINGS: Use these to interpret how the law applies to specific scenarios. [cite: 5]\n\n"
    
    "### STRICT RULES\n"
    "1. ONLY use the provided context to answer technical compliance queries. [cite: 2]\n"
    "2. CITATION: Cite SIS Act by Section (e.g., 's 62 SIS Act') and Deed by Clause (e.g., 'Clause 12.4'). DO NOT hallucinate citations. [cite: 6, 7, 8]\n"
    "3. SCOPE CHECK:\n"
    "   - If the query is a general SMSF query not found in the documents: State 'This query is not directly addressed in the provided compliance documents; however, based on general SMSF principles, the answer is as follows:' then provide the answer.\n"
    "   - If the query is NOT related to SMSF: State 'This query does not relate to SMSF and cannot be answered.' and do not provide further information.\n\n"
    
    "### RESPONSE STRUCTURE [cite: 9]\n"
    "1. SUMMARY: A direct 'Yes/No/It Depends' answer.\n"
    "2. LEGAL BASIS: Reference the SIS Act and Regulations. [cite: 9]\n"
    "3. DEED PERMISSION: State if the provided Trust Deed specifically allows or restricts this power. [cite: 10]\n"
    "4. CONFLICTS: Explicitly flag if the Trust Deed is silent or conflicts with the SIS Act. [cite: 11, 15]\n\n"
    
    "Context: {context_str}\n"
    "Query: {query_str}\n"
    "Answer: "
)

SMSF_QA_PROMPT = PromptTemplate(SMSF_QA_PROMPT_TEXT)
SMSF_REFINE_PROMPT_TEXT = (
    "The original query is as follows: {query_str}\n"
    "We have provided an existing compliance answer: {existing_answer}\n"
    "New context is provided below:\n"
    "------------\n"
    "{context_msg}\n"
    "------------\n"
    "As a Senior SMSF Compliance Auditor, refine the existing answer only if the new context "
    "provides more specific citations, identifies a legal conflict, or clarifies a Deed provision.\n\n"
    
    "STRICT AUDITOR REFINEMENT RULES:\n"
    "1. CITATION PRECISION: If the new context contains a specific Clause or Section number missing from "
    "the original answer, you MUST incorporate it[cite: 6, 7].\n"
    "2. HIERARCHY CHECK: If the new context reveals the SIS Act prohibits something the Deed allows, "
    "update the answer to flag this conflict immediately[cite: 3, 4, 15].\n"
    "3. SCOPE ADHERENCE:\n"
    "   - If the new context confirms the query is general SMSF knowledge, ensure the 'General Principles' "
    "disclaimer is present.\n"
    "   - If the query is non-SMSF related, strictly return: 'This query does not relate to SMSF and cannot be answered.'\n"
    "4. TONE: Maintain a technical, evidence-based tone. Do not acknowledge the 'refinement' process in the output.\n\n"
    
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
        return vector_index.as_query_engine(
            similarity_top_k=5,
            filters=filters,
            text_qa_template=SMSF_QA_PROMPT,
            refine_template=SMSF_REFINE_PROMPT
        )

    # 1. Public Law Tool (Always available)
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

    # Initialize the list of tools with the public law tool
    query_engine_tools = [public_tool]

    # 2. Private Deed Tool (Conditional Access)
    # Only add the deed tool if fund_id is provided and not "global"
    if fund_id and fund_id.lower() != "global":
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
        query_engine_tools.append(deed_tool)
    
    # 3. Fallback Tool (Always available)
    fallback_engine = llm.as_query_engine()
    fallback_tool = QueryEngineTool(
        query_engine=fallback_engine,
        metadata=ToolMetadata(
            name="fallback",
            description="Use this for greetings or general superannuation questions."
        )
    )
    query_engine_tools.append(fallback_tool)

    # 4. Final Router using the dynamically built list of tools
    return RouterQueryEngine(
        selector=LLMSingleSelector.from_defaults(),
        query_engine_tools=query_engine_tools,
        verbose=True
    )