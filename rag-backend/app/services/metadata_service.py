"""
Service layer for document metadata CRUD operations.
Provides a clean interface between the RAG-service layer and the database.
"""
from datetime import datetime
from typing import Optional, List
from sqlmodel import Session, select
from app.db.models import DocumentRecord
from app.db.database import engine
import logging

logger = logging.getLogger(__name__)


class MetadataService:
    """
    Handles all document metadata (document record) persistence operations
    """
    def create_document(
        self,
        document_id: str,
        filename: str,
        upload_time: datetime,
        session_id: str,
        num_chunks: int,
        status: str="completed"
    ) -> DocumentRecord:
        """Create a new document record"""
        with Session(engine) as session:
            record = DocumentRecord(
                document_id=document_id,
                filename=filename,
                upload_time=upload_time,
                last_accessed=None,
                session_id=session_id,
                num_chunks=num_chunks,
                status=status
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            logger.info(f"Created document record for document {document_id} ({filename})")
            return record
    

    def get_document(self, document_id: str) -> Optional[DocumentRecord]:
        """Retrieve a document by ID."""
        with Session(engine) as session:
            return session.get(DocumentRecord, document_id)
    

    def get_all_documents(self) -> List[DocumentRecord]:
        """Retrieve all document records from the database."""
        with Session(engine) as session:
            statement = select(DocumentRecord).order_by(DocumentRecord.upload_time.desc())
            return session.exec(statement).all()
    

    def get_documents_by_session(self, session_id: str) -> List[DocumentRecord]:
        """Retrieve all document records uploaded by a specific Session ID."""
        with Session(engine) as session:
            statement = select(DocumentRecord).where(
                DocumentRecord.session_id == session_id
            )
            return session.exec(statement).all()
    

    def update_last_accessed(self, document_id: str) -> bool:
        """Update the last_accessed timestamp of a document."""
        with Session(engine) as session:
            record = session.get(DocumentRecord, document_id)
            if record:
                record.last_accessed = datetime.now()
                session.add(record)
                session.commit()
                return True
            return False
        
    
    def update_status(self, document_id: str, status: str) -> bool:
        """Update the processing status of a document, in its document record."""
        with Session(engine) as session:
            record = session.get(DocumentRecord, document_id)
            if record:
                record.status = status
                session.add(record)
                session.commit()
                return True
            return False
        
    
    def delete_document(self, document_id: str) -> bool:
        """Delete a document record from the database."""
        with Session(engine) as session:
            record = session.get(DocumentRecord, document_id)
            if record:
                session.delete(record)
                session.commit()
                return True
            return False
    

    def delete_all_documents(self) -> bool:
        """Delete all documents from the database."""
        with Session(engine) as session:
            statement = select(DocumentRecord)
            records = session.exec(statement).all()
            for record in records:
                session.delete(record)
            session.commit()
            return True
        

    def get_most_stale_document(self) -> Optional[DocumentRecord]:
        """Get the document which was accessed longest ago (or not at all). Used for LRU-style auto-deletion."""
        with Session(engine) as session:
            statement = select(DocumentRecord).order_by(
                DocumentRecord.last_accessed.is_(None).desc(),
                DocumentRecord.last_accessed.asc()
            ).limit(1)
            return session.exec(statement).first()
        
    
    def count_documents(self) -> int:
        """Get the total number of documents in the database."""
        with Session(engine) as session:
            statement = select(DocumentRecord)
            return len(session.exec(statement).all())
        

# Export singleton instance
metadata_service = MetadataService()