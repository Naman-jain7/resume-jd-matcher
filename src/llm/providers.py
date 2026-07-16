from typing import Any, AsyncIterator, Dict, Iterator, List, Optional, Type, Union

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langsmith import traceable
from pydantic import BaseModel

from configs.core_config import (
    OLLAMA_CONFIG,
    OLLAMA_LOCAL_CONFIG,
    OPENROUTER_CONFIG,
    settings,
)
from src.graphs.tools import tools
from src.utils.exception import ExternalServiceError
from src.utils.logger import LLM_LOGGER


def _convert_messages(messages: List[Any]) -> List[Any]:
    """Helper to format dictionary messages into LangChain message objects."""
    formatted_messages = []

    for msg in messages:
        if isinstance(msg, BaseMessage):
            formatted_messages.append(msg)

        elif isinstance(msg, dict):
            role = msg.get("role", "user").lower()
            content = msg.get("content", "")

            if role == "system":
                formatted_messages.append(SystemMessage(content=content))
            elif role == "assistant":
                formatted_messages.append(AIMessage(content=content))
            else:
                formatted_messages.append(HumanMessage(content=content))

        else:
            formatted_messages.append(HumanMessage(content=str(msg)))

    return formatted_messages

# ============================================================================================

class OllamaLocalProvider:
    """Client for local Ollama generation."""

    def __init__(
        self,
        temperature: float = 0.4,
        think: bool = False,
        num_predict:int = OLLAMA_LOCAL_CONFIG['num_predict'],
        **default_kwargs: Any,
    ) -> None:
        
        self._validate_connection()

        self.temperature = temperature
        self.num_predict = num_predict
        self.default_kwargs = default_kwargs

        self.llm = ChatOllama(
            model=settings.llm.OLLAMA_LOCAL_MODEL_NAME,
            base_url=settings.llm.OLLAMA_LOCAL_BASE_URL,
            temperature=self.temperature,
            num_predict=self.num_predict,
            validate_model_on_init=True,
            **self.default_kwargs,
        )

        LLM_LOGGER.info(
            "Ollama Local provider initialized: model=%s",
            settings.llm.OLLAMA_LOCAL_MODEL_NAME,
        )

    def _validate_connection(self) -> None:
        """Ping the local Ollama endpoint to verify it is reachable."""
        import urllib.request

        # Strips trailing slash if present and builds the root ping path
        base_url = settings.llm.OLLAMA_LOCAL_BASE_URL.rstrip("/")

        try:
            # A simple GET request to the root Ollama port (returns 'Ollama is running')
            with urllib.request.urlopen(base_url, timeout=2.0) as response:
                if response.status != 200:
                    raise Exception(f"Received status code {response.status}")
        except Exception as e:
            raise ExternalServiceError(
                message="Local Ollama service is not running or unreachable.",
                payload={"base_url": base_url, "original_error": str(e)},
            )

    def generate(
        self,
        messages: List[Dict[str, str]],
        response_format: Optional[Type[BaseModel]] = None,
    ) -> Union[str, BaseModel]:
        """Generate a synchronous answer from a local Ollama model."""

        formatted_messages = _convert_messages(messages)
        try:
            if response_format:
                structured_llm = self.llm.with_structured_output(response_format)
                return structured_llm.invoke(formatted_messages)  # type: ignore

            response = self.llm.invoke(formatted_messages)
            return response.content  # type: ignore
        
        except Exception as e:
            raise ExternalServiceError(
                message=f"Local Ollama generation failed: {str(e)}",
                payload={"model": settings.llm.OLLAMA_LOCAL_MODEL_NAME},
            ) from e

    async def agenerate(
        self,
        messages: List[Dict[str, str]],
        response_format: Optional[Type[BaseModel]] = None,
    ) -> Union[str, BaseModel]:
        """Generate an asynchronous answer (great for concurrent API tasks)."""
        formatted_messages = _convert_messages(messages)
        try:
            if response_format:
                structured_llm = self.llm.with_structured_output(response_format)
                return await structured_llm.ainvoke(formatted_messages)  # type: ignore

            response = await self.llm.ainvoke(formatted_messages)
            return response.content  # type: ignore
        
        except Exception as e:
            raise ExternalServiceError(
                message=f"Local Ollama async generation failed: {str(e)}",
                payload={"model": settings.llm.OLLAMA_LOCAL_MODEL_NAME},
            ) from e

    def stream(
        self,
        messages: List[Dict[str, str]],
    ) -> Iterator[str]:
        """Stream chunks of the response in real-time."""

        formatted_messages = _convert_messages(messages)
        try:
            for chunk in self.llm.stream(formatted_messages):
                if chunk.content:
                    yield chunk.content  # type: ignore
        except Exception as e:
            raise ExternalServiceError(
                message=f"Local Ollama streaming interrupted: {str(e)}",
                payload={"model": settings.llm.OLLAMA_LOCAL_MODEL_NAME}
            ) from e

    async def astream(
        self,
        messages: List[Dict[str, str]],
    ) -> AsyncIterator[str]:
        """Asynchronously stream chunks of the response in real-time."""

        formatted_messages = _convert_messages(messages)
        try:
            async for chunk in self.llm.astream(formatted_messages):
                yield chunk.content  # type: ignore

        except Exception as e:
            raise ExternalServiceError(
                message=f"Local Ollama async streaming interrupted: {str(e)}",
                payload={"model": settings.llm.OLLAMA_LOCAL_MODEL_NAME}
            ) from e

