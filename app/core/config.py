from llama_index.core import Settings
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI

Settings.llm = OpenAI(
    model="gpt-4.1-mini",
    temperature=0.0,
)

Settings.embed_model = OpenAIEmbedding(
    model="text-embedding-3-large"
)

Settings.chunk_size = 512
Settings.chunk_overlap = 64
Settings.context_window = 128000
