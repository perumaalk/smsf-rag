from llama_index.core.node_parser import SentenceSplitter
from llama_index.core import SimpleDirectoryReader

def get_sis_nodes(file_path: str):
    # Load SIS Act PDF
    documents = SimpleDirectoryReader(input_files=[file_path]).load_data()
    
    # Add SIS specific metadata
    for doc in documents:
        doc.metadata.update({
            "category": "legislation",
            "document_name": "SIS Act 1993",
            "jurisdiction": "Commonwealth"
        })

    # Chunking: Larger chunks often work better for legislative sections
    parser = SentenceSplitter(chunk_size=1024, chunk_overlap=100)
    return parser.get_nodes_from_documents(documents)

"""
# Summary Augmented Chunking
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.extractors import SummaryExtractor
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core import SimpleDirectoryReader

def get_sis_nodes(file_path: str):
    # 1. Load Documents
    documents = SimpleDirectoryReader(input_files=[file_path]).load_data()
    
    # 2. Basic Metadata Setup
    for doc in documents:
        doc.metadata.update({
            "category": "legislation",
            "document_name": "SIS Act 1993",
            "jurisdiction": "Commonwealth"
        })

    # 3. Define the Ingestion Pipeline
    # This combines chunking and summary extraction into one flow
    pipeline = IngestionPipeline(
        transformations=[
            # First, split into chunks
            SentenceSplitter(chunk_size=1024, chunk_overlap=100),
            # Second, extract summaries of the surrounding context for each node
            # 'summaries=["self"]' means it summarizes the chunk itself + context
            SummaryExtractor(summaries=["self"], show_progress=True)
        ]
    )

    # 4. Run the pipeline to get augmented nodes
    nodes = pipeline.run(documents=documents)
    
    return nodes
"""