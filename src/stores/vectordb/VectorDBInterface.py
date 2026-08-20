from abc import ABC, abstractmethod
from typing import List, Optional

class VectorDBInterface(ABC):

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def disconnect(self):
        pass

    @abstractmethod
    def is_collection_exists(self, collection_name: str) -> bool:
        pass

    @abstractmethod
    def list_all_collections(self) -> List:
        pass

    @abstractmethod
    def get_collection_info(self, collection_name: str) -> dict:
        pass

    @abstractmethod
    def delete_collection(self, collection_name: str):
        pass

    @abstractmethod
    def create_collection(self, collection_name: str, vector_dimension: int, do_reset: bool = False) -> bool:
        pass

    @abstractmethod
    def insert_one(self, collection_name: str, text: str, vector_id: str, vector: list, metadata: Optional[dict] = None) -> bool:
        pass

    @abstractmethod
    def insert_many(self, collection_name: str, texts: List[str], vector_ids: List[str], vectors: List[list], metadatas: Optional[List[dict]] = None, batch_size: int = 100) -> bool:
        pass

    @abstractmethod
    def search_by_vectors(self, collection_name: str, vectors: list, top_k: int) -> list:
        pass
