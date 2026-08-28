from .minirag_base import SQLAlchemyBase
from sqlalchemy import Integer, DateTime, String, func, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
import uuid

class CeleryTaskExecution(SQLAlchemyBase):
  __tablename__ = "celery_task_executions"

  execution_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
  task_name: Mapped[str] = mapped_column(String(250), nullable=False)
  celery_task_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=True)
  status: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDING")
  task_args: Mapped[dict] = mapped_column(JSONB, nullable=True)
  task_args_hash: Mapped[str] = mapped_column(String(64), nullable=False) # SHA256 hash of the task_args
  result: Mapped[dict] = mapped_column(JSONB, nullable=True)
  created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=True)
  updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
  started_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
  ended_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)

  __table_args__ = (
    Index('ix_task_name_celery_task_id', task_name, task_args_hash, celery_task_id, unique=True),
    Index('ix_task_execution_status', status),
    Index('ix_task_execution_created_at', created_at),
    Index('ix_celery_task_id', celery_task_id),
  )
