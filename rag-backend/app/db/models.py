'''
SQL model definitions for persistent document-metadata storage.
'''
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class DocumentRecord(SQLModel, table=True):
    """
    Persistent storage for document metadata.
    Linked to ChromaDB chunks via document_id.
    """
    __tablename__= "documents"

    document_id: str = Field(primary_key=True, index=True)
    filename: str
    upload_time: datetime
    last_accessed: Optional[datetime] = None
    session_id: str = Field(index=True)
    num_chunks: int
    status: str = Field(default="completed")