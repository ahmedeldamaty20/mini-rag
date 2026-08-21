from uuid import uuid4

from .BaseController import BaseController
from models.db_schemas import Project, DataChunk
from typing import List, Optional
import json
from stores.llm.LLMEnums import DocumentTypeEnums

class NLPController(BaseController):
  def __init__(self, vectordb_client, embedding_client, generation_client):
    super().__init__()

    self.vectordb_client = vectordb_client
    self.embedding_client = embedding_client  
    self.generation_client = generation_client

  def create_collection_name(self, project_id: str) -> str:
    return f"collection_{project_id}".strip()

  def reset_vector_database_collection(self, project: Project) -> bool:
    collection_name = self.create_collection_name(project.project_id)
    return self.vectordb_client.delete_collection(collection_name)

  def get_vector_db_collection_info(self, project: Project) -> dict:
    collection_name = self.create_collection_name(project.project_id)
    return self.vectordb_client.get_collection_info(collection_name)

  def index_into_vector_db(self, project: Project, data_chunks: List[DataChunk], do_reset: int = False) -> bool:
    collection_name = self.create_collection_name(project.project_id)
    if do_reset:
      self.reset_vector_database_collection(project)

    texts = [chunk.chunk_text for chunk in data_chunks]
    metadata_list = [chunk.chunk_metadata for chunk in data_chunks]
    vectors = [
      self.embedding_client.generate_embedding(text)
      for text in texts
    ]

    vector_ids = [str(uuid4()) for _ in data_chunks]

    # create the collection if it doesn't exist
    _ = self.vectordb_client.create_collection(collection_name, self.embedding_client.embedding_model_size, do_reset=do_reset)

    return self.vectordb_client.insert_many(collection_name, texts,  vector_ids, vectors, metadata_list)

  async def search_in_vector_db(self, project: Project, query_text: str, top_k: Optional[int] = 10) -> list:

    collection_name = self.create_collection_name(project.project_id)
    query_vector = self.embedding_client.generate_embedding(query_text, DocumentTypeEnums.QUERY.value)

    if not query_vector:
      return []

    search_results = self.vectordb_client.search_by_vectors(collection_name, query_vector, top_k=top_k)

    if not search_results:
      return []

    return json.loads(
      json.dumps(search_results, default=lambda o: o.__dict__ if hasattr(o, '__dict__') else str(o))
    )
  