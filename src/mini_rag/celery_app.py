from contextlib import asynccontextmanager
import logging
from celery import Celery
from helpers.config import get_settings
from fastapi import FastAPI
from stores.llm.LLMProviderFactory import LLMProviderFactory
from stores.vectordb.VectorDBProviderFactory import VectorDBProviderFactory
from stores.llm.templates.template_parser import TemplateParser
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

settings = get_settings()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("uvicorn")

async def get_setup_utils():
  # Startup
  settings = get_settings()

  postges_conn_str = f"postgresql+asyncpg://{settings.POSTGRES_USERNAME}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_MAIN_DATABASE}"
  db_engine = create_async_engine(postges_conn_str)
  db_client = async_sessionmaker(bind=db_engine, class_=AsyncSession, expire_on_commit=False)
  logger.info("Database connection established.")

  llm_provider_factory = LLMProviderFactory(settings)

  # generation_client is the LLM provider used for text generation and embedding generation
  generation_client = llm_provider_factory.get_provider(settings.GENERATION_BACKEND)
  generation_client.set_generation_model(settings.GENERATION_MODEL_ID) # type: ignore

  # embedding_client is the LLM provider used for embedding generation
  embedding_client = llm_provider_factory.get_provider(settings.EMBEDDING_BACKEND)
  embedding_client.set_embedding_model(settings.EMBEDDING_MODEL_ID, settings.EMBEDDING_MODEL_SIZE) # type: ignore

  vector_db_provider_factory = VectorDBProviderFactory(settings, db_client=db_client)
  vector_db_client = vector_db_provider_factory.get_provider(settings.VECTOR_DB_BACKEND)
  await vector_db_client.connect() # type: ignore 

  template_parser = TemplateParser(settings.PRIMARY_LANGUAGE, settings.DEFAULT_LANGUAGE) # type: ignore

  return(
    db_engine,
    db_client,
    llm_provider_factory,
    generation_client,
    embedding_client,
    vector_db_provider_factory,
    vector_db_client,
    template_parser
  )

# Initialize Celery app
celery_app = Celery(
    settings.APP_NAME,
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
      "tasks.file_processing",
      "tasks.data_indexing",
      "tasks.process_workflow",
      "tasks.mainteinance"
    ]
)

# Configure Celery app
celery_app.conf.update(
  task_serializer=settings.CELERY_TASK_SERIALIZER,
  result_serializer=settings.CELERY_TASK_SERIALIZER,
  accept_content=[settings.CELERY_TASK_SERIALIZER],
  task_acks_late=settings.CELERY_ACKS_LATE,
  task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
  worker_concurrency=settings.CELERY_WORKER_CONCURRENCY,
  task_ignore_result=False,
  result_expires=3600,  # Results expire after 1 hour
  broker_connection_retry_on_startup=True,
  broker_connection_retry=True,
  broker_connection_max_retries=10,
  worker_cancel_long_running_tasks_on_connection_loss=True,
  task_routes={
    "tasks.file_processing.process_project_files": {"queue": "file_processing_queue"},
    "tasks.data_indexing.index_data_content": {"queue": "data_indexing_queue"},
    "tasks.process_workflow.process_and_push_data_to_vector_db": {"queue": "file_processing_queue"},
    "tasks.mainteinance.clean_celery_executions_table": {"queue": "default"},
  },
  beat_schedule={
    "clean_celery_executions_table": {
      "task": "tasks.mainteinance.clean_celery_executions_table",
      "schedule": 86400
    }
  },
  timezone='UTC'
)


celery_app.conf.task_default_queue = "default"
