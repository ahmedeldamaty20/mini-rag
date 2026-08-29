from mini_rag.celery_app import celery_app, get_setup_utils
from utils.IdempotencyManager import IdempotencyManager
from helpers.config import get_settings
import asyncio
import logging

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="tasks.mainteinance.clean_celery_executions_table", retry_kwargs={'max_retries': 3, 'countdown': 60}, auto_retry_for=(Exception,))
def clean_celery_executions_table(self):
  return asyncio.run(_clean_celery_executions_table(self))

async def _clean_celery_executions_table(task_instance):
  db_engine = None
  vector_db_client = None

  try:
    (db_engine, db_client, llm_provider_factory, generation_client,
      embedding_client, vector_db_provider_factory, vector_db_client, template_parser
    ) = await get_setup_utils()

    idempotency_manager = IdempotencyManager(db_client, db_engine)

    _ = await idempotency_manager.cleanup_old_task_records()

    return True

  except Exception as e:
    logger.error(f"Error processing project files: {str(e)}")
    task_instance.update_state(
      state='FAILURE',
      meta={
        "message": str(e),
      }
    )
    raise e
  finally:
    try:
      if db_engine is not None:
        await db_engine.dispose()
        logger.info("Database connection closed.")
      
      if vector_db_client is not None:
        await vector_db_client.disconnect()
        logger.info("Vector DB connection closed.")
    except Exception as cleanup_error:
      logger.error(f"Error during cleanup: {str(cleanup_error)}")


