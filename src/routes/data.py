from fastapi import APIRouter, Depends, UploadFile, status, Request
from fastapi.responses import JSONResponse
from helpers.config import get_settings, Settings
from controllers import DataController, ProcessController
from models import ResponseSignals
from .schemas.data import ProcessRequest
from models.ProjectModel import ProjectModel
from models.ChunkModel import ChunkModel
from models.AssetModel import AssetModel
from models.db_schemas import DataChunk, Asset
from models.enums.AssetTypeEnum import AssetTypeEnum
from tasks.file_processing import process_project_files
from controllers import NLPController
from bson import ObjectId
import logging
import aiofiles
import os

logger = logging.getLogger(__name__)

data_router = APIRouter(
  prefix="/api/v1/data",
  tags=["api_v1", "data"],
)

@data_router.post("/upload/{project_id}")
async def upload_data(request: Request, project_id: int, file: UploadFile, app_settings: Settings = Depends(get_settings)):

  project_model = await ProjectModel.create_instance(db_client = request.app.state.db_client)

  project = await project_model.get_project_or_create_one(project_id)

  print(f"Project ID: {project.project_id}, Project Name: {project.project_id}")

  data_controller = DataController()
  is_valid, result_signal = data_controller.validate_uplaoded_file(file)

  if not is_valid:
    return JSONResponse(
      status_code=status.HTTP_400_BAD_REQUEST,
      content={"message": result_signal.value},
    )

  file_path, file_id = data_controller.generate_unique_filepath(file.filename or "", project_id)

  try:
    async with aiofiles.open(file_path, 'wb') as out_file:
      while chunk := await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):
        await out_file.write(chunk)
  except Exception as e:
    logger.error(f"Error occurred while saving the file: {e}")
    return JSONResponse(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      content={"message": ResponseSignals.FILE_UPLOADED_FAILED.value},
    )

  # Save the file metadata to the database
  asset_model = await AssetModel.create_instance(db_client = request.app.state.db_client)
  asset = Asset(
    asset_project_id=project.project_id, # type: ignore
    asset_type=AssetTypeEnum.FILE.value,
    asset_name=file_id,
    asset_size=os.path.getsize(file_path),
  )
  asset_response = await asset_model.create_asset(asset)

  return JSONResponse(
    status_code=status.HTTP_200_OK,
    content={
      "message": ResponseSignals.FILE_UPLOADED_SUCCESSFULLY.value,
      "file_id": str(asset_response.asset_id)
    },
  )

@data_router.post("/process/{project_id}")
async def process_data(request: Request, project_id: int, process_request: ProcessRequest, app_settings: Settings = Depends(get_settings)):
    file_id = process_request.file_id
    chunk_size = process_request.chunk_size
    overlap_size = process_request.overlap_size
    do_reset = process_request.do_reset

    task = process_project_files.delay(project_id=project_id, file_id=file_id, chunk_size=chunk_size, overlap_size=overlap_size, do_reset=do_reset)

    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={
            "message": ResponseSignals.FILE_PROCESSING_STARTED.value,
            "task_id": task.id
        },
    )