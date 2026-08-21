from typing import List, Optional
from ..VectorDBInterface import VectorDBInterface
from ..VectorDBEnums import DistanceMetodEnums
from qdrant_client import QdrantClient, models
from models.db_schemas import RetrievedDocument

import logging

class QdrantDBProvider(VectorDBInterface):

  def __init__(self, db_path: str, distance_method: str):
    self.client = None
    self.db_path = db_path

    if distance_method == DistanceMetodEnums.COSINE.value:
      self.distance_method = models.Distance.COSINE
    elif distance_method == DistanceMetodEnums.DOT.value:
      self.distance_method = models.Distance.DOT

    self.logger = logging.getLogger(__name__)

  def connect(self):
    self.client = QdrantClient(path=self.db_path)
    self.logger.info(f"Connected to QdrantDB at {self.db_path}")

  def disconnect(self):
    if self.client:
      self.client.close()
      self.logger.info("Disconnected from QdrantDB")

  def is_collection_exists(self, collection_name: str) -> bool:
    if self.client:
      return self.client.collection_exists(collection_name)
    else:
      self.logger.error("Qdrant client is not connected.")
      return False

  def list_all_collections(self) -> List:
    if self.client:
      return self.client.get_collections().collections
    else:
      self.logger.error("Qdrant client is not connected.")
      return []

  def get_collection_info(self, collection_name: str) -> dict:
    if self.client:
      return self.client.get_collection(collection_name).model_dump()
    else:
      self.logger.error("Qdrant client is not connected.")
      return {}

  def delete_collection(self, collection_name: str):
    if self.client:
      if(self.is_collection_exists(collection_name)):
        self.client.delete_collection(collection_name)
        self.logger.info(f"Collection deleted: {collection_name}")
      else:
        self.logger.warning(f"Collection does not exist: {collection_name}")
    else:
      self.logger.error("Qdrant client is not connected.")

  def create_collection(self, collection_name: str, vector_dimension: int, do_reset: bool = False) -> bool:
    if self.client:
      if self.is_collection_exists(collection_name):
        if do_reset:
          _ = self.delete_collection(collection_name)
          self.logger.info(f"Collection reset: {collection_name}")
        else:
          self.logger.warning(f"Collection already exists: {collection_name}")
          return False

      self.client.create_collection(
        collection_name=collection_name,
        vectors_config=models.VectorParams(size=vector_dimension, distance=self.distance_method)
      )
      self.logger.info(f"Collection created: {collection_name} with dimension {vector_dimension}")
      return True
    else:
      self.logger.error("Qdrant client is not connected.")
      return False

  def insert_one(self, collection_name: str, text: str, vector_id: str, vector: list, metadata: Optional[dict] = None) -> bool:
    if self.client:
      if not self.is_collection_exists(collection_name):
        self.logger.error(f"Collection does not exist: {collection_name}")
        return False

      try:
        _ = self.client.upsert(
          collection_name=collection_name,
          points=[
            models.PointStruct(
              id=vector_id,
              vector=vector,
              payload={"text": text, **metadata} if metadata else {"text": text}
            )
          ]
        )
        self.logger.info(f"Inserted point with ID {vector_id} into collection {collection_name}")
        return True
      except Exception as e:
        self.logger.error(f"Error occurred while inserting point into collection {collection_name}: {e}")
        return False
    else:
      self.logger.error("Qdrant client is not connected.")
      return False

  def insert_many(self, collection_name: str, texts: List[str], vector_ids: List[str], vectors: List[list], metadatas: Optional[List[dict]] = None, batch_size: int = 100) -> bool:
    if self.client:
      if not self.is_collection_exists(collection_name):
        self.logger.error(f"Collection does not exist: {collection_name}")
        return False

      try:
        points = []
        for i in range(len(texts)):
          payload = {"text": texts[i]}
          if metadatas and i < len(metadatas):
            payload.update(metadatas[i])
          points.append(models.PointStruct(id=vector_ids[i], vector=vectors[i], payload=payload))
      except (IndexError, KeyError) as e:
        self.logger.error(f"Error occurred while building points for collection {collection_name}: {e}")
        return False

      for i in range(0, len(points), batch_size):
        batch_points = points[i:i + batch_size]

        try:
          _ = self.client.upsert(collection_name=collection_name, points=batch_points)
          self.logger.info(f"Inserted batch of {len(batch_points)} points into collection {collection_name}")
        except Exception as e:
          self.logger.error(f"Error occurred while inserting batch into collection {collection_name}: {e}")
          return False

      return True
    else:
      self.logger.error("Qdrant client is not connected.")
      return False
  
  def search_by_vectors(self, collection_name: str, vectors: list, top_k: int) -> List[RetrievedDocument]:
    if self.client:
      if not self.is_collection_exists(collection_name):
        self.logger.error(f"Collection does not exist: {collection_name}")
        return []

      try:
        result = self.client.query_points(
          collection_name=collection_name,
          query=vectors,
          limit=top_k
        )

        if not result or not result.points:
          self.logger.warning(f"No results found for the query in collection {collection_name}")
          return []

        self.logger.info(f"Search completed in collection {collection_name} for top {top_k} results")
        
        return [
          RetrievedDocument(
            text=point.payload.get("text", ""),  # type: ignore
            score=point.score  # type: ignore
          )
          for point in result.points
        ]
      except Exception as e:
        self.logger.error(f"Error occurred while searching in collection {collection_name}: {e}")
        return []
    else:
      self.logger.error("Qdrant client is not connected.")
      return []
    



