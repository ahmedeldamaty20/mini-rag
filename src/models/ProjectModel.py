from .BaseDataModel import BaseDataModel
from .db_schemas import Project
from .enums.DataBaseEnum import DataBaseEnum
from sqlalchemy.future import select
from sqlalchemy import func

class ProjectModel(BaseDataModel):
  def __init__(self, db_client):
    super().__init__(db_client)
    self.db_client = db_client

  @classmethod
  async def create_instance(cls, db_client):
    instance = cls(db_client) # create an instance of the class so that we can call the __init__ method
    return instance
  
  async def create_project(self, project: Project):
    async with self.db_client() as session:
      async with session.begin():
        session.add(project)
      await session.commit()
      await session.refresh(project)
    return project

  async def get_project_or_create_one(self, project_id: int):
    async with self.db_client() as session:
      async with session.begin():
        result = await session.execute(select(Project).where(Project.project_id == project_id))
        project = result.scalar_one_or_none()
        if project is None:
          project = await self.create_project(Project(project_id=project_id))
        return project

  async def get_all_projects(self, page: int=1, page_size: int=10):
    async with self.db_client() as session:
      async with session.begin():
        total_documents = await session.execute(select(func.count(Project.project_id)))
        total_documents = total_documents.scalar_one()
        total_pages = total_documents // page_size
        if (total_documents % page_size) > 0:
          total_pages += 1

        result = await session.execute(select(Project).offset((page - 1) * page_size).limit(page_size))
        projects = result.scalars().all()
        return {
          "projects": projects,
          "total_documents": total_documents,
          "total_pages": total_pages,
          "current_page": page
        }
  