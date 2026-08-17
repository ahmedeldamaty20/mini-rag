from fastapi import FastAPI
from routes import base, data

app = FastAPI(title="mini-RAG", version="0.1")
app.include_router(base.base_router)
app.include_router(data.data_router)

