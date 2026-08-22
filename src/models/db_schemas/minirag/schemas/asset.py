from .minirag_base import SQLAlchemyBase
from sqlalchemy import Column, Integer, DateTime, String, ForeignKey, func, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped, mapped_column
import uuid

class Asset(SQLAlchemyBase):
  __tablename__ = "assets"

  asset_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
  asset_uuid: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
  asset_type: Mapped[str] = mapped_column(String(50), nullable=False)
  asset_name: Mapped[str] = mapped_column(String(100), nullable=False)
  asset_size: Mapped[int] = mapped_column(Integer, nullable=False)
  asset_config: Mapped[dict] = mapped_column(JSONB, nullable=True)
  asset_project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.project_id"), nullable=False)
  created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
  updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

  # Relationship with Project
  project = relationship("Project", back_populates="assets")
  chunks = relationship("DataChunk", back_populates="asset", cascade="all, delete-orphan")

  # Indexes for faster queries
  __table_args__ = (
    Index('ix_asset_project_id', 'asset_project_id'),
  )
