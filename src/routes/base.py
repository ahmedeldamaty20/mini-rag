from fastapi import APIRouter, Depends
from helpers.config import get_settings, settings

base_router = APIRouter(
    prefix="/api/v1",
    tags=["api_v1"],
)

@base_router.get("/welcome")
async def welcome_message(app_settings: settings = Depends(get_settings)):
    app_name = app_settings.APP_NAME
    app_version = app_settings.APP_VERSION
    return {"message": f"Welcome to {app_name}! This is version {app_version}."}
