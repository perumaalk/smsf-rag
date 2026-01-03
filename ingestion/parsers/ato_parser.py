import re
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core import SimpleDirectoryReader

def get_ato_nodes(file_path: str):
    documents = SimpleDirectoryReader(input_files=[file_path]).load_data()
    
    # Extract Ruling ID from filename (e.g., TR_2023_1.pdf)
    file_name = file_path.split("/")[-1]
    ruling_id = file_name.replace("_", " ").replace(".pdf", "")

    for doc in documents:
        doc.metadata.update({
            "category": "ato_ruling",
            "ruling_id": ruling_id,
            "status": "current", # Default to current
            "is_binding": True
        })

    parser = SentenceSplitter(chunk_size=800, chunk_overlap=50)
    return parser.get_nodes_from_documents(documents)