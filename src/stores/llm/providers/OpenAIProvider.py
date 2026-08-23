from ..LLMInterface import LLMInterface
from ..LLMEnums import OpenAIEnums
from typing import Optional, List, Union
from openai import OpenAI
import logging

class OpenAIProvider(LLMInterface):
  def __init__(self, api_key: str, api_url: Optional[str] = None,
  default_input_max_chars=1000, default_generation_max_output_tokens=1000, default_generation_temperature=0.1):
    self.api_key = api_key
    self.api_url = api_url

    self.default_input_max_chars = default_input_max_chars
    self.default_generation_max_output_tokens = default_generation_max_output_tokens
    self.default_generation_temperature = default_generation_temperature

    self.generation_model_id = None
    
    self.embedding_model_id = None
    self.embedding_model_size = None

    self.client = OpenAI(api_key=self.api_key, base_url=self.api_url) if self.api_key else None

    self.enums = OpenAIEnums

    self.logger = logging.getLogger(__name__)


  def set_generation_model(self, model_id: str):
    self.generation_model_id = model_id

  def set_embedding_model(self, model_id: str, embedding_size: int):
    self.embedding_model_id = model_id
    self.embedding_model_size = embedding_size

  def generate_text(self, prompt: str, chat_history: list = [], max_output_tokens: Optional[int] = None, temperature: Optional[float] = None) -> Optional[str]:
    if not self.client:
      self.logger.error("OpenAI client is not initialized. Please check your API key and URL.")
      return None

    if not self.generation_model_id:
      self.logger.error("Generation model is not set. Please set the generation model before generating text.")
      return None

    if max_output_tokens is None:
      max_output_tokens = self.default_generation_max_output_tokens

    if temperature is None:
      temperature = self.default_generation_temperature

    chat_history.append(self.construct_prompt(prompt, role=OpenAIEnums.USER.value))

    response = self.client.chat.completions.create(
      model=self.generation_model_id,
      messages=chat_history,
      max_tokens=max_output_tokens,
      temperature=temperature
    )

    if not response or not response.choices or len(response.choices) == 0 or not response.choices[0].message:
      self.logger.error("Failed to generate text. Response is empty or invalid.")
      return None

    return response.choices[0].message.content

  def generate_embedding(self, text: Union[str, List[str]], document_type: Optional[str] = None) -> Optional[list[List[float]]]:
    if not self.client:
      self.logger.error("OpenAI client is not initialized. Please check your API key and URL.")
      return None

    if not self.embedding_model_id:
      self.logger.error("Embedding model is not set. Please set the embedding model before generating embeddings.")
      return None

    if isinstance(text, str):
      text = [text]

    response = self.client.embeddings.create(
      model=self.embedding_model_id,
      input=text
    )

    if not response or not response.data or len(response.data) == 0:
      self.logger.error("Failed to generate embedding. Response is empty or invalid.")
      return None

    return [ embedding.embedding for embedding in response.data ]

  def construct_prompt(self, prompt: str, role: str) -> dict:
    return {
      "role": role,
      "content": prompt
    }

  def process_text(self, text: str) -> str:
    if len(text) > self.default_input_max_chars:
      self.logger.warning(f"Input text exceeds the maximum allowed characters ({self.default_input_max_chars}). Truncating the input.")
      return text[:self.default_input_max_chars].strip()
    return text