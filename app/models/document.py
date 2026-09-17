import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime, Boolean, Float, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(Text, nullable=False)
    mime_type = Column(String(50))
    sha256_hash = Column(String(64))
    storage_path = Column(Text, nullable=False)
    page_count = Column(Integer, default=1)
    document_type = Column(String(50))
    status = Column(String(30), default="uploaded")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    pages = relationship("Page", back_populates="document", cascade="all, delete-orphan")
    extraction_jobs = relationship("ExtractionJob", back_populates="document", cascade="all, delete-orphan")
    extracted_fields = relationship("ExtractedField", back_populates="document", cascade="all, delete-orphan")
    line_items = relationship("LineItem", back_populates="document", cascade="all, delete-orphan")
    human_reviews = relationship("HumanReview", back_populates="document", cascade="all, delete-orphan")

class Page(Base):
    __tablename__ = "pages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    page_number = Column(Integer, nullable=False)
    image_path = Column(Text)
    width = Column(Integer)
    height = Column(Integer)

    document = relationship("Document", back_populates="pages")

class ExtractionJob(Base):
    __tablename__ = "extraction_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    status = Column(String(30), default="pending")
    model_version = Column(String(50))
    ocr_engine = Column(String(50))
    vlm_model = Column(String(50))
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    error_message = Column(Text)

    document = relationship("Document", back_populates="extraction_jobs")

class ExtractedField(Base):
    __tablename__ = "extracted_fields"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    job_id = Column(UUID(as_uuid=True), ForeignKey("extraction_jobs.id"))
    field_name = Column(String(100), nullable=False)
    raw_value = Column(Text)
    normalized_value = Column(Text)
    confidence = Column(Float, default=0.0)
    source = Column(String(50))
    page_number = Column(Integer)
    bbox = Column(JSON)
    validation_status = Column(String(30))
    requires_review = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="extracted_fields")

class LineItem(Base):
    __tablename__ = "line_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    description = Column(Text)
    quantity = Column(Float)
    unit_price = Column(Float)
    amount = Column(Float)
    confidence = Column(Float, default=0.0)
    page_number = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="line_items")

class HumanReview(Base):
    __tablename__ = "human_reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    field_name = Column(String(100), nullable=False)
    original_value = Column(Text)
    corrected_value = Column(Text)
    reviewer_name = Column(String(100))
    review_status = Column(String(30), default="pending")
    comments = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="human_reviews")