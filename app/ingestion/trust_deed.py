# ingestion/trust_deed.py
import os
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
# Relative import since utils.py is in the same folder
from .utils import get_storage_context, get_parent_child_nodes

def process_trust_deed_upload(file_path: str, fund_id: str):
    """
    Logic used by the FastAPI background task.
    """
    # Store persistent data in a folder dedicated to deeds
    sc, vs = get_storage_context("trust_deeds", persist_dir="./storage/trust_deeds")
    
    documents = SimpleDirectoryReader(input_files=[file_path]).load_data()
    
    for doc in documents:
        doc.metadata.update({
            "category": "trust_deed",
            "fund_id": fund_id,
            "is_latest": True
        })

    nodes, leaf_nodes = get_parent_child_nodes(documents)
    
    # Idempotent indexing: only embeds if doc hash is new
    sc.docstore.add_documents(nodes)
    VectorStoreIndex(leaf_nodes, storage_context=sc)
    
    sc.docstore.persist(persist_dir="./storage/trust_deeds")
    
    if os.path.exists(file_path):
        os.remove(file_path)