from mini_rag.celery_app import celery_app, get_setup_utils
from fastapi import status
import asyncio
from typing import Optional
from fastapi.responses import JSONResponse
from controllers import ProcessController
from models import ResponseSignals
from models.ProjectModel import ProjectModel
from models.ChunkModel import ChunkModel
from models.AssetModel import AssetModel
from models.db_schemas import DataChunk
from models.enums.AssetTypeEnum import AssetTypeEnum
from controllers import NLPController
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="tasks.file_processing.process_project_files", retry_kwargs={'max_retries': 3, 'countdown': 60}, auto_retry_for=(Exception,))
def process_project_files(self, project_id: int, file_id: Optional[str], chunk_size: Optional[int], 
                          overlap_size: Optional[int], do_reset: Optional[int]):
  
  return asyncio.run(_process_project_files(self, project_id, file_id, chunk_size, overlap_size, do_reset))

async def _process_project_files(task_instance, project_id: int, file_id: Optional[str], chunk_size: Optional[int], 
                          overlap_size: Optional[int], do_reset: Optional[int]):
  db_engine = None
  vector_db_client = None

  try:
    (db_engine, db_client, llm_provider_factory, generation_client,
      embedding_client, vector_db_provider_factory, vector_db_client, template_parser
    ) = await get_setup_utils()

    project_model = await ProjectModel.create_instance(db_client = db_client)

    project = await project_model.get_project_or_create_one(project_id)

    asset_model = await AssetModel.create_instance(db_client = db_client)

    nlp_controller = NLPController(
      vectordb_client = vector_db_client,
      embedding_client = embedding_client, 
      generation_client = generation_client,
      template_parser = template_parser
    )

    project_files_ids: dict[ObjectId, str] = {}

    if file_id is not None:
      asset_record = await asset_model.get_asset_record(project.project_id, file_id) # type: ignore
      if asset_record is None:
        task_instance.update_state(
          state='FAILURE',
          meta={
            "message": ResponseSignals.FILE_NOT_FOUND.value,
          }
        )
        raise Exception(ResponseSignals.FILE_NOT_FOUND.value)

      project_files_ids[asset_record.asset_id] = str(asset_record.asset_name) # type: ignore
    else:
      project_assets = await asset_model.get_assets_by_project_id(project.project_id, asset_type=AssetTypeEnum.FILE.value) # type: ignore
      project_files_ids = {asset.asset_id: str(asset.asset_name) for asset in project_assets}

    if len(project_files_ids) == 0:
      task_instance.update_state(
        state='FAILURE',
        meta={
          "message": ResponseSignals.NO_FILES_FOUND_FOR_PROCESSING.value,
        }
      )
      raise Exception(ResponseSignals.NO_FILES_FOUND_FOR_PROCESSING.value)

    process_controller = ProcessController(project_id)

    chunk_model = await ChunkModel.create_instance(db_client = db_client)

    if do_reset and vector_db_client is not None:
      _ = await chunk_model.delete_chunks_by_project_id(project.project_id) # type: ignore

      collection_name = nlp_controller.create_collection_name(project.project_id)
      _ = await vector_db_client.delete_collection(collection_name)

    num_inserted = 0
    num_files_processed = 0

    for asset_id, file_id in project_files_ids.items():
      file_content = process_controller.get_file_content(file_id)

      if file_content is None or len(file_content) == 0:
        logger.warning(f"No content found for file_id: {file_id}. Skipping processing.")
        continue
      
      chunks = process_controller.process_file_content(file_content, file_id, chunk_size, overlap_size)

      if chunks is None or len(chunks) == 0:
        logger.error(f"No chunks generated for file_id: {file_id}. Skipping insertion.")
        pass

      file_chunks_records = [
        DataChunk(
          chunk_text=chunk.texts[0],
          chunk_metadata=chunk.metadatas[0] if chunk.metadatas else None,
          chunk_order= i + 1,
          chunk_project_id=project.project_id, # type: ignore
          chunk_asset_id=asset_id
        ) for i, chunk in enumerate(chunks)
      ]

      inserted_result = await chunk_model.insert_many_chunks(file_chunks_records)
      if inserted_result is not None:
        num_inserted += inserted_result
        num_files_processed += 1

      task_instance.update_state(
        state='SUCCESS',
        meta={
          "num_files_processed": num_files_processed,
          "num_chunks_inserted": num_inserted,
          "total_files_to_process": len(project_files_ids),
          "message": ResponseSignals.FILE_PROCESSED_SUCCESSFULLY.value,
        }
      )

      return {
        "message": ResponseSignals.FILE_PROCESSED_SUCCESSFULLY.value,
        "num_chunks_inserted": num_inserted,
        "num_files_processed": num_files_processed,
        "project_id": str(project.project_id)
      }
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
