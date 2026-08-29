import hashlib
import json
from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy import select, delete
from models.db_schemas.minirag.schemas.celery_task_execution import CeleryTaskExecution

class IdempotencyManager:
  def __init__(self, db_client, db_engine):
    self.db_client = db_client
    self.db_engine = db_engine

  def create_args_hash(self, task_name: str, task_args: dict):
    compiled_args = {
      **task_args,
      "task_name": task_name
    }

    args_json = json.dumps(compiled_args, sort_keys=True, default=str) # Sort keys to ensure consistent hashing
    args_hash = hashlib.sha256(args_json.encode()).hexdigest()

    return args_hash

  async def create_task_record(self, task_name: str, task_args: dict, celery_task_id: Optional[str] = None):

    args_hash = self.create_args_hash(task_name, task_args)

    new_task_execution = CeleryTaskExecution(
      task_name=task_name,
      celery_task_id=celery_task_id,
      status="PENDING",
      task_args=task_args,
      task_args_hash=args_hash,
      created_at=datetime.now(timezone.utc)
    )

    async with self.db_client() as connection:
      connection.add(new_task_execution)
      await connection.commit()
      await connection.refresh(new_task_execution)  # Refresh to get the updated state from the database

    return new_task_execution
  
  async def update_task_record(self, execution_id: int, status: str, result: Optional[dict] = None):
    async with self.db_client() as connection:
      task_execution = await connection.get(CeleryTaskExecution, execution_id)
      if task_execution:
        task_execution.status = status
        if result is not None:
          task_execution.result = result
        if status in ["SUCCESS", "FAILURE"]:
          task_execution.ended_at = datetime.now(timezone.utc)
        task_execution.updated_at = datetime.now(timezone.utc)
        await connection.commit()
      else:
        raise ValueError(f"Task execution with ID {execution_id} not found.")


  async def get_existing_task_record(self, task_name: str, task_args: dict, celery_task_id: str) -> Optional[CeleryTaskExecution]:
    args_hash = self.create_args_hash(task_name, task_args)

    async with self.db_client() as connection:
      existing_task_execution = await connection.execute(
        select(CeleryTaskExecution).where(
          CeleryTaskExecution.celery_task_id == celery_task_id,
          CeleryTaskExecution.task_name == task_name,
          CeleryTaskExecution.task_args_hash == args_hash
        )
      )

      return existing_task_execution.scalar_one_or_none()

  async def should_execute_task(self, task_name: str, task_args: dict, celery_task_id: str, task_time_limit: int = 600) -> tuple[bool, Optional[CeleryTaskExecution]]:
    existing_task_execution = await self.get_existing_task_record(task_name, task_args, celery_task_id)

    if not existing_task_execution:
      return True, None
  
    status = existing_task_execution.status

    # Task already completed successfully 
    if status == "SUCCESS": 
      return False, existing_task_execution
    elif status == "FAILURE":
      return True, existing_task_execution
    elif existing_task_execution.status in ["PENDING", "STARTED"]:
      # Check if the task is still within the time limit
      if existing_task_execution.started_at:
        time_elapsed = (datetime.now(timezone.utc) - existing_task_execution.started_at).total_seconds()  # type: ignore
        time_gap = 60 
        if time_elapsed < task_time_limit + time_gap:
          return False, existing_task_execution

    return True, existing_task_execution

  async def cleanup_old_task_records(self, time_retention: int = 86400):
    cutoff_time = datetime.now(timezone.utc) - timedelta(days=time_retention)

    async with self.db_client() as connection:
      await connection.execute(
        delete(CeleryTaskExecution).where(
          CeleryTaskExecution.created_at < cutoff_time
        )
      )
      await connection.commit()
