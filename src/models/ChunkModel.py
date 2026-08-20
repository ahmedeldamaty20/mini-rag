from .BaseDataModel import BaseDataModel
from .db_schemas import DataChunk
from .enums.DataBaseEnum import DataBaseEnum
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import InsertOne

class ChunkModel(BaseDataModel):
  def __init__(self, db_client: AsyncIOMotorDatabase):
    super().__init__(db_client)
    self.collection = self.db_client[DataBaseEnum.COLLECTION_CHUNK_NAME.value]

  @classmethod
  async def create_instance(cls, db_client: AsyncIOMotorDatabase):
    instance = cls(db_client) # create an instance of the class so that we can call the __init__ method
    await instance.init_collection()
    return instance

  async def init_collection(self):
      # check if the collection not exists, create it and add indexes
      all_collections = await self.db_client.list_collection_names()
      if DataBaseEnum.COLLECTION_CHUNK_NAME.value not in all_collections:
        self.collection = self.db_client[DataBaseEnum.COLLECTION_CHUNK_NAME.value]
        indexes = DataChunk.get_indexes()
        for index in indexes:
          await self.collection.create_index(index["key"], name=index["name"], unique=index["unique"])

  async def create_chunk(self, chunk: DataChunk):
    result = await self.collection.insert_one(chunk.model_dump(by_alias=True, exclude_unset=True))
    chunk.id = result.inserted_id
    return chunk

  async def get_chunk_by_id(self, chunk_id: str):
    result = await self.collection.find_one({"_id": ObjectId(chunk_id)})
    if result is None:
      return None
    return DataChunk(**result)

  async def get_chunks_by_project_id(self, project_id: str, page_number: int = 1, page_size: int = 50):
    result = self.collection.find({"chunk_project_id":project_id}).skip((page_number - 1) * page_size).limit(page_size)
    chunks = []
    async for chunk in result:
      chunks.append(DataChunk(**chunk))
    return chunks

  async def get_chunks_count_by_project_id(self, project_id: str):
    count = await self.collection.count_documents({"chunk_project_id":project_id})
    return count

  async def insert_many_chunks(self, chunks: list[DataChunk], bulk_size: int = 100):
    for i in range(0, len(chunks), bulk_size):
      bulk_chunks = chunks[i:i + bulk_size]
      requests = [
        InsertOne(chunk.model_dump(by_alias=True, exclude_unset=True))
        for chunk in bulk_chunks
      ]
      await self.collection.bulk_write(requests)

    return len(chunks)

  async def delete_chunks_by_project_id(self, project_id: ObjectId):
    result = await self.collection.delete_many({"chunk_project_id": project_id})
    return result.deleted_count