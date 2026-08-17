from .BaseController import BaseController
import os

class ProjectController(BaseController):
  def __init__(self):
    super().__init__()

  def get_project_path(self, project_id: str) -> str:
    project_directory = os.path.join(self.files_dir, project_id)

    if not os.path.exists(project_directory):
      os.makedirs(project_directory)

    return project_directory
