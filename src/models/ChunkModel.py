from .BaseDataModel import BaseDataModel
from .db_schemas import DataChunk
from .enums.DataBaseEnum import DataBaseEnum
from bson import ObjectId
from pymongo import InsertOne

class ChunkModel(BaseDataModel):
  def __init__(self, db_client: object):
    super().__init__(db_client)
    self.collection = self.db_client[DataBaseEnum.COLLECTION_CHUNK_NAME.value]

  async def create_chunk(self, chunk: DataChunk):
    result = await self.collection.insert_one(chunk.dict(by_alias=True, exclude_unset=True))
    chunk._id = result.inserted_id
    return chunk

  async def get_chunk_by_id(self, chunk_id: str):
    result = await self.collection.find_one({"_id": ObjectId(chunk_id)})
    if result is None:
      return None
    return DataChunk(**result)

  async def insert_many_chunks(self, chunks: list[DataChunk], bulk_size: int = 100):
    for i in range(0, len(chunks), bulk_size):
      bulk_chunks = chunks[i:i + bulk_size]
      requests = [
        InsertOne(chunk.dict(by_alias=True, exclude_unset=True))
        for chunk in bulk_chunks
      ]
      await self.collection.bulk_write(requests)

      return len(chunks)

  async def delete_chunks_by_project_id(self, project_id: ObjectId):
    result = await self.collection.delete_many({"chunk_project_id": project_id})
    return result.deleted_count