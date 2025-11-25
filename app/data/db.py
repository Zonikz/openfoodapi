"""Database connection and initialization"""
from sqlmodel import SQLModel, create_engine, Session
from typing import Generator
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# Create engine
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    connect_args={"check_same_thread": False}  # SQLite specific
)


def init_db() -> None:
    """Initialize database tables"""
    try:
        SQLModel.metadata.create_all(engine)
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ Database init failed: {e}")
        raise


def get_db() -> Generator[Session, None, None]:
    """Get database session"""
    with Session(engine) as session:
        yield session
