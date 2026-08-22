from .minirag_base import SQLAlchemyBase
from sqlalchemy import Column, Integer, DateTime, String, ForeignKey, func, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

class Asset(SQLAlchemyBase):
  __tablename__ = "assets"

  asset_id = Column(Integer, primary_key=True, autoincrement=True)
  asset_uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4())
  asset_type = Column(String(50), nullable=False)
  asset_name = Column(String(100), nullable=False)
  asset_size = Column(Integer, nullable=False)
  asset_config = Column(JSONB, nullable=True)
  asset_project_id = Column(Integer, ForeignKey("projects.project_id"), nullable=False)
  created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
  updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=False)

  # Relationship with Project
  project = relationship("Project", back_populates="assets")

  # Indexes for faster queries
  __table_args__ = (
    Index('ix_asset_project_id', 'asset_project_id'),
  )
