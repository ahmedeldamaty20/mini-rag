from .BaseDataModel import BaseDataModel
from .db_schemas import Asset
from .enums.DataBaseEnum import DataBaseEnum
from bson import ObjectId

class AssetModel(BaseDataModel):
  def __init__(self, db_client: object):
    super().__init__(db_client)
    self.collection = self.db_client[DataBaseEnum.COLLECTION_ASSET_NAME.value]

  @classmethod
  async def create_instance(cls, db_client: object):
    instance = cls(db_client) # create an instance of the class so that we can call the __init__ method
    await instance.init_collection()
    return instance

  async def init_collection(self):
    # check if the collection not exists, create it and add indexes
    all_collections = await self.db_client.list_collection_names()
    if DataBaseEnum.COLLECTION_ASSET_NAME.value not in all_collections:
      self.collection = self.db_client[DataBaseEnum.COLLECTION_ASSET_NAME.value]
      indexes = Asset.get_indexes()
      for index in indexes:
        await self.collection.create_index(index["key"], name=index["name"], unique=index["unique"])

  async def create_asset(self, asset: Asset):
    result = await self.collection.insert_one(asset.dict(by_alias=True, exclude_unset=True))
    asset._id = result.inserted_id
    return asset

  async def get_assets_by_project_id(self, project_id: str, asset_type: str = None):
    query = {"asset_project_id": ObjectId(project_id) if isinstance(project_id, str) else project_id}
    if asset_type is not None:
      query["asset_type"] = asset_type
    result = self.collection.find(query)
    assets = []
    async for document in result:
      assets.append(
        Asset(**document)
      )
    return assets

  async def get_asset_record(self, asset_project_id: str, asset_name: str):
    query = {
      "asset_project_id": ObjectId(asset_project_id) if isinstance(asset_project_id, str) else asset_project_id,
      "asset_name": asset_name
    }
    result = await self.collection.find_one(query)
    if result is None:
      return None
    return Asset(**result)
  


