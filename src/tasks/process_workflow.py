from mini_rag.celery_app import celery_app
from celery import chain
from tasks.file_processing import process_project_files
from tasks.data_indexing import _index_data_content
from typing import Optional
from models import ResponseSignals
import asyncio
import logging

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="tasks.process_workflow.push_after_processing", retry_kwargs={'max_retries': 3, 'countdown': 60}, auto_retry_for=(Exception,))
def push_after_processing(self, prev_task_result):

  project_id = prev_task_result.get('project_id')
  do_reset = prev_task_result.get('do_reset', 0)

  if isinstance(project_id, str):
    project_id = int(project_id)

  task_result = asyncio.run(_index_data_content(self, project_id=project_id, do_reset=do_reset))

  return {
    "project_id": prev_task_result['project_id'],
    "do_reset": prev_task_result['do_reset'],
    "task_result": task_result
  }

@celery_app.task(bind=True, name="tasks.process_workflow.process_and_push_data_to_vector_db", retry_kwargs={'max_retries': 3, 'countdown': 60}, auto_retry_for=(Exception,))
def process_and_push_data_to_vector_db(self, project_id: int, file_id: Optional[str], chunk_size: Optional[int], 
                          overlap_size: Optional[int], do_reset: Optional[int]):
  workflow_chain = chain(
    process_project_files.s(project_id=project_id, file_id=file_id, chunk_size=chunk_size, overlap_size=overlap_size, do_reset=do_reset),
    push_after_processing.s()  
  )

  result = workflow_chain.apply_async()

  assert result is not None
  return {
    "message": ResponseSignals.FILE_PROCESSING_STARTED.value,
    "project_id": project_id,
    "file_id": file_id,
    "chunk_size": chunk_size,
    "overlap_size": overlap_size,
    "do_reset": do_reset,
    "task_id": result.id,
    "tasks": ["tasks.file_processing.process_project_files", "tasks.process_workflow.push_after_processing"]
  }
  