import qdrant_client
from llama_index.core import StorageContext, VectorStoreIndex
from llama_index.vector_stores.qdrant import QdrantVectorStore
from app.core.config import settings
from ingestion.parsers.sis_parser import get_sis_nodes
from ingestion.parsers.ato_parser import get_ato_nodes

def build_pipeline(nodes):
    # Initialize Qdrant
    client = qdrant_client.QdrantClient(
        url=settings.QDRANT_URL, 
        api_key=settings.QDRANT_API_KEY
    )
    
    vector_store = QdrantVectorStore(
        client=client, 
        collection_name=settings.COLLECTION_NAME
    )
    
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    
    # Create index (this generates embeddings and uploads to Qdrant)
    index = VectorStoreIndex(
        nodes, 
        storage_context=storage_context, 
        show_progress=True
    )
    return index