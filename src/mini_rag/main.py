from contextlib import asynccontextmanager
from fastapi import FastAPI
from routes import base, data, nlp
from motor.motor_asyncio import AsyncIOMotorClient
from helpers.config import get_settings
from stores.llm.LLMProviderFactory import LLMProviderFactory
from stores.vectordb.VectorDBProviderFactory import VectorDBProviderFactory
from stores.llm.templates.template_parser import TemplateParser
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("uvicorn")

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

    vector_db_provider_factory = VectorDBProviderFactory(settings)
    app.state.vector_db_client = vector_db_provider_factory.get_provider(settings.VECTOR_DB_BACKEND)
    app.state.vector_db_client.connect() # type: ignore

    app.state.template_parser = TemplateParser(settings.PRIMARY_LANGUAGE, settings.DEFAULT_LANGUAGE) # type: ignore

    yield

    # Shutdown
    app.state.mongo_conn.close()
    logger.info("Database connection closed.")

    app.state.vector_db_client.disconnect() # type: ignore
    logger.info("Vector DB connection closed.")

app = FastAPI(title="mini-RAG", version="0.1", lifespan=lifespan)

app.include_router(base.base_router)
app.include_router(data.data_router)
app.include_router(nlp.nlp_router)
