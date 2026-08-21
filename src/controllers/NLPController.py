from uuid import uuid4

from .BaseController import BaseController
from models.db_schemas import Project, DataChunk, RetrievedDocument
from typing import List, Optional
from stores.llm.LLMEnums import DocumentTypeEnums

class NLPController(BaseController):
  def __init__(self, vectordb_client, embedding_client, generation_client, template_parser):
    super().__init__()

    self.vectordb_client = vectordb_client
    self.embedding_client = embedding_client  
    self.generation_client = generation_client
    self.template_parser = template_parser

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

  async def search_in_vector_db(self, project: Project, query_text: str, top_k: Optional[int] = 10) -> List[RetrievedDocument]:

    collection_name = self.create_collection_name(project.project_id)
    query_vector = self.embedding_client.generate_embedding(query_text, DocumentTypeEnums.QUERY.value)

    if not query_vector:
      return []

    search_results = self.vectordb_client.search_by_vectors(collection_name, query_vector, top_k=top_k)

    if not search_results:
      return []

    return search_results

  async def answer_rag_query(self, project: Project, query_text: str, top_k: Optional[int] = 10):

    answer, full_prompt, chat_history = None, None, None

    retrieved_docs = await self.search_in_vector_db(project, query_text, top_k=top_k)

    if not retrieved_docs:
      return None, None, None

    system_prompt = self.template_parser.get_template("rag", "system_prompt", {})
    documents_prompts = "\n".join([
      self.template_parser.get_template("rag", "document_prompt", {
        "doc_number": str(idx),
        "doc_text": doc.text
      })
      for idx, doc in enumerate(retrieved_docs, start=1)
    ])

    footer_prompt = self.template_parser.get_template("rag", "footer_template", {})

    chat_history = [
      self.generation_client.construct_prompt(system_prompt, self.generation_client.enums.SYSTEM.value)
    ]

    full_prompt = "\n\n".join([  documents_prompts, footer_prompt, f"User Query: {query_text}" ])

    answer = self.generation_client.generate_text(full_prompt, chat_history=chat_history)

    return answer, full_prompt, chat_history
    