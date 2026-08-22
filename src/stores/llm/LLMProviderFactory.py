from helpers.config import Settings
from .LLMEnums import LLMEnums
from .providers import OpenAIProvider, CohereProvider

class LLMProviderFactory:

  def __init__(self, config: Settings):
    self.config = config

  def get_provider(self, provider_name: str):
    if provider_name == LLMEnums.OPENAI.value:
      # print OPENAI_BASE_URL
      print(f"Using OpenAI provider with base URL: {self.config.OPENAI_BASE_URL}")
      return OpenAIProvider(
        api_key=self.config.OPENAI_API_KEY,
        api_url=self.config.OPENAI_BASE_URL,
        default_input_max_chars=self.config.INPUT_DEFAULT_MAX_CHARACTERS,
        default_generation_max_output_tokens=self.config.GENERATION_DEFAULT_MAX_TOKENS,
        default_generation_temperature=self.config.GENERATION_DEFAULT_TEMPERATURE
      )
    elif provider_name == LLMEnums.COHERE.value:
      return CohereProvider(
        api_key=self.config.COHERE_API_KEY,
        default_input_max_chars=self.config.INPUT_DEFAULT_MAX_CHARACTERS,
        default_generation_max_output_tokens=self.config.GENERATION_DEFAULT_MAX_TOKENS,
        default_generation_temperature=self.config.GENERATION_DEFAULT_TEMPERATURE
      )

    return None
       