from .providers import QdrantDBProvider
from helpers.config import Settings
from .VectorDBEnums import VectorDBEnums
from controllers.BaseController import BaseController

class VectorDBProviderFactory:

  def __init__(self, config: Settings):
      self.config = config
      self.base_controller = BaseController()

  def get_provider(self, provider_name: str):
    if provider_name == VectorDBEnums.QDRANT.value:
      # Ensure the database path exists
      db_path = self.base_controller.get_database_path(self.config.QDRANT_DB_PATH)
      return QdrantDBProvider(
        db_path=db_path,
        distance_method=self.config.QDRANT_DISTANCE_METHOD
      )

    return None

