from langchain_core.embeddings import Embeddings
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.embeddings import FakeEmbeddings

from src.core.config import settings


class EchoChatModel(BaseChatModel):
    @property
    def _llm_type(self) -> str:
        return "echo-chat"

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        human_messages = [
            message.content for message in messages if hasattr(message, "content")
        ]
        response = "\n".join(
            ["Demo answer generated without external LLM.", *human_messages[-1:]]
        )
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=response))])


def get_embeddings() -> Embeddings:
    if settings.embedding_provider == "openai" and settings.openai_api_key:
        return OpenAIEmbeddings(api_key=settings.openai_api_key)
    return FakeEmbeddings(size=1536)


def get_llm() -> BaseChatModel:
    if settings.llm_provider == "openai" and settings.openai_api_key:
        return ChatOpenAI(model="gpt-4o-mini", api_key=settings.openai_api_key, temperature=0)
    return EchoChatModel()
