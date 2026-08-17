from fastapi import APIRouter, Depends, UploadFile, status
from fastapi.responses import JSONResponse
from helpers.config import get_settings, settings
from controllers import DataController, ProjectController, ProcessController
from models import ResponseSignals
from .schemas.data import ProcessRequest
import logging
import aiofiles
import os

logging.basicConfig(level=logging.INFO)

data_router = APIRouter(
  prefix="/api/v1/data",
  tags=["api_v1", "data"],
)

@data_router.post("/upload/{project_id}")
async def upload_data(project_id: str, file: UploadFile, app_settings: settings = Depends(get_settings)):

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
    logging.error(f"Error occurred while saving the file: {e}")
    return JSONResponse(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      content={"message": ResponseSignals.FILE_UPLOAD_FAILED.value},
    )

  return JSONResponse(
    status_code=status.HTTP_200_OK,
    content={
      "message": ResponseSignals.FILE_UPLOADED_SUCCESSFULLY.value,
      "file_id": file_id
    },
  )

@data_router.post("/process/{project_id}")
async def process_data(project_id: str, request: ProcessRequest, app_settings: settings = Depends(get_settings)):
    file_id = request.file_id
    chunk_size = request.chunk_size
    overlap_size = request.overlap_size
    
    process_controller = ProcessController(project_id)

    file_content = process_controller.get_file_content(file_id)

    chunks = process_controller.process_file_content(file_content, file_id, chunk_size, overlap_size)

    if chunks is None or len(chunks) == 0:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": ResponseSignals.FILE_PROCESSING_FAILED.value},
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": ResponseSignals.FILE_PROCESSED_SUCCESSFULLY.value,
            "chunks": [chunk.page_content for chunk in chunks]
        },
    )
