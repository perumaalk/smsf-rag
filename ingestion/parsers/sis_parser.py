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