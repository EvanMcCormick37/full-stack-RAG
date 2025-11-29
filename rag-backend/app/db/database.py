"""
Database connection and session management
"""
from sqlmodel import SQLModel, Session, create_engine
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Create SQLite database file alongside ChromaDB
engine = create_engine(
    f"sqlite:///{settings.METADATA_DB_PATH}",
    echo=False,
    connect_args={"check_same_thread": False}
)

def init_db():
    """Create all tables if they don't exist."""
    SQLModel.metadata.create_all(engine)
    logger.info(f"Metadata database initialized at {settings.METADATA_DB_PATH}")

def get_session():
    """Yield a database session."""
    with Session(engine) as session:
        yield session