from mini_rag.celery_app import celery_app, get_setup_utils
import asyncio
from typing import Optional
from models import ResponseSignals
from models.ProjectModel import ProjectModel
from models.ChunkModel import ChunkModel
from controllers import NLPController
from tqdm.auto import tqdm
import logging

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="tasks.file_processing.process_project_files", retry_kwargs={'max_retries': 3, 'countdown': 60}, auto_retry_for=(Exception,))
def index_data_content(self, project_id: int, do_reset: Optional[int] = 0):
  return asyncio.run(_index_data_content(self, project_id, do_reset))

async def _index_data_content(task_instance, project_id: int, do_reset: Optional[int] = 0):

  db_engine = None
  vector_db_client = None

  try:

    (db_engine, db_client, llm_provider_factory, generation_client,
      embedding_client, vector_db_provider_factory, vector_db_client, template_parser
    ) = await get_setup_utils()

    project_model = await ProjectModel.create_instance(db_client = db_client)
      
    project = await project_model.get_project_or_create_one(project_id)
  
    if not project:
      task_instance.update_state(
        state='FAILURE',
        meta={
          "message": ResponseSignals.PROJECT_NOT_FOUND.value,
        }
      )
      raise Exception(ResponseSignals.PROJECT_NOT_FOUND.value)
  
    nlp_controller = NLPController(
      vectordb_client = vector_db_client,
      embedding_client = embedding_client, 
      generation_client = generation_client,
      template_parser = template_parser
    )
  
    if do_reset is None:
      do_reset = 0
  
    chunk_model = await ChunkModel.create_instance(db_client = db_client)
  
    chunks_count = await chunk_model.get_chunks_count_by_project_id(project_id = project.project_id) # type: ignore
  
    if chunks_count == 0:
      task_instance.update_state(
        state='FAILURE',
        meta={
          "message": ResponseSignals.NO_FILES_FOUND_FOR_PROCESSING.value,
        }
      )
      raise Exception(ResponseSignals.NO_FILES_FOUND_FOR_PROCESSING.value)

    collection_name = nlp_controller.create_collection_name(project.project_id)

    if vector_db_client is None:
      task_instance.update_state(
        state='FAILURE',
        meta={
          "message": ResponseSignals.VECTOR_DB_CLIENT_NOT_CONNECTED.value,
        }
      )
      raise Exception(ResponseSignals.VECTOR_DB_CLIENT_NOT_CONNECTED.value)
    
    _ = await vector_db_client.create_collection(
      collection_name, 
      nlp_controller.embedding_client.embedding_model_size, # type: ignore
      do_reset=do_reset
    )
  
    pbar = tqdm(total=chunks_count, desc="Indexing data into vector database", unit="chunk", position=0) 
  
    page_size = 50
    inserted_count = 0
  
    for page_number in range(1, (chunks_count // page_size) + 2):
      data_chunks = await chunk_model.get_chunks_by_project_id(project_id = project.project_id, page_number = page_number, page_size =  page_size) # type: ignore
      if not data_chunks:
        break
  
      is_indexed = await nlp_controller.index_into_vector_db(project, data_chunks)
      if not is_indexed:
        task_instance.update_state(
          state='FAILURE',
          meta={
            "message": ResponseSignals.INSERT_INTO_VECTOR_DB_ERROR.value,
          }
        )
        raise Exception(ResponseSignals.INSERT_INTO_VECTOR_DB_ERROR.value)

      pbar.update(len(data_chunks))
      inserted_count += len(data_chunks)
  
    task_instance.update_state(
      state='SUCCESS',
      meta={
        "message": ResponseSignals.INSERT_INTO_VECTOR_DB_SUCCESS.value,
        "inserted_count": inserted_count
      }
    )

    return {
      "message": ResponseSignals.INSERT_INTO_VECTOR_DB_SUCCESS.value,
      "inserted_count": inserted_count
    }

  except Exception as e:
    logger.error(f"Error during indexing: {str(e)}")
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