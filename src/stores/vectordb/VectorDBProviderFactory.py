from .providers import QdrantDBProvider, PgVectorProvider
from helpers.config import Settings
from .VectorDBEnums import VectorDBEnums
from controllers.BaseController import BaseController
from sqlalchemy.orm import sessionmaker
from typing import Optional

class VectorDBProviderFactory:

  def __init__(self, config: Settings, db_client: Optional[sessionmaker] = None):
      self.config = config
      self.base_controller = BaseController()
      self.db_client = db_client

  def get_provider(self, provider_name: str):
    if provider_name == VectorDBEnums.QDRANT.value:
      # Ensure the database path exists
      db_path = self.base_controller.get_database_path(self.config.QDRANT_DB_PATH)
      return QdrantDBProvider(
        db_path=db_path,
        distance_method=self.config.VECTOR_DB_DISTANCE_METHOD
      )
    elif provider_name == VectorDBEnums.PGVECTOR.value:
      return PgVectorProvider(
        db_client=self.db_client,
        distance_method=self.config.VECTOR_DB_DISTANCE_METHOD,
        default_vector_size=self.config.EMBEDDING_MODEL_SIZE,
        index_threadhold=self.config.VECTOR_DB_PGVECTOR_INDEX_THREADHOLD,
      )

    return None

