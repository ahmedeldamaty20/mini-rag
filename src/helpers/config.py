from pydantic_settings import BaseSettings, SettingsConfigDict

class settings(BaseSettings):

  APP_NAME: str
  APP_VERSION: str

  FILE_ALLOWED_TYPES: list[str]
  FILE_MAX_SIZE: int
  FILE_DEFAULT_CHUNK_SIZE: int

  MONGODB_URL: str
  MONGODB_DATABASE: str

  GENERATION_BACKEND: str
  EMBEDDING_BACKEND: str

  OPENAI_API_KEY: str
  COHERE_API_KEY: str

  GENERATION_MODEL_ID: str
  EMBEDDING_MODEL_ID: str
  EMBEDDING_MODEL_SIZE: int

  INPUT_DEFAULT_MAX_CHARACTERS: int
  GENERATION_DEFAULT_MAX_TOKENS: int
  GENERATION_DEFAULT_TEMPERATURE: float

  VECTOR_DB_BACKEND: str
  QDRANT_DB_PATH: str
  QDRANT_DISTANCE_METHOD: str

  class Config:
    env_file = ".env"

def get_settings() -> settings:
  return settings() # type: ignore