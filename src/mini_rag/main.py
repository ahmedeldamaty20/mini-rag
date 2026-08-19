from contextlib import asynccontextmanager
from fastapi import FastAPI
from routes import base, data
from motor.motor_asyncio import AsyncIOMotorClient
from helpers.config import get_settings
from stores.llm.LLMProviderFactory import LLMProviderFactory
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("uvicorn")

app = FastAPI(title="mini-RAG", version="0.1")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    settings = get_settings()
    app.state.mongo_conn = AsyncIOMotorClient(settings.MONGODB_URL)
    app.state.db_client = app.state.mongo_conn[settings.MONGODB_DATABASE]
    logger.info("Database connection established.")

    llm_provider_factory = LLMProviderFactory(settings)

    # generation_client is the LLM provider used for text generation and embedding generation
    app.state.generation_client = llm_provider_factory.get_provider(settings.GENERATION_BACKEND)
    app.state.generation_client.set_generation_model(settings.GENERATION_MODEL_ID) # type: ignore

    # embedding_client is the LLM provider used for embedding generation
    app.state.embedding_client = llm_provider_factory.get_provider(settings.EMBEDDING_BACKEND)
    app.state.embedding_client.set_embedding_model(settings.EMBEDDING_MODEL_ID, settings.EMBEDDING_MODEL_SIZE) # type: ignore

    yield

    # Shutdown
    app.state.mongo_conn.close()
    logger.info("Database connection closed.")

app.include_router(base.base_router)
app.include_router(data.data_router)
