from typing import Optional
from .BaseController import BaseController
from .ProjectController import ProjectController
from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from models import ProcessingEnum
import os

class ProcessController(BaseController):
  def __init__(self, project_id: str):
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
    text_splitter = RecursiveCharacterTextSplitter(
      chunk_size = chunk_size,
      chunk_overlap = overlap_size,
      length_function = len
    )
  
    file_content_texts = [
      rec.page_content
      for rec in file_content
    ]

    file_content_metadata = [
      rec.metadata
      for rec in file_content
    ]

    chunks = text_splitter.create_documents(
      file_content_texts,
      metadatas = file_content_metadata
    )

    return chunks

