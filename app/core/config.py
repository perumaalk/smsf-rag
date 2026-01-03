import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from llama_index.core import Settings
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI

# 1. Define your Environment Variables (FastAPI/Pydantic)
class AppSettings(BaseSettings):
    # This looks for these keys in your Render Env Vars
    OPENAI_API_KEY: str
    QDRANT_URL: str
    QDRANT_API_KEY: str
    
    # Optional: Load from .env file locally
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

# Initialize the environment settings
settings = AppSettings()

# 2. Configure LlamaIndex Global Settings
# Note: Ensure the model name is exactly "gpt-4o-mini" (OpenAI standard)
Settings.llm = OpenAI(
    model="gpt-4o-mini", 
    temperature=0.0,
    api_key=settings.OPENAI_API_KEY
)

Settings.embed_model = OpenAIEmbedding(
    model="text-embedding-3-large",
    api_key=settings.OPENAI_API_KEY
)

Settings.chunk_size = 512
Settings.chunk_overlap = 64
Settings.context_window = 128000