# ============================================================================================

class OpenRouterProvider:
    """Client for OpenRouter generation."""

    def __init__(
        self,
        temperature: float = 0.4,
        max_completion_tokens: int = OPENROUTER_CONFIG["max_completion_tokens"],
        **default_kwargs: Any,
    ) -> None:
        
        self._validate_connection()
        self.temperature = temperature
        self.max_completion_tokens = max_completion_tokens
        self.default_kwargs = default_kwargs

        self.llm = ChatOpenAI(
            model=settings.llm.OPENROUTER_MODEL_NAME,
            api_key=settings.llm.OPENROUTER_API_KEY,  # type: ignore
            base_url="https://openrouter.ai/api/v1",
            temperature=self.temperature,
            max_completion_tokens=self.max_completion_tokens,
            timeout=settings.llm.TIMEOUT,
            max_retries=settings.llm.MAX_RETRIES,
            **self.default_kwargs,
        )

        LLM_LOGGER.info(
            "OpenRouter provider initialized: model=%s",
            settings.llm.OPENROUTER_MODEL_NAME,
        )

    def _validate_connection(self) -> None:
        """Ping the Openrouter endpoint to verify it is reachable."""
        import urllib.request

        # Appending /models gives a valid public GET endpoint
        base_url = "https://openrouter.ai/api/v1/models"

        try:
            with urllib.request.urlopen(base_url, timeout=2.0) as response:
                if response.status != 200:
                    raise Exception(f"Received status code {response.status}")
        except Exception as e:
            raise ExternalServiceError(
                message="Openrouter service is not running or unreachable.",
                payload={"base_url": base_url, "original_error": str(e)},
            )

    @traceable(run_type="llm", name="OpenRouter_generate")
    def generate(
        self,
        messages: List[Dict[str, str]],
        response_format: Optional[Type[BaseModel]] = None,
    ) -> Union[str, BaseModel]:
        """Generate a synchronous answer."""

        formatted_messages = _convert_messages(messages)
        try:
            if response_format:
                structured_llm = self.llm.with_structured_output(response_format)
                return structured_llm.invoke(formatted_messages)  # type: ignore

            response = self.llm.invoke(formatted_messages)
            return response.content  # type: ignore
        
        except Exception as e:
            raise ExternalServiceError(
                message=f"Openrouter generation failed: {str(e)}",
                payload={"model": settings.llm.OPENROUTER_MODEL_NAME},
            ) from e

    @traceable(run_type="llm", name="OpenRouter_agenerate")
    async def agenerate(
        self,
        messages: List[Dict[str, str]],
        response_format: Optional[Type[BaseModel]] = None,
    ) -> Union[str, BaseModel]:
        """Generate an asynchronous answer."""

        formatted_messages = _convert_messages(messages)
        try:
            if response_format:
                structured_llm = self.llm.with_structured_output(response_format)
                return await structured_llm.ainvoke(formatted_messages)  # type: ignore

            response = await self.llm.ainvoke(formatted_messages)
            return response.content  # type: ignore
    
        except Exception as e:
            raise ExternalServiceError(
                message=f"Openrouter async generation failed: {str(e)}",
                payload={"model": settings.llm.OPENROUTER_MODEL_NAME},
            ) from e

    @traceable(run_type="llm", name="OpenRouter_stream")
    def stream(
        self,
        messages: List[Dict[str, str]],
    ) -> Iterator[str]:
        """Stream chunks of the response."""

        formatted_messages = _convert_messages(messages)

        try:
            for chunk in self.llm.stream(formatted_messages):
                if chunk.content:
                    yield chunk.content  # type: ignore

        except Exception as e:
            raise ExternalServiceError(
                message=f"Openrouter streaming interrupted: {str(e)}",
                payload={"model": settings.llm.OPENROUTER_MODEL_NAME},
            ) from e
    
    @traceable(run_type="llm", name="OpenRouter_astream")
    async def astream(
        self,
        messages: List[Dict[str, str]],
    ) -> AsyncIterator[str]:
        """Asynchronously stream chunks of the response."""

        formatted_messages = _convert_messages(messages)

        try:
            async for chunk in self.llm.astream(formatted_messages):
                if chunk.content:
                    yield chunk.content  # type: ignore

        except Exception as e:
            raise ExternalServiceError(
                message=f"Openrouter async streaming interrupted: {str(e)}",
                payload={"model": settings.llm.OPENROUTER_MODEL_NAME},
            ) from e

