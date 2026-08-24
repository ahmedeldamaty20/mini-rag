from typing import Any, List, Optional
from .BaseController import BaseController
from .ProjectController import ProjectController
from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders import PyMuPDFLoader
from dataclasses import dataclass
from models import ProcessingEnum
import os

@dataclass
class Document:
  texts: list[str]
  metadatas: Optional[list[dict[Any, Any]]] = None

class ProcessController(BaseController):
  def __init__(self, project_id: int):
    super().__init__()

    self.project_id = project_id
    self.project_directory_path = ProjectController().get_project_directory_path(project_id)

  def get_file_extension(self, file_id: str):
    return os.path.splitext(file_id)[-1]

  def get_file_loader(self, file_id: str):
    file_extension = self.get_file_extension(file_id)
    file_path = os.path.join(self.project_directory_path, file_id)

    if not os.path.exists(file_path):
      return None

    if file_extension == ProcessingEnum.TXT.value:
      return TextLoader(file_path, encoding="utf-8")
    elif file_extension == ProcessingEnum.PDF.value:
      return PyMuPDFLoader(file_path)
    else:
      return None

  def get_file_content(self, file_id: str):
    loader = self.get_file_loader(file_id)
    if loader is None:
      return None
    documents = loader.load()
    return documents

  def process_file_content(self, file_content: list, file_id: str, chunk_size: Optional[int] = 1000, overlap_size: Optional[int] = 20):

    file_content_texts = [
      rec.page_content
      for rec in file_content
    ]

    file_content_metadata = [
      rec.metadata
      for rec in file_content
    ]

    chunks = self.process_simpler_splitter(
      file_content_texts,
      file_content_metadata,
      chunk_size=chunk_size if chunk_size else 1000
    )

    return chunks

  def process_simpler_splitter(self, file_content: List[str], metadatas: List[dict], chunk_size: int = 1000, splitter: str = "\n"):
    full_text = " ".join(file_content)

    lines = [chunk.strip() for chunk in full_text.split(splitter) if len(chunk.strip()) > 1 ]

    chunks: list[Document] = []
    current_chunk = ""

    for line in lines:
      current_chunk += line + splitter
      if len(current_chunk) >= chunk_size:
        chunks.append(Document(
          texts=[current_chunk.strip()],
          metadatas=metadatas
        ))
        current_chunk = ""

    if current_chunk:
      chunks.append(Document(
        texts=[current_chunk.strip()],
        metadatas=metadatas
      ))

    return chunks
