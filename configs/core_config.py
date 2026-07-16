from dotenv import load_dotenv
from pathlib import Path
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, Any, Annotated
import os

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[2]


class LLMSettings(BaseSettings):
    """LLM and Provider Configurations."""

    OPENROUTER_PROVIDER_NAME: str = Field(..., validation_alias="OPENROUTER_PROVIDER_NAME")
    OPENROUTER_MODEL_NAME: str = Field(..., validation_alias="OPENROUTER_MODEL_NAME")
    OPENROUTER_API_KEY: Optional[str] = Field(..., validation_alias="OPENROUTER_API_KEY")
    OPENROUTER_PRIORITY: int = Field(..., validation_alias="OPENROUTER_PRIORITY")

    OLLAMA_PROVIDER_NAME: str = Field(..., validation_alias="OLLAMA_PROVIDER_NAME")
    OLLAMA_MODEL_NAME: str = Field(..., validation_alias="OLLAMA_MODEL_NAME")
    OLLAMA_API_KEY: Optional[str] = Field(None, validation_alias="OLLAMA_API_KEY")
    OLLAMA_PRIORITY: int = Field(..., validation_alias="OLLAMA_PRIORITY")

    OLLAMA_LOCAL_PROVIDER_NAME: str = Field(..., validation_alias="OLLAMA_LOCAL_PROVIDER_NAME")
    OLLAMA_LOCAL_MODEL_NAME: str = Field(..., validation_alias="OLLAMA_LOCAL_MODEL_NAME")
    OLLAMA_LOCAL_BASE_URL: str = Field(default="http://localhost:11434", validation_alias="OLLAMA_LOCAL_BASE_URL")
    OLLAMA_LOCAL_PRIORITY: Annotated[int, Field(..., validation_alias="OLLAMA_LOCAL_PRIORITY")]

    TIMEOUT: int = Field(default=1, validation_alias="TIMEOUT")
    MAX_RETRIES: int = Field(default=1, validation_alias="MAX_RETRIES")
    CIRCUIT_BREAKER_THRESHOLD: int = Field(default=3, validation_alias="CIRCUIT_BREAKER_THRESHOLD")
    CIRCUIT_BREAKER_COOLDOWN: int = Field(default=30, validation_alias="CIRCUIT_BREAKER_COOLDOWN")

class DatabaseConfig(BaseSettings):
    DB_DSN: Annotated[Optional[str], Field("", validation_alias="DB_DSN")]

    @model_validator(mode="before")
    @classmethod
    def preprocess_empty_strings(cls, values: Any) -> Any:
        if isinstance(values, dict):
            return {
                k: (None if isinstance(v, str) and v.strip() == "" else v)
                for k, v in values.items()
            }
        return values

class EmbeddingSettings(BaseSettings):
    HUGGINGFACEHUB_API_TOKEN: str = Field(..., validation_alias="HUGGINGFACEHUB_API_TOKEN")
    
    EMBEDDING_MODEL: str = Field(..., validation_alias="EMBEDDING_MODEL")
    EMBEDDING_DIMENSION: str = Field(..., validation_alias="EMBEDDING_DIMENSION")

    RERANKER_MODEL: str = Field(..., validation_alias="RERANKER_MODEL")
    
class AppConfig(BaseSettings):
    APP_NAME: str = Field(..., validation_alias="APP_NAME")
    APP_VERSION: str = Field(..., validation_alias="APP_VERSION")

    VECTOR_DB_PATH: str = Field(..., validation_alias="VECTOR_DB_PATH")

    LANGCHAIN_PROJECT: str = Field(..., validation_alias="LANGCHAIN_PROJECT")

class Settings(BaseSettings):
    """Master Settings Object."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    llm: LLMSettings = Field(default_factory=lambda: LLMSettings())  # type: ignore
    embedding: EmbeddingSettings = Field(default_factory=lambda: EmbeddingSettings())  # type: ignore
    db: FirebaseSettings = Field(default_factory=lambda: FirebaseSettings())  # type: ignore
    app: AppConfig = Field(default_factory=lambda: AppConfig()) # type: ignore


settings = Settings()

OPENROUTER_CONFIG = {
    "max_completion_tokens": 1024
}

OLLAMA_CONFIG = {
    "max_completion_tokens": 1024
}

OLLAMA_LOCAL_CONFIG = {
    "num_predict": 1024,
}

VECTOR_DB_PATH = BASE_DIR / settings.app.VECTOR_DB_PATH