# ============================================================================================

class OllamaProvider:
    """Client for Ollama Cloud generation."""

    def __init__(
        self,
        temperature: float = 0.4,
        max_completion_tokens: int = OLLAMA_CONFIG["max_completion_tokens"],
        **default_kwargs: Any,
    ) -> None:
        
        self.temperature = temperature
        self.max_completion_tokens = max_completion_tokens
        self.default_kwargs = default_kwargs
        
        self.llm = ChatOpenAI(
            model=settings.llm.OLLAMA_MODEL_NAME,
            api_key=settings.llm.OLLAMA_API_KEY,  # type: ignore
            base_url="https://ollama.com/v1",
            temperature=self.temperature,
            max_completion_tokens=self.max_completion_tokens,
            timeout=settings.llm.TIMEOUT,
            max_retries=settings.llm.MAX_RETRIES,
            **self.default_kwargs,
        )
        
        LLM_LOGGER.info(
            "Ollama provider initialized (ChatOpenAI wrapper): model=%s",
            settings.llm.OLLAMA_MODEL_NAME,
        )

    @traceable(run_type="llm", name="Ollama_generate")
    def generate(
        self,
        messages: List[Dict[str, str]],
        response_format: Optional[Type[BaseModel]] = None,
    ) -> Union[str, BaseModel]:
        """Generate a synchronous answer."""

        formatted_messages = _convert_messages(messages)
        try:
            if response_format:
                structured_llm = self.llm.with_structured_output(response_format)
                return structured_llm.invoke(formatted_messages)  # type: ignore

            response = self.llm.invoke(formatted_messages)
            return response.content  # type: ignore
        
        except Exception as e:
            raise ExternalServiceError(
                message=f"Ollama generation failed: {str(e)}",
                payload={"model": settings.llm.OLLAMA_MODEL_NAME},
            ) from e

    @traceable(run_type="llm", name="Ollama_agenerate")
    async def agenerate(
        self,
        messages: List[Dict[str, str]],
        response_format: Optional[Type[BaseModel]] = None,
    ) -> Union[str, BaseModel]:
        """Generate an asynchronous answer."""

        formatted_messages = _convert_messages(messages)
        try:
            if response_format:
                structured_llm = self.llm.with_structured_output(response_format)
                return await structured_llm.ainvoke(formatted_messages)  # type: ignore

            response = await self.llm.ainvoke(formatted_messages)
            return response.content  # type: ignore
        
        except Exception as e:
            raise ExternalServiceError(
                message=f"Ollama async generation failed: {str(e)}",
                payload={"model": settings.llm.OLLAMA_MODEL_NAME},
            ) from e

    @traceable(run_type="llm", name="Ollama_stream")
    def stream(
        self,
        messages: List[Dict[str, str]],
    ) -> Iterator[str]:
        """Stream chunks of the response."""

        formatted_messages = _convert_messages(messages)
        try:
            for chunk in self.llm.stream(formatted_messages):
                if chunk.content:
                    yield chunk.content  # type: ignore

        except Exception as e:
            raise ExternalServiceError(
                message=f"Ollama streaming interrupted: {str(e)}",
                payload={"model": settings.llm.OLLAMA_MODEL_NAME},
            ) from e

    @traceable(run_type="llm", name="Ollama_astream")
    async def astream(
        self,
        messages: List[Dict[str, str]],
    ) -> AsyncIterator[str]:
        """Asynchronously stream chunks of the response."""

        formatted_messages = _convert_messages(messages)
        try:
            async for chunk in self.llm.astream(formatted_messages):
                if chunk.content:
                    yield chunk.content  # type: ignore

        except Exception as e:
            raise ExternalServiceError(
                message=f"Ollama async streaming interrupted: {str(e)}",
                payload={"model": settings.llm.OLLAMA_MODEL_NAME},
            ) from e

# ============================================================================================

class ResilientLLMManager:
    """
    Leverages LangChain's native runnable architecture to automatically
    fallback across multiple underlying provider chains.
    """

    def __init__(self, primary_provider, backup_providers: list):
        main_chain = primary_provider.llm
        fallback_chains = [p.llm for p in backup_providers]

        self.resilient_llm = main_chain.with_fallbacks(fallbacks=fallback_chains)

    async def astream(self, messages: List[Dict[str, str]]) -> AsyncIterator[str]:
        formatted_messages = _convert_messages(messages)

        async for chunk in self.resilient_llm.astream(formatted_messages):
            if chunk.content:
                yield chunk.content

# ============================================================================================

llm = ResilientLLMManager(
    primary_provider = OllamaLocalProvider(), 
    backup_providers = [OllamaProvider(), OpenRouterProvider()]
)