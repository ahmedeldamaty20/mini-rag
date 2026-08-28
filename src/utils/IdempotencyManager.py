import hashlib
import json
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select
from src.models.db_schemas.minirag.schemas.celery_task_execution import CeleryTaskExecution

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

  def create_task_record(self, task_name: str, task_args: dict, celery_task_id: Optional[str] = None):

    args_hash = self.create_args_hash(task_name, task_args)

    new_task_execution = CeleryTaskExecution(
      task_name=task_name,
      celery_task_id=celery_task_id,
      status="PENDING",
      task_args=task_args,
      task_args_hash=args_hash,
      created_at=datetime.now(timezone.utc)
    )

    with self.db_client.session() as connection:
      connection.add(new_task_execution)
      connection.commit()
      connection.refresh(new_task_execution)  # Refresh to get the updated state from the database

    return new_task_execution
  
  def update_task_record(self, execution_id: int, status: str, result: Optional[dict] = None):
    with self.db_client.session() as connection:
      task_execution = connection.get(CeleryTaskExecution, execution_id)
      if task_execution:
        task_execution.status = status
        if result is not None:
          task_execution.result = result
        if status in ["SUCCESS", "FAILURE"]:
          task_execution.ended_at = datetime.now(timezone.utc)
        task_execution.updated_at = datetime.now(timezone.utc)
        connection.commit()
      else:
        raise ValueError(f"Task execution with ID {execution_id} not found.")

  def get_existing_task_record(self, task_name: str, task_args: dict) -> Optional[CeleryTaskExecution]:
    args_hash = self.create_args_hash(task_name, task_args)

    with self.db_client.session() as connection:
      existing_task_execution = connection.execute(
        select(CeleryTaskExecution).where(
          CeleryTaskExecution.task_name == task_name,
          CeleryTaskExecution.task_args_hash == args_hash
        )
      ).scalar_one_or_none()

    return existing_task_execution

  def should_execute_task(self, task_name: str, task_args: dict, task_time_limit: int = 600) -> tuple[bool, Optional[CeleryTaskExecution]]:
    existing_task_execution = self.get_existing_task_record(task_name, task_args)

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

