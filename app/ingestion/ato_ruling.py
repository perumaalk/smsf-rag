# ingestion/ato_ruling.py
import os
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from .utils import get_storage_context, get_parent_child_nodes
from .sis_act import download_from_spaces # Reuse the downloader

def ingest_ato_ruling(remote_key: str, ruling_id: str):
    local_path = f"./data/temp_{os.path.basename(remote_key)}"
    os.makedirs("./data", exist_ok=True)

    # Pull from DO Spaces
    download_from_spaces(remote_key, local_path)
    
    sc, vs = get_storage_context("ato_rulings", persist_dir="./storage/ato_rulings")
    documents = SimpleDirectoryReader(input_files=[local_path]).load_data()
    
    for doc in documents:
        doc.metadata.update({
            "category": "ruling",
            "ruling_id": ruling_id,
            "fund_id": "global",
            "is_latest": True
        })

    nodes, leaf_nodes = get_parent_child_nodes(documents)
    sc.docstore.add_documents(nodes)
    VectorStoreIndex(leaf_nodes, storage_context=sc)
    sc.docstore.persist(persist_dir="./storage/ato_rulings")
    
    if os.path.exists(local_path):
        os.remove(local_path)