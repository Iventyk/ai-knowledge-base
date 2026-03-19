from langchain.vectorstores.pgvector import PGVector
from langchain.embeddings.openai import OpenAIEmbeddings

from src.core.config import settings


def get_vector_store():
    return PGVector(
        connection_string=settings.database_url,
        embedding_function=OpenAIEmbeddings()
    )
