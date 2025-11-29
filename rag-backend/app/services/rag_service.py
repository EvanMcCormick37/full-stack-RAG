from datetime import datetime
from typing import List, Optional
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb import QueryResult

from app.config import settings
from app.services import document_service, metadata_service
from app.core.interfaces import LLMClient
from app.core.exceptions import VectorStoreError
from app.models.schemas import Source, QueryResponse, DocumentListResponse, DocumentMetadata
import logging

logger = logging.getLogger(__name__)


class RAGService:
    """
    Orchestrates document processing, embedding generation, context retrieval, and LLM question-answering.
    
    Architecture:
        - ChromaDB: Stores embeddings + chunk text + document_id reference
        - MetadataService: Stores document metadata (filename, timestamps, etc.)
    """

    def __init__(
        self,
        llm_client: LLMClient,
    ):
        logger.info("Initializing RAG Service...")
        
        self._llm_client = llm_client
        self._embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
        self._client = chromadb.PersistentClient(
            path = settings.CHROMADB_PERSIST_DIR
        )
        self._vector_database = self._client.get_or_create_collection(
            name = settings.COLLECTION_NAME
        )

        logger.info("RAG Service Initialized.")
    

    def process_document(
        self,
        document_id: str,
        filename: str,
        file_path: str,
        upload_time: datetime,
        session_id: str
    ) -> int:
        '''
        Processes a single document. Stores chunks, embeddings in ChromaDB, document metadata in SQLite.

        Params:
            - document_id - Document ID of document
            - filename - The name of the document file
            - file_path - Path to document file
            - upload_time - The time which the document was uploaded
            - session_id - The session in which the document was uploaded, useful for determining user access and deletion privileges

        Returns:
            The number of chunks the document was chunked into.
        '''
        text = document_service.extract_text(file_path)
        chunks = document_service.chunk_text(text)
        embeddings = self._embedding_model.encode(
            chunks,
            show_progress_bar = True,
            convert_to_numpy = True
        )
        chunk_metadatas = [{"document_id": document_id}] * len(chunks)
        chunk_ids = [f"{document_id}_{i}" for i in range(len(chunks))]

        try:
            self._vector_database.add(
                documents = chunks,
                embeddings = embeddings,
                metadatas = chunk_metadatas,
                ids = chunk_ids
            )
            
            metadata_service.create_document(
                document_id=document_id,
                filename=filename,
                upload_time=upload_time,
                session_id=session_id,
                num_chunks=len(chunks),
                status="processing"
            )
            # Check for possible auto-deletion of old documents if ChromaDB has grown too large
            self.maybe_auto_delete()

            return len(chunks)
        except Exception as e:
            raise VectorStoreError(f"Failed to add document chunks to the database: {str(e)}")
    

    def query(
        self,
        question: str
    ) -> QueryResponse:
        """
        Query the RAG system for a response with context.

        Params:
            - question - The user's question
            - n_results - Optional number of context chunks the user wants to use as context.

        Returns:
            - QueryResponse with answer, sources, and metadata
        """
        logger.info(f"Processing query: {question}...")

        embedding = self._embedding_model.encode(question)
        chromadb_queryresult = self._vector_database.query(
            query_embeddings = embedding,
            n_results = settings.N_SEARCH_RESULTS
        )

        sources = self._convert_chromadb_queryresult_to_sources(chromadb_queryresult)
        self.update_access_times(sources)

        answer = self._llm_client.answer(
            question,
            sources
        )

        return QueryResponse(
            answer = answer,
            context = sources
        )
    

    def list_documents(self) -> DocumentListResponse:
        """
        Get a list of unique document sources in the vector store.
        
        Returns:
            DocumentList of document filenames
        """
        # Get all document records
        records = metadata_service.get_all_documents()

        if not records or len(records) == 0:
            return DocumentListResponse(
                documents = None,
                count = 0
            )
        
        # Get DocumentMetadata for each document record
        document_metadatas = [
            DocumentMetadata(
                document_id=r.document_id,
                filename=r.filename,
                upload_time=r.upload_time,
                last_accessed=r.last_accessed,
                session_id=r.session_id,
                num_chunks=r.num_chunks
            ) for r in records
        ]

        return DocumentListResponse(
            documents = document_metadatas,
            count = len(document_metadatas)
        )


    def get_document(self, document_id: str) -> DocumentMetadata | None:
        """
        Get the metadata for a single document from the vector store.

        Params:
            - document_id - The ID of the document to get metadata for

        Returns:
            DocumentMetadata with the metadata for the document ID
        """
        record = metadata_service.get_document(document_id)
        if record:
            return DocumentMetadata(
                document_id=record.document_id,
                filename=record.filename,
                upload_time=record.upload_time,
                last_accessed=record.last_accessed,
                session_id=record.session_id,
                num_chunks=record.num_chunks
            )
        return None


    def delete_document(self, document_id: str) -> None:
        '''
        Delete a document from the vector store.

        Params:
            - document_id - The ID of the document to be deleted.
        '''
        self._vector_database.delete(where={"document_id": document_id})
        metadata_service.delete_document(document_id)
    

    def delete_all_documents(self) -> None:
        '''
        Delete all documents from the vector store.
        
        Returns:
            bool representing the success of deletion.
        '''
        self._client.delete_collection(settings.COLLECTION_NAME)
        self._vector_database = self._client.get_or_create_collection(settings.COLLECTION_NAME)
        metadata_service.delete_all_documents()


    def _convert_chromadb_queryresult_to_sources(self, chromadb_queryresult: QueryResult) -> List[Source]:
        '''
        Converts a QueryResult object to List[Source]

        Params:
            chromadb_queryresult - The QueryResult object to be converted
        
        Returns:
            A list of Sources generated from the QueryResult.
        '''
        chunk_texts = chromadb_queryresult['documents'][0]
        document_ids = [metadata['document_id'] for metadata in chromadb_queryresult['metadatas'][0]]

        sources = []
        for chunk_text, document_id in zip(chunk_texts, document_ids):
            doc_record = metadata_service.get_document(document_id)

            if doc_record:
                sources.append(
                    Source(
                        document_id = document_id,
                        filename = doc_record.filename,
                        upload_time = doc_record.upload_time,
                        chunk_text = chunk_text
                    ))

        return sources
    

    def update_access_times(self, sources: List[Source]) -> None:
        """
        Update last_accessed timestamps for all retrieved documents, in document-records SQLite db.

        ### Params:
            - sources: List[Source] - The Sources retrieved from ChromaDB. Update last_accessed timestamp on all associated document records.
        """
        seen_doc_ids = Set()
        for source in sources:
            if source.document_id not in seen_doc_ids:
                metadata_service.update_last_accessed(source.document_id)
                seen_doc_ids.add(source.document_id)
    

    def maybe_auto_delete(self) -> None:
        """Delete least accessed documents if storage exceeds maximum storage threshold"""
        while self._vector_database.count() > settings.MAX_VECTOR_CHUNKS:
            stale_doc = metadata_service.get_most_stale_document()
            self.delete_document(stale_doc.document_id)
    

    def is_owner(self, document_id: str, session_id: str) -> bool:
        """
        Check if a session owns a document (i.e. that document was created within that session).
        
        ### Params:
            - document_id: str - The document ID
            - session_id: str - The session ID
        
        ### Returns:
            Boolean determining whether the session owns the document.
        """
        record = metadata_service.get_document(document_id)
        return (record is not None and record.session_id == session_id)