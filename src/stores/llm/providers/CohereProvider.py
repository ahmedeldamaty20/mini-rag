from ..LLMInterface import LLMInterface
from ..LLMEnums import CohereEnums, DocumentTypeEnums
from typing import Optional
import cohere
import logging

class CohereProvider(LLMInterface):
  def __init__(self, api_key: str, 
  default_input_max_chars=1000, default_generation_max_output_tokens=1000, default_generation_temperature=0.1):
    self.api_key = api_key

    self.default_input_max_chars = default_input_max_chars
    self.default_generation_max_output_tokens = default_generation_max_output_tokens
    self.default_generation_temperature = default_generation_temperature

    self.generation_model_id = None

    self.embedding_model_id = None
    self.embedding_model_size = None

    self.client = cohere.ClientV2(api_key=self.api_key)

    self.logger = logging.getLogger(__name__)

  def set_generation_model(self, model_id: str) :
      self.generation_model_id = model_id
  
  def set_embedding_model(self, model_id: str, embedding_size: int):
    self.embedding_model_id = model_id
    self.embedding_model_size = embedding_size

  def generate_text(self, prompt: str, chat_history: list = [], max_output_tokens: Optional[int] = None, temperature: Optional[float] = None) -> Optional[str]:
    if not self.client:
      self.logger.error("Cohere client is not initialized. Please check your API key and URL.")
      return None

    if not self.generation_model_id:
      self.logger.error("Generation model is not set. Please set the generation model before generating text.")
      return None

    if max_output_tokens is None:
      max_output_tokens = self.default_generation_max_output_tokens

    if temperature is None:
      temperature = self.default_generation_temperature

    chat_history.append(self.construct_prompt(prompt, role=CohereEnums.USER.value))

    response = self.client.chat(
      model = self.generation_model_id,
      messages = chat_history,
      max_tokens = max_output_tokens,
      temperature = temperature
    )

    if not response or not response.message or not response.message.content:
      self.logger.error("Failed to generate text. Response is empty or invalid.")
      return None

    return response.message.content[0].text # type: ignore

  def generate_embedding(self, text: str, document_type: Optional[str] = None) -> Optional[list[float]]:
    if not self.client:
      self.logger.error("Cohere client is not initialized. Please check your API key and URL.")
      return None

    if not self.embedding_model_id:
      self.logger.error("Embedding model is not set. Please set the embedding model before generating embeddings.")
      return None

    input_type = CohereEnums.DOCUMENT.value
    if document_type == DocumentTypeEnums.QUERY.value:
      input_type = CohereEnums.QUERY.value

    response = self.client.embed(
      model = self.embedding_model_id,
      texts = [self.process_text(text)],
      input_type = input_type,
      embedding_types=["float"]
    )

    if not response or not response.embeddings or not response.embeddings.float_:
      self.logger.error("Failed to generate embedding. Response is empty or invalid.")
      return None

    return response.embeddings.float_[0]

  def construct_prompt(self, prompt: str, role: str) -> dict:
    return { 
      "role": role,
      "content": self.process_text(prompt)
    }

  def process_text(self, text: str) -> str:
    if len(text) > self.default_input_max_chars:
      self.logger.warning(f"Input text exceeds the maximum allowed characters ({self.default_input_max_chars}). Truncating the input.")
      return text[:self.default_input_max_chars].strip()
    return text
