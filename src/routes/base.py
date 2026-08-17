from fastapi import FastAPI, APIRouter
import os

base_router = APIRouter(
    prefix="/api/v1",
    tags=["api_v1"],
)

@base_router.get("/welcome")
async def welcome_message():
    app_name = os.getenv("APP_NAME", "mini-RAG")
    app_version = os.getenv("APP_VERSION", "0.1")
    return {"message": f"Welcome to {app_name}! This is version {app_version}."}