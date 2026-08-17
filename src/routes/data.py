from fastapi import APIRouter, Depends, UploadFile, status
from fastapi.responses import JSONResponse
from helpers.config import get_settings, settings
from controllers import DataController, ProjectController
from models import ResponseSignals
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

  project_directory_path = ProjectController().get_project_path(project_id)
  file_path = data_controller.generate_unique_filename(file.filename, project_id)

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
      "file_path": file_path
    },
  )
