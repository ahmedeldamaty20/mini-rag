from ..VectorDBInterface import VectorDBInterface
from ..VectorDBEnums import DistanceMetodEnums, PgVectorDistanceMethodEnums, PgVectorIndexTypeEnums, PgVectorTableSchemaEnums, PgVectorQueryOperatorEnums
from models.db_schemas import RetrievedDocument
from sqlalchemy.sql import text as sql_text
from typing import List, Optional
import logging
import json

class PgVectorProvider(VectorDBInterface):

  def __init__(self, db_client, distance_method: str, default_vector_size: int, index_threadhold: int = 1000):
    self.db_client = db_client
    self.default_vector_size = default_vector_size
    self.index_threadhold = index_threadhold

    if distance_method == DistanceMetodEnums.COSINE.value:
      self.distance_method = PgVectorDistanceMethodEnums.COSINE.value
    elif distance_method == DistanceMetodEnums.DOT.value:
      self.distance_method = PgVectorDistanceMethodEnums.DOT.value
    elif distance_method == DistanceMetodEnums.EUCLIDEAN.value:
      self.distance_method = PgVectorDistanceMethodEnums.EUCLIDEAN.value
    else:
      raise ValueError(f"Unsupported distance method: {distance_method}")

    self.pgvector_table_prefix = PgVectorTableSchemaEnums._PREFIX.value

    self.default_index_name = lambda collection_name: f"{self.pgvector_table_prefix}{collection_name}_vector_idx"

    self.logger = logging.getLogger("uvicorn")

  def _get_safe_table_name(self, collection_name: str) -> str:
    table_name = f"{self.pgvector_table_prefix}{collection_name}"
    if not table_name.replace("_", "").isalnum():
      self.logger.error(f"Invalid collection name: {collection_name}. Only alphanumeric characters and underscores are allowed.")
      raise ValueError(f"Invalid collection name: {collection_name}. Only alphanumeric characters and underscores are allowed.")
    return table_name

  async def connect(self):
    async with self.db_client.connect() as session:
      async with session.begin():
        await session.execute(sql_text(
          "CREATE EXTENSION IF NOT EXISTS vector"
        ))

  async def disconnect(self):
    pass

  async def is_collection_exists(self, collection_name: str) -> bool:
    table_name = self._get_safe_table_name(collection_name)
    async with self.db_client.connect() as session:
      async with session.begin():
        result = await session.execute(sql_text('''
          SELECT EXISTS (
            SELECT 1 FROM pg_tables 
            WHERE schemaname = :schema AND tablename = :table_name
          )
        '''), {"schema": "public", "table_name": table_name})
        exists = result.scalar_one()
    return bool(exists)

  async def list_all_collections(self) -> List[str]:
    collections = []
    async with self.db_client.connect() as session:
      async with session.begin():
        result = await session.execute(sql_text(
          'SELECT tablename FROM pg_tables WHERE schemaname = :schema AND tablename LIKE :prefix'
        ), {"schema": "public", "prefix": f"{self.pgvector_table_prefix}%"})
        table_names = result.scalars().all()
        collections = [
          name[len(self.pgvector_table_prefix):] for name in table_names
        ]
    return collections

  async def get_collection_info(self, collection_name: str) -> dict:
    table_name = self._get_safe_table_name(collection_name)
    collection_info = {}

    async with self.db_client.connect() as session:
      async with session.begin():
        table_info = await session.execute(sql_text('''
          SELECT schemaname, tablename, tableowner, tablespace, hasindexes
          FROM pg_tables
          WHERE tablename = :collection_name
          '''
        ), {"collection_name": table_name})

        table_data = table_info.fetchone()

        count_result = await session.execute(sql_text(
          f'SELECT COUNT(*) FROM "{table_name}"'
        ))
        table_records_count = count_result.scalar_one()

        collection_info = {
          "table_info": dict(table_data._mapping) if table_data else {},
          "table_records_count": table_records_count
        }

    return collection_info

  async def delete_collection(self, collection_name: str):
    table_name = self._get_safe_table_name(collection_name)
    async with self.db_client.connect() as session:
      async with session.begin():
        await session.execute(sql_text(
          f'DROP TABLE IF EXISTS "{table_name}"'
        ))
    self.logger.info(f"Collection deleted: {collection_name}")

  async def create_collection(self, collection_name: str, vector_dimension: int, do_reset: bool = False) -> bool:
    if await self.is_collection_exists(collection_name):
      if do_reset:
        await self.delete_collection(collection_name)
        self.logger.info(f"Collection reset: {collection_name}")
      else:
        self.logger.warning(f"Collection already exists: {collection_name}")
        return False

    table_name = self._get_safe_table_name(collection_name)
    async with self.db_client.connect() as session:
      async with session.begin():
        await session.execute(sql_text(f'''
          CREATE TABLE "{table_name}" (
            {PgVectorTableSchemaEnums.ID.value} BIGSERIAL PRIMARY KEY,
            {PgVectorTableSchemaEnums.TEXT.value} TEXT,
            {PgVectorTableSchemaEnums.VECTOR.value} VECTOR({vector_dimension}),
            {PgVectorTableSchemaEnums.CHUNK_ID.value} INTEGER,
            {PgVectorTableSchemaEnums.METADATA.value} JSONB DEFAULT '{{}}'::JSONB,
            CONSTRAINT fk_chunk_id FOREIGN KEY ({PgVectorTableSchemaEnums.CHUNK_ID.value}) REFERENCES chunks(id) ON DELETE CASCADE
          )
        '''))
    self.logger.info(f"Collection created: {collection_name} with dimension {vector_dimension}")
    return True

  async def is_index_exists(self, collection_name: str) -> bool:
    index_name = self.default_index_name(collection_name)
    async with self.db_client.connect() as session:
      async with session.begin():
        result = await session.execute(sql_text('''
          SELECT EXISTS (
            SELECT 1 FROM pg_indexes 
            WHERE schemaname = :schema AND tablename = :table_name AND indexname = :index_name
          )
        '''), {"schema": "public", "table_name": self._get_safe_table_name(collection_name), "index_name": index_name})
        exists = result.scalar_one()
    return bool(exists)

  async def create_vector_index(self, collection_name: str, index_type: str = PgVectorIndexTypeEnums.IVFFLAT.value) -> bool:
    if not await self.is_collection_exists(collection_name):
      self.logger.error(f"Collection does not exist: {collection_name}")
      return False

    index_name = self.default_index_name(collection_name)
    table_name = self._get_safe_table_name(collection_name)

    if await self.is_index_exists(collection_name):
      self.logger.warning(f"Index already exists for collection: {collection_name}")
      return False

    async with self.db_client.connect() as session:
      async with session.begin():
        count_result = await session.execute(sql_text(
          f'SELECT COUNT(*) FROM "{table_name}"'
        ))
        table_records_count = count_result.scalar_one()

        if table_records_count < self.index_threadhold:
          self.logger.info(f"Skipping index creation for collection: {collection_name} as record count ({table_records_count}) is below threshold ({self.index_threadhold})")
          return False
        
        await session.execute(sql_text(f'''
          CREATE INDEX "{index_name}" ON "{table_name}" USING {index_type} ({PgVectorTableSchemaEnums.VECTOR.value} {self.distance_method})
        '''))
    self.logger.info(f"Index created for collection: {collection_name} with index type: {index_type}")
    return True

  async def reset_vector_index(self, collection_name: str, index_type: str = PgVectorIndexTypeEnums.IVFFLAT.value) -> bool:
    if not await self.is_collection_exists(collection_name):
      self.logger.error(f"Collection does not exist: {collection_name}")
      return False

    index_name = self.default_index_name(collection_name)

    if await self.is_index_exists(collection_name):
      async with self.db_client.connect() as session:
        async with session.begin():
          await session.execute(sql_text(f'''
            DROP INDEX IF EXISTS "{index_name}"
          '''))
      self.logger.info(f"Index dropped for collection: {collection_name}")

    return await self.create_vector_index(collection_name, index_type)

  async def insert_one(self, collection_name: str, text: str, chunk_id: str, vector: list, metadata: Optional[dict] = None) -> bool:
    if not await self.is_collection_exists(collection_name):
      self.logger.error(f"Collection does not exist: {collection_name}")
      return False

    if not chunk_id:
      self.logger.error("Vector ID is required for insertion.")
      return False

    table_name = self._get_safe_table_name(collection_name)
    async with self.db_client.connect() as session:
      async with session.begin():
        await session.execute(sql_text(f'''
          INSERT INTO "{table_name}" ({PgVectorTableSchemaEnums.TEXT.value}, {PgVectorTableSchemaEnums.VECTOR.value}, {PgVectorTableSchemaEnums.CHUNK_ID.value}, {PgVectorTableSchemaEnums.METADATA.value})
          VALUES (:text, :vector, :chunk_id, :metadata)
        '''), 
        {
          "text": text,
          "vector": "[" + ", ".join(str(x) for x in vector) + "]",
          "chunk_id": chunk_id,
          "metadata": json.dumps(metadata) if metadata else '{}'
        })
    self.logger.info(f"Inserted point with ID {chunk_id} into collection {collection_name}")
    return True

  async def insert_many(self, collection_name: str, texts: List[str], chunk_ids: List[str], vectors: List[list], metadatas: Optional[List[dict]] = None, batch_size: int = 100) -> bool:
    if not await self.is_collection_exists(collection_name):
      self.logger.error(f"Collection does not exist: {collection_name}")
      return False

    if len(texts) != len(chunk_ids) or len(texts) != len(vectors):
      self.logger.error("Length of texts, chunk_ids, and vectors must be the same.")
      return False

    if metadatas and len(metadatas) != len(texts):
      self.logger.error("Length of metadatas must match length of texts.")
      return False

    table_name = self._get_safe_table_name(collection_name)
    async with self.db_client.connect() as session:
      async with session.begin():
        for i in range(0, len(texts), batch_size):
          batch_texts = texts[i:i + batch_size]
          batch_chunk_ids = chunk_ids[i:i + batch_size]
          batch_vectors = vectors[i:i + batch_size]
          batch_metadatas = metadatas[i:i + batch_size] if metadatas else [{}] * len(batch_texts)

          values = [
            f"(:text_{j}, :vector_{j}, :chunk_id_{j}, :metadata_{j})"
            for j in range(len(batch_texts))
          ]
          values_str = ", ".join(values)

          params = {}
          for j in range(len(batch_texts)):
            params[f"text_{j}"] = batch_texts[j]
            params[f"vector_{j}"] = "[" + ", ".join(str(x) for x in batch_vectors[j]) + "]"
            params[f"chunk_id_{j}"] = batch_chunk_ids[j]
            params[f"metadata_{j}"] = json.dumps(batch_metadatas[j]) if batch_metadatas else '{}'

          await session.execute(sql_text(f'''
            INSERT INTO "{table_name}" ({PgVectorTableSchemaEnums.TEXT.value}, {PgVectorTableSchemaEnums.VECTOR.value}, {PgVectorTableSchemaEnums.CHUNK_ID.value}, {PgVectorTableSchemaEnums.METADATA.value})
            VALUES {values_str}
          '''), params)
    self.logger.info(f"Inserted {len(texts)} points into collection {collection_name}")
    return True

  async def search_by_vectors(self, collection_name: str, vectors: list, top_k: int) -> List[RetrievedDocument]:
    if not await self.is_collection_exists(collection_name):
      self.logger.error(f"Collection does not exist: {collection_name}")
      return []

    table_name = self._get_safe_table_name(collection_name)
    retrieved_documents = []

    if self.distance_method == PgVectorDistanceMethodEnums.COSINE.value:
      operand = PgVectorQueryOperatorEnums.COSINE.value
    elif self.distance_method == PgVectorDistanceMethodEnums.DOT.value:
      operand = PgVectorQueryOperatorEnums.DOT.value
    elif self.distance_method == PgVectorDistanceMethodEnums.EUCLIDEAN.value:
      operand = PgVectorQueryOperatorEnums.EUCLIDEAN.value
    else:
      self.logger.error(f"Unsupported distance method: {self.distance_method}")
      return []

    async with self.db_client.connect() as session:
      async with session.begin():
        vector = "[" + ", ".join(str(x) for x in vectors) + "]"
        result = await session.execute(sql_text(f'''
          SELECT {PgVectorTableSchemaEnums.TEXT.value} as text, 1 - ({PgVectorTableSchemaEnums.VECTOR.value} {operand} :vector) as score
          FROM "{table_name}"
          ORDER BY score DESC
          LIMIT :top_k
        '''), {"vector": vector, "top_k": top_k})
        rows = result.fetchall()

        retrieved_documents = [
          RetrievedDocument(text=row.text, score=row.score)
          for row in rows
        ]

    return retrieved_documents
