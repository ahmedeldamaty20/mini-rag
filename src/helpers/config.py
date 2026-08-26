from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import List

class Settings(BaseSettings):

  APP_NAME: str
  APP_VERSION: str

  FILE_ALLOWED_TYPES: list[str]
  FILE_MAX_SIZE: int
  FILE_DEFAULT_CHUNK_SIZE: int

  POSTGRES_USERNAME: str
  POSTGRES_PASSWORD: str
  POSTGRES_HOST: str
  POSTGRES_PORT: int
  POSTGRES_MAIN_DATABASE: str

  BACKEND_LITERALS: List[str]
  GENERATION_BACKEND: str
  EMBEDDING_BACKEND: str

  OPENAI_API_KEY: str
  OPENAI_BASE_URL_Literals: List[str]
  OPENAI_BASE_URL: str
  COHERE_API_KEY: str

  GENERATION_MODEL_ID_LITERALS: List[str]
  GENERATION_MODEL_ID: str
  EMBEDDING_MODEL_ID_LITERALS: List[str]
  EMBEDDING_MODEL_ID: str
  EMBEDDING_MODEL_SIZE_LITERALS: List[int]
  EMBEDDING_MODEL_SIZE: int

  INPUT_DEFAULT_MAX_CHARACTERS: int
  GENERATION_DEFAULT_MAX_TOKENS: int
  GENERATION_DEFAULT_TEMPERATURE: float

  VECTOR_DB_LITERALS: List[str]
  VECTOR_DB_BACKEND: str
  QDRANT_DB_PATH: str
  VECTOR_DB_DISTANCE_METHOD: str
  VECTOR_DB_PGVECTOR_INDEX_THREADHOLD: int

  PRIMARY_LANGUAGE: str
  DEFAULT_LANGUAGE: str

  CELERY_BROKER_URL: str
  CELERY_RESULT_BACKEND: str
  CELERY_TASK_SERIALIZER: str
  CELERY_TASK_TIME_LIMIT: int
  CELERY_ACKS_LATE: bool
  CELERY_WORKER_CONCURRENCY: int
  CELERY_FLOWER_PASSWORD: str

  model_config = SettingsConfigDict(env_file=".env")

@lru_cache()
def get_settings() -> Settings:
  return Settings() # type: ignore