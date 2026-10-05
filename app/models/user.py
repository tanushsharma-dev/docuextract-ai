import uuid
import logging
from datetime import datetime

from sqlalchemy import Column, String, DateTime

# Sahi import path — app.core.database me engine aur Base hai
from app.core.database import Base, engine

logger = logging.getLogger(__name__)


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# Users table create karo (agar nahi hai)
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Users table ready")
except Exception as e:
    logger.warning(f"Table creation note: {e}")