from typing import Dict, Any, Optional

from .BaseDataModel import BaseDataModel
from .db_schemas import Asset
from .enums.DataBaseEnum import DataBaseEnum
from bson import ObjectId
from sqlalchemy.future import select
from sqlalchemy import func, delete

class AssetModel(BaseDataModel):
  def __init__(self, db_client):
    super().__init__(db_client)
    self.db_client = db_client

  @classmethod
  async def create_instance(cls, db_client):
    instance = cls(db_client) # create an instance of the class so that we can call the __init__ method
    return instance

  async def create_asset(self, asset: Asset):
    async with self.db_client() as session:
      async with session.begin():
        session.add(asset)
      await session.commit()
      await session.refresh(asset)
    return asset

  async def get_assets_by_project_id(self, project_id: str, asset_type: Optional[str] = None):
    async with self.db_client() as session:
      async with session.begin():
        query = select(Asset).where(Asset.asset_project_id == project_id)
        if asset_type:
          query = query.where(Asset.asset_type == asset_type)
        result = await session.execute(query)
        assets = result.scalars().all()
        return assets

  async def get_asset_record(self, asset_project_id: str, asset_name: str):
    async with self.db_client() as session:
      async with session.begin():
        result = await session.execute(
          select(Asset).where(
            Asset.asset_project_id == asset_project_id,
            Asset.asset_name == asset_name
          )
        )
        asset = result.scalar_one_or_none()
        return asset
  


