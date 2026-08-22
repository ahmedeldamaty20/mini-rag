from .BaseDataModel import BaseDataModel
from .db_schemas import DataChunk
from .enums.DataBaseEnum import DataBaseEnum
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import InsertOne
from sqlalchemy.future import select
from sqlalchemy import func, delete

class ChunkModel(BaseDataModel):
  def __init__(self, db_client):
    super().__init__(db_client)
    self.db_client = db_client

  @classmethod
  async def create_instance(cls, db_client):
    instance = cls(db_client)
    return instance

  async def create_chunk(self, chunk: DataChunk):
    async with self.db_client() as session:
      async with session.begin():
        session.add(chunk)
      await session.commit()
      await session.refresh(chunk)
    return chunk

  async def get_chunk_by_id(self, chunk_id: str):
    async with self.db_client() as session:
      async with session.begin():
        result = await session.execute(select(DataChunk).where(DataChunk.chunk_id == chunk_id))
        chunk = result.scalar_one_or_none()
        return chunk

  async def get_chunks_by_project_id(self, project_id: str, page_number: int = 1, page_size: int = 50):
    async with self.db_client() as session:
      async with session.begin():
        query = select(DataChunk).where(DataChunk.chunk_project_id == project_id).offset((page_number - 1) * page_size).limit(page_size)
        result = await session.execute(query)
        chunks = result.scalars().all()
        return chunks

  async def get_chunks_count_by_project_id(self, project_id: str):
    async with self.db_client() as session:
      async with session.begin():
        count = await session.execute(select(func.count(DataChunk.chunk_id)).where(DataChunk.chunk_project_id == project_id))
        return count.scalar_one()

  async def insert_many_chunks(self, chunks: list[DataChunk], bulk_size: int = 100):
    async with self.db_client() as session:
      async with session.begin():
        for i in range(0, len(chunks), bulk_size):
          bulk_chunks = chunks[i:i + bulk_size]
          session.add_all(bulk_chunks)
      await session.commit()
      return len(chunks)

  async def delete_chunks_by_project_id(self, project_id: ObjectId):
    async with self.db_client() as session:
      async with session.begin():
        result = await session.execute(
          delete(DataChunk).where(DataChunk.chunk_project_id == project_id)
        )
      await session.commit()
      return result.rowcount