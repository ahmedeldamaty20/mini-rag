from .BaseController import BaseController
from .ProjectController import ProjectController
from fastapi import UploadFile
from models import ResponseSignals
import os
import re

class DataController(BaseController):
  def __init__(self):
    super().__init__()

  def validate_uplaoded_file(self, file: UploadFile):
    # Validate file size
    if file.size > self.app_settings.FILE_MAX_SIZE * 1024 * 1024: # type: ignore
      return False, ResponseSignals.FILE_SIZE_EXCEEDS_LIMIT

    # Validate file type
    if file.content_type not in self.app_settings.FILE_ALLOWED_TYPES:
      return False, ResponseSignals.FILE_TYPE_NOT_ALLOWED

    return True, ResponseSignals.FILE_VALIDATION_SUCCESS

  def generate_unique_filepath(self, original_filename: str, project_id: str) -> str:
    random_key = self.generate_random_string(12)
    project_directory_path = ProjectController().get_project_directory_path(project_id)

    cleaned_filename = self.get_cleaned_file_name(original_filename)

    new_filename = f"{random_key}_{cleaned_filename}"
    new_file_path = os.path.join(project_directory_path, new_filename)

    # Ensure the new filename is unique within the project directory
    while os.path.exists(new_file_path):
      random_key = self.generate_random_string(12)
      new_filename = f"{random_key}_{cleaned_filename}"
      new_file_path = os.path.join(project_directory_path, new_filename)

    return new_file_path, new_filename # type: ignore

  def get_cleaned_file_name(self, original_filename: str) -> str:
    # Remove any special characters and spaces from the filename
    cleaned_filename = re.sub(r'[^a-zA-Z0-9_.-]', '_', original_filename)
    return cleaned_filename
    