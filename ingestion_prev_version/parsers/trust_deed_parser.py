import os
from typing import List
from llama_parse import LlamaParse
from llama_index.core import SimpleDirectoryReader, Document
from llama_index.core.node_parser import MarkdownElementNodeParser
from llama_index.llms.openai import OpenAI
from app.core.config import settings

def get_trust_deed_nodes(file_path: str, fund_id: str) -> List:
    """
    Parses a Trust Deed PDF using LlamaParse for OCR and structural analysis.
    Stamps every node with a fund_id to ensure data isolation.
    """
    
    # 1. Initialize LlamaParse
    # We use 'gpt-4o' as the parsing instruction model for high accuracy on legal tables
    parser = LlamaParse(
        api_key=os.environ.get("LLAMA_CLOUD_API_KEY"),
        result_type="markdown",  # Crucial for preserving legal numbering
        num_workers=4,
        parsing_instruction=(
            "This is an SMSF Trust Deed. It contains rules and powers for trustees. "
            "Examine the 'Execution' or 'Signatures' page to confirm the deed is signed. "
            "Identify and preserve Clause numbers (e.g. 12.1.a) accurately. "
            "If a table lists 'Permitted Investments', extract it as a clean Markdown table."
        ),
        verbose=True
    )

    # 2. Extract Data
    # SimpleDirectoryReader allows us to use specialized extractors per file type
    file_extractor = {".pdf": parser}
    reader = SimpleDirectoryReader(
        input_files=[file_path], 
        file_extractor=file_extractor
    )
    
    # Load document and immediately add fund-specific metadata
    documents = reader.load_data()
    
    for doc in documents:
        doc.metadata.update({
            "fund_id": fund_id,           # Used for query-time filtering
            "category": "trust_deed",
            "doc_type": "private_law",
            "source_file": os.path.basename(file_path)
        })

    # 3. Transform Documents into Nodes
    # MarkdownElementNodeParser is the 'gold standard' for legal RAG. 
    # It identifies tables and section headers to keep related context together.
    node_parser = MarkdownElementNodeParser(
        llm=OpenAI(model="gpt-4o"), 
        num_workers=4
    )
    
    # This generates a list of 'TextNodes' and 'TableNodes'
    # TableNodes specifically help the LLM 'read' investment power grids correctly.
    nodes = node_parser.get_nodes_from_documents(documents)

    return nodes