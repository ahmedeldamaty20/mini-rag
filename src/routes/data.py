from fastapi import APIRouter, Depends, UploadFile, status, Request
from fastapi.responses import JSONResponse
from helpers.config import get_settings, settings
from controllers import DataController, ProjectController, ProcessController
from models import ResponseSignals
from .schemas.data import ProcessRequest
from models.ProjectModel import ProjectModel
from models.ChunkModel import ChunkModel
from models.AssetModel import AssetModel
from models.db_schemas import DataChunk, Asset
from models.enums.AssetTypeEnum import AssetTypeEnum
import logging
import aiofiles
import os

logger = logging.getLogger(__name__)

data_router = APIRouter(
  prefix="/api/v1/data",
  tags=["api_v1", "data"],
)

@data_router.post("/upload/{project_id}")
async def upload_data(request: Request, project_id: str, file: UploadFile, app_settings: settings = Depends(get_settings)):

  project_model = await ProjectModel.create_instance(db_client = request.app.db_client)

  project = await project_model.get_project_or_create_one(project_id)

  data_controller = DataController()
  is_valid, result_signal = data_controller.validate_uplaoded_file(file)

  if not is_valid:
    return JSONResponse(
      status_code=status.HTTP_400_BAD_REQUEST,
      content={"message": result_signal.value},
    )

  project_directory_path = ProjectController().get_project_directory_path(project_id)
  file_path, file_id = data_controller.generate_unique_filepath(file.filename, project_id)

  try:
    async with aiofiles.open(file_path, 'wb') as out_file:
      while chunk := await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):
        await out_file.write(chunk)
  except Exception as e:
    logger.error(f"Error occurred while saving the file: {e}")
    return JSONResponse(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      content={"message": ResponseSignals.FILE_UPLOAD_FAILED.value},
    )

  # Save the file metadata to the database
  asset_model = await AssetModel.create_instance(db_client = request.app.db_client)
  asset = Asset(
    asset_project_id=project.id,
    asset_type=AssetTypeEnum.FILE.value,
    asset_name=file_id,
    asset_size=os.path.getsize(file_path),
  )
  asset_response = await asset_model.create_asset(asset)

  return JSONResponse(
    status_code=status.HTTP_200_OK,
    content={
      "message": ResponseSignals.FILE_UPLOADED_SUCCESSFULLY.value,
      "file_id": str(asset_response._id)
    },
  )

@data_router.post("/process/{project_id}")
async def process_data(request: Request, project_id: str, process_request: ProcessRequest, app_settings: settings = Depends(get_settings)):
    # file_id = process_request.file_id
    chunk_size = process_request.chunk_size
    overlap_size = process_request.overlap_size
    do_reset = process_request.do_reset

    project_model = await ProjectModel.create_instance(db_client = request.app.db_client)
    
    project = await project_model.get_project_or_create_one(project_id)

    asset_model = await AssetModel.create_instance(db_client = request.app.db_client)

    project_files_ids = {}

    if process_request.file_id is not None:
      asset_record = await asset_model.get_asset_record(project.id, process_request.file_id)
      if asset_record is None:
        return JSONResponse(
          status_code=status.HTTP_400_BAD_REQUEST,
          content={"message": ResponseSignals.FILE_NOT_FOUND.value},
        )
      project_files_ids[asset_record.id] = str(asset_record.asset_name)
    else:
      project_assets = await asset_model.get_assets_by_project_id(project.id, asset_type=AssetTypeEnum.FILE.value)
      project_files_ids = {str(asset.id): str(asset.asset_name) for asset in project_assets}

    if len(project_files_ids) == 0:
      return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"message": ResponseSignals.NO_FILES_FOUND_FOR_PROCESSING.value},
      )
    
    process_controller = ProcessController(project_id)

    chunk_model = await ChunkModel.create_instance(db_client = request.app.db_client)

    if do_reset:
      deleted_count = await chunk_model.delete_chunks_by_project_id(project.id)
    
    num_inserted = 0
    num_files_processed = 0

    for asset_id, file_id in project_files_ids.items():
      file_content = process_controller.get_file_content(file_id)

      if file_content is None or len(file_content) == 0:
        logger.warning(f"No content found for file_id: {file_id}. Skipping processing.")
        continue
      
      chunks = process_controller.process_file_content(file_content, file_id, chunk_size, overlap_size)
  
      if chunks is None or len(chunks) == 0:
        return JSONResponse(
          status_code=status.HTTP_400_BAD_REQUEST,
          content={"message": ResponseSignals.FILE_PROCESSING_FAILED.value},
        )
  
      file_chunks_records = [
        DataChunk(
          _id=None,
          chunk_text=chunk.page_content,
          chunk_metadata=chunk.metadata,
          chunk_order= i + 1,
          chunk_project_id=project.id,
          chunk_asset_id=asset_id
        ) for i, chunk in enumerate(chunks)
      ]
  
      num_inserted += await chunk_model.insert_many_chunks(file_chunks_records)
      num_files_processed += 1

    return JSONResponse(
      status_code=status.HTTP_200_OK,
      content={
        "message": ResponseSignals.FILE_PROCESSED_SUCCESSFULLY.value,
        "num_chunks_inserted": num_inserted,
        "num_files_processed": num_files_processed,
        "project_id": str(project.id)
      },
    )
