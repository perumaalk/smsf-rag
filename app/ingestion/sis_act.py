# ingestion/sis_act.py
import os
import boto3
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from .utils import get_storage_context, get_parent_child_nodes

def download_from_spaces(remote_key, local_path):
    """Downloads a file from DigitalOcean Spaces."""
    s3 = boto3.client(
        's3',
        region_name='sgp1', # e.g., nyc3, sgp1
        endpoint_url=os.environ["DO_SPACES_ENDPOINT"],
        aws_access_key_id=os.environ["DO_SPACES_KEY"],
        aws_secret_access_key=os.environ["DO_SPACES_SECRET"]
    )
    s3.download_file(os.environ["DO_SPACES_BUCKET"], remote_key, local_path)

def ingest_sis_act(remote_key: str, version_tag: str):
    # 1. Prepare local temp path
    local_filename = os.path.basename(remote_key)
    local_path = f"./data/temp_{local_filename}"
    os.makedirs("./data", exist_ok=True)

    # 2. Retrieve from DigitalOcean Spaces
    download_from_spaces(remote_key, local_path)
    
    # 3. Standard Ingestion Logic
    sc, vs = get_storage_context("legislation", persist_dir="./storage/legislation")
    documents = SimpleDirectoryReader(input_files=[local_path]).load_data()
    
    for doc in documents:
        doc.metadata.update({
            "category": "legislation",
            "fund_id": "global",
            "version_tag": version_tag,
            "is_latest": True
        })

    nodes, leaf_nodes = get_parent_child_nodes(documents)
    sc.docstore.add_documents(nodes)
    VectorStoreIndex(leaf_nodes, storage_context=sc)
    sc.docstore.persist(persist_dir="./storage/legislation")
    
    # Cleanup
    if os.path.exists(local_path):
        os.remove(local_path)