from .minirag_base import SQLAlchemyBase
from sqlalchemy import Column, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

class Project(SQLAlchemyBase):
  __tablename__ = "projects"

  project_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
  project_uuid: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
  created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
  updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

  # Relationship with Asset and DataChunk
  assets = relationship("Asset", back_populates="project", cascade="all, delete-orphan")
  chunks = relationship("DataChunk", back_populates="project", cascade="all, delete-orphan")
