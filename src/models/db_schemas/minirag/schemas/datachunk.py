from .minirag_base import SQLAlchemyBase
from sqlalchemy import Column, Integer, DateTime, String, ForeignKey, func, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from pydantic import BaseModel
from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column
import uuid

class DataChunk(SQLAlchemyBase):
  __tablename__ = "chunks"

  chunk_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
  chunk_uuid: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
  chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
  chunk_metadata: Mapped[dict] = mapped_column(JSONB, nullable=True)
  chunk_order: Mapped[int] = mapped_column(Integer, nullable=False)
  chunk_project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.project_id"), nullable=False)
  chunk_asset_id: Mapped[int] = mapped_column(Integer, ForeignKey("assets.asset_id"), nullable=False)
  created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
  updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

  # Relationship with Asset
  project = relationship("Project", back_populates="chunks")
  asset = relationship("Asset", back_populates="chunks")

  # Indexes for faster queries
  __table_args__ = (
    Index('ix_chunk_project_id', 'chunk_project_id'),
    Index('ix_chunk_asset_id', 'chunk_asset_id'),
  )

class RetrievedDocument(BaseModel):
  text: str
  score: float
