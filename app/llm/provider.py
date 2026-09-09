from typing import Protocol

from langchain_core.language_models.chat_models import BaseChatModel


class LLMProvider(Protocol):
    """Contract implemented by supported LLM providers."""

    def get_model(self) -> BaseChatModel:
        """Return the configured LangChain chat model."""
        ...
