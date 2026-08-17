from fastapi import FastAPI
from dotenv import load_dotenv
load_dotenv()
from routes import base

app = FastAPI(title="mini-RAG", version="0.1")
app.include_router(base.base_router)
