import os

class TemplateParser:
  def __init__(self, language: str, default_language: str):
    self.current_dir = os.path.dirname(os.path.abspath(__file__))
    self.default_language = default_language

    self.set_language(language)

  def set_language(self, language: str):
    if not language:
      language = self.default_language

    language_path = os.path.join(self.current_dir, "locales", language)
    if language and os.path.exists(language_path):
      self.language = language
    else:
      self.language = self.default_language

  def get_template(self, group: str, key: str, vars: dict = {}) -> str:
    if not group or not key:
      return ""

    group_path = os.path.join(self.current_dir, "locales", self.language, f"{group}.py")
    if not os.path.exists(group_path):
      return ""

    module = __import__(f"stores.llm.templates.locales.{self.language}.{group}", fromlist=[group])

    if not module or not hasattr(module, key):
      return ""

    key_attribute = getattr(module, key)
    return key_attribute.substitute(vars) if vars else key_attribute.substitute()
