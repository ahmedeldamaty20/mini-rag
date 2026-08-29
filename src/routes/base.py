import logging
from time import sleep
from tasks.main_service import send_email_reports

from fastapi import APIRouter, Depends
from helpers.config import get_settings, Settings

logger = logging.getLogger("uvicorn.error")

base_router = APIRouter(
  prefix="/api/v1",
  tags=["api_v1"],
)

@base_router.get("/welcome")
async def welcome_message(app_settings: Settings = Depends(get_settings)):
  app_name = app_settings.APP_NAME
  app_version = app_settings.APP_VERSION
  return {"message": f"Welcome to {app_name}! This is version {app_version}."}

@base_router.get("/send_reports")
async def send_reports(app_settings: Settings = Depends(get_settings)):
  task = send_email_reports.delay(main_wait_time=3)
        
  return {
    "message": "Report sending task has been initiated.",
    "task_id": task.id
  }
