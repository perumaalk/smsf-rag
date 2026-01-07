# ingestion/utils.py
import os
from llama_index.core import StorageContext
from llama_index.core.node_parser import HierarchicalNodeParser, get_leaf_nodes
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core.storage.docstore import SimpleDocumentStore
from qdrant_client import QdrantClient

def get_storage_context(collection_name: str, persist_dir: str):
    """
    Sets up Qdrant and a local Docstore for idempotency.
    """
    # Initialize Qdrant Client
    client = QdrantClient(
        url=os.environ.get("QDRANT_URL"), 
        api_key=os.environ.get("QDRANT_API_KEY")
    )
    
    vector_store = QdrantVectorStore(
        collection_name=collection_name, 
        client=client
    )
    
    # Ensure the storage directory exists for the Docstore
    os.makedirs(persist_dir, exist_ok=True)
    
    # Load or create Docstore (handles mid-process failures)
    try:
        docstore = SimpleDocumentStore.from_persist_dir(persist_dir)
    except (FileNotFoundError, Exception):
        docstore = SimpleDocumentStore()

    return StorageContext.from_defaults(
        vector_store=vector_store,
        docstore=docstore
    ), vector_store

def get_parent_child_nodes(documents):
    """
    Recursive Retrieval: Defines the hierarchy.
    - Parent: 2048 (Context)
    - Mid: 512
    - Child/Leaf: 128 (Vectors)
    """
    node_parser = HierarchicalNodeParser.from_defaults(
        chunk_sizes=[2048, 512, 128]
    )
    nodes = node_parser.get_nodes_from_documents(documents)
    leaf_nodes = get_leaf_nodes(nodes)
    return nodes, leaf_nodes