"""
Async Metadata Service

Handles document metadata CRUD operations with async wrappers around SQLModel.
Uses asyncio.to_thread() since SQLModel's async support is still maturing.
"""
from datetime import datetime
from typing import Optional, List
import asyncio

from sqlmodel import Session, select

from app.models.schemas import DocumentMetadata, DocumentListResponse
from app.db.models import DocumentRecord
from app.db.database import engine
import logging

logger = logging.getLogger(__name__)


class MetadataService:
    """
    Async wrapper for document metadata operations.
    
    Strategy: Uses asyncio.to_thread() to run blocking SQLModel operations
    in a thread pool, preventing event loop blocking while maintaining
    SQLModel's synchronous session management.
    """

    async def create_document(
        self,
        document_id: str,
        filename: str,
        upload_time: datetime,
        session_id: str,
        num_chunks: int,
        status: str = "completed"
    ) -> DocumentMetadata:
        """Create a new document record."""
        return await asyncio.to_thread(
            self._create_document_sync,
            document_id,
            filename,
            upload_time,
            session_id,
            num_chunks,
            status
        )

    def _create_document_sync(
        self,
        document_id: str,
        filename: str,
        upload_time: datetime,
        session_id: str,
        num_chunks: int,
        status: str
    ) -> DocumentMetadata:
        """Synchronous implementation of create_document."""
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
            logger.info(f"Created document record: {document_id} ({filename})")
            return self._to_metadata(record)

    async def get_document(
        self, 
        document_id: str
    ) -> Optional[DocumentMetadata]:
        """Retrieve a document by ID."""
        return await asyncio.to_thread(
            self._get_document_sync, 
            document_id
        )

    def _get_document_sync(
        self, 
        document_id: str
    ) -> Optional[DocumentMetadata]:
        """Synchronous implementation of get_document."""
        with Session(engine) as session:
            record = session.get(DocumentRecord, document_id)
            return self._to_metadata(record)

    async def get_all_documents(
        self, 
        session_id: Optional[str] = None
    ) -> List[DocumentMetadata]:
        """Retrieve all document records, optionally filtered by session."""
        return await asyncio.to_thread(
            self._get_all_documents_sync, 
            session_id
        )

    def _get_all_documents_sync(
        self, 
        session_id: Optional[str] = None
    ) -> List[DocumentMetadata]:
        """Synchronous implementation of get_all_documents."""
        with Session(engine) as session:
            statement = select(DocumentRecord).order_by(
                DocumentRecord.upload_time.desc()
            )
            records = session.exec(statement).all()
            docs = [self._to_metadata(r) for r in records]
            
            if session_id is None:
                return docs
            return [d for d in docs if d.session_id == session_id]

    async def get_documents_by_session(
        self, 
        session_id: str
    ) -> List[DocumentMetadata]:
        """Retrieve all documents for a specific session."""
        return await asyncio.to_thread(
            self._get_documents_by_session_sync, 
            session_id
        )

    def _get_documents_by_session_sync(
        self, 
        session_id: str
    ) -> List[DocumentMetadata]:
        """Synchronous implementation."""
        with Session(engine) as session:
            statement = select(DocumentRecord).where(
                DocumentRecord.session_id == session_id
            )
            return [
                self._to_metadata(r) 
                for r in session.exec(statement).all()
            ]

    async def update_last_accessed(
        self, 
        document_id: str
    ) -> bool:
        """Update the last_accessed timestamp."""
        return await asyncio.to_thread(
            self._update_last_accessed_sync, 
            document_id
        )

    def _update_last_accessed_sync(
        self, 
        document_id: str
    ) -> bool:
        """Synchronous implementation."""
        with Session(engine) as session:
            record = session.get(DocumentRecord, document_id)
            if record:
                record.last_accessed = datetime.now()
                session.add(record)
                session.commit()
                return True
            return False

    async def update_status(
        self, 
        document_id: str, 
        status: str
    ) -> bool:
        """Update the processing status of a document."""
        return await asyncio.to_thread(
            self._update_status_sync, 
            document_id, 
            status
        )

    def _update_status_sync(
        self, 
        document_id: str, 
        status: str
    ) -> bool:
        """Synchronous implementation."""
        with Session(engine) as session:
            record = session.get(DocumentRecord, document_id)
            if record:
                record.status = status
                session.add(record)
                session.commit()
                return True
            return False

    async def delete_document(self, document_id: str) -> None:
        """Delete a document record."""
        await asyncio.to_thread(
            self._delete_document_sync, 
            document_id
        )

    def _delete_document_sync(self, document_id: str) -> None:
        """Synchronous implementation."""
        with Session(engine) as session:
            record = session.get(DocumentRecord, document_id)
            if record:
                session.delete(record)
                session.commit()
                logger.info(f"Deleted document record: {document_id}")

    async def delete_all_documents(self) -> None:
        """Delete all document records."""
        await asyncio.to_thread(self._delete_all_documents_sync)

    def _delete_all_documents_sync(self) -> None:
        """Synchronous implementation."""
        with Session(engine) as session:
            statement = select(DocumentRecord)
            records = session.exec(statement).all()
            for record in records:
                session.delete(record)
            session.commit()
            logger.info(f"Deleted all {len(records)} document records")

    async def get_most_stale_document(self) -> Optional[DocumentMetadata]:
        """Get the document accessed longest ago (for LRU auto-deletion)."""
        return await asyncio.to_thread(
            self._get_most_stale_document_sync
        )

    def _get_most_stale_document_sync(self) -> Optional[DocumentMetadata]:
        """Synchronous implementation."""
        with Session(engine) as session:
            statement = select(DocumentRecord).order_by(
                DocumentRecord.last_accessed.is_(None).desc(),
                DocumentRecord.last_accessed.asc()
            ).limit(1)
            record = session.exec(statement).first()
            return self._to_metadata(record)

    async def count_documents(self) -> int:
        """Get the total number of documents."""
        return await asyncio.to_thread(self._count_documents_sync)

    def _count_documents_sync(self) -> int:
        """Synchronous implementation."""
        with Session(engine) as session:
            statement = select(DocumentRecord)
            return len(session.exec(statement).all())

    async def list_documents(
        self, 
        session_id: Optional[str] = None
    ) -> DocumentListResponse:
        """Get a list of documents with count."""
        docs = await self.get_all_documents(session_id)
        count = len(docs)
        return DocumentListResponse(
            documents=docs if count > 0 else None,
            count=count
        )

    @staticmethod
    def _to_metadata(
        record: Optional[DocumentRecord] = None
    ) -> Optional[DocumentMetadata]:
        """Convert DocumentRecord to DocumentMetadata."""
        if record is None:
            return None
        return DocumentMetadata(
            document_id=record.document_id,
            filename=record.filename,
            upload_time=record.upload_time,
            last_accessed=record.last_accessed,
            session_id=record.session_id,
            num_chunks=record.num_chunks,
            status=record.status
        )