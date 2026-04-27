from __future__ import annotations
from pydantic import SecretStr

from langchain_community.embeddings import (
    FakeEmbeddings,
    HuggingFaceEmbeddings,
)
from langchain_core.embeddings import Embeddings
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_groq import ChatGroq

from src.core.config import settings


class EchoChatModel(BaseChatModel):
    @property
    def _llm_type(self) -> str:
        return "echo-chat"

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        prompt = str(messages[-1].content) if messages else ""
        response = (
            "Demo answer generated without an external LLM. "
            "Below is the prompt that would be sent to the model:\n\n"
            f"{prompt}"
        )

        return ChatResult(
            generations=[ChatGeneration(message=AIMessage(content=response))]
        )

    async def _agenerate(
        self, messages, stop=None, run_manager=None, **kwargs
    ):
        return self._generate(
            messages=messages,
            stop=stop,
            run_manager=run_manager,
            **kwargs,
        )


def get_embeddings() -> Embeddings:
    if settings.embedding_provider == "openai" and settings.openai_api_key:
        return OpenAIEmbeddings(
            model=settings.embedding_model,
            api_key=SecretStr(settings.openai_api_key),
        )
    if settings.embedding_provider == "huggingface":
        return HuggingFaceEmbeddings(model_name=settings.embedding_model)
    return FakeEmbeddings(size=settings.vector_dimensions)


def get_llm() -> BaseChatModel:
    if settings.llm_provider == "openai" and settings.openai_api_key:
        return ChatOpenAI(
            model=settings.llm_model,
            api_key=SecretStr(settings.openai_api_key),
            temperature=0,
        )
    if settings.llm_provider == "groq" and settings.groq_api_key:
        return ChatGroq(
            model=settings.llm_model,
            api_key=SecretStr(settings.groq_api_key),
            temperature=0,
        )
    return EchoChatModel()
