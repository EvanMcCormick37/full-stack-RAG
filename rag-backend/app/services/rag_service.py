from datetime import datetime
from typing import List, Optional
import asyncio
from functools import partial

from sentence_transformers import SentenceTransformer
import chromadb
from chromadb import QueryResult

from app.config import settings
from app.services import document_processing_service
from app.core.exceptions import VectorStoreError
from app.core.interfaces import LLMClient, MetadataService
from app.models.schemas import Source, QueryResponse, DocumentMetadata
import logging

logger = logging.getLogger(__name__)


class RAGService:
    """
    Orchestrates document processing, embedding generation, context retrieval, and LLM question-answering.
    
    Architecture:
        - ChromaDB: Stores embeddings + chunk text + document_id reference
        - MetadataService: Stores document metadata (filename, timestamps, etc.)
        - LLMClient: API Calls to Gemini-2.0-flash answering LLM
    """

    def __init__(self, llm_client: LLMClient, metadata_service: MetadataService):
        logger.info("Initializing RAG Service...")

        self._embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
        self._client = chromadb.PersistentClient(
            path = settings.CHROMADB_PERSIST_DIR
        )
        self._vector_database = self._client.get_or_create_collection(
            name = settings.COLLECTION_NAME
        )
        self._chroma_lock = asyncio.Lock()
        self._llm_client = llm_client
        self._metadata_service = metadata_service

        logger.info("RAG Service Initialized.")
    

    async def process_document(
        self,
        document_id: str,
        filename: str,
        file_path: str,
        upload_time: datetime,
        session_id: str
    ) -> None:
        '''
        Processes a single document. Stores chunks, embeddings in ChromaDB, document metadata in SQLite.

        Params:
            - document_id - Document ID of document
            - filename - The name of the document file
            - file_path - Path to document file
            - upload_time - The time which the document was uploaded
            - session_id - The session in which the document was uploaded, useful for determining user access and deletion privileges
        '''
        text = await asyncio.to_thread(document_processing_service.extract_text, file_path)
        chunks = await asyncio.to_thread(document_processing_service.chunk_text, text)
        embeddings = await asyncio.to_thread(
            partial(
                self._embedding_model.encode,
                chunks,
                show_progress_bar=False,
                convert_to_numpy=True
            )
        )
        chunk_metadatas = [{"document_id": document_id}] * len(chunks)
        chunk_ids = [f"{document_id}_{i}" for i in range(len(chunks))]

        try:
            async with self._chroma_lock:
                await asyncio.to_thread(
                    self._vector_database.add,
                    documents = chunks,
                    embeddings = embeddings,
                    metadatas = chunk_metadatas,
                    ids = chunk_ids
                )
            
            await self._metadata_service.create_document(
                document_id=document_id,
                filename=filename,
                upload_time=upload_time,
                session_id=session_id,
                num_chunks=len(chunks)
            )
            
            await self.maybe_auto_delete()

        except Exception as e:
            raise VectorStoreError(f"Failed to add document to one of the databases (SQLite document-metadata or ChromaDB chunk storage): {str(e)}")
    

    async def query(self, question: str) -> QueryResponse:
        """
        Query the RAG system for a response with context.

        Params:
            - question - The user's question
            - n_results - Optional number of context chunks the user wants to use as context.

        Returns:
            - QueryResponse with answer, sources, and metadata
        """
        logger.info(f"Processing query: {question}...")

        embedding = await asyncio.to_thread(
            self._embedding_model.encode,
            question
        )

        async with self._chroma_lock:
            chromadb_queryresult = await asyncio.to_thread(
                self._vector_database.query,
                query_embeddings = embedding,
                n_results = settings.N_SEARCH_RESULTS
            )

        sources = await self._convert_chromadb_queryresult_to_sources(chromadb_queryresult)
        documents = await self._update_access_times(sources)

        answer = self._llm_client.answer(question, sources)

        return QueryResponse(
            answer = answer,
            sources = sources,
            document_metadatas = documents
        )
    

    async def delete_document(
        self,
        document_id: str,
        session_id: Optional[str] = None
    ) -> None:
        '''
        Delete a document from the vector store.

        Params:
            - document_id - The ID of the document to be deleted.
            - session_id = The ID of the session attempting to delete the document. Sessions can only delete the documents they add.
        '''
        doc = await self._metadata_service.get_document(document_id)

        if doc is None:
            raise VectorStoreError(f"Document {document_id} not found")
        
        if session_id and doc.session_id != session_id:
            raise VectorStoreError(
                f"You don't have permission to delete document {document_id}"
            )
        
        async with self._chroma_lock:
            await asyncio.to_thread(
                self._vector_database.delete,
                where={"document_id": document_id}
            )
        
        await self._metadata_service.delete_document(document_id)
    

    async def delete_all_documents(self, session_id: Optional[str]) -> None:
        '''
        Delete all documents from the vector store. (Filtered on session-id if called by an individual session)
        
        Params:
            - session_id - The session-ID trying to delete all documents.
        Returns:
            bool representing the success of deletion.
        '''
        if session_id is None:
            async with self._chroma_lock:
                await asyncio.to_thread(
                    self._client.delete_collection,
                    settings.COLLECTION_NAME
                )
                self._vector_database = await asyncio.to_thread(
                    self._client.get_or_create_collection,
                    settings.COLLECTION_NAME
                )
            await self._metadata_service.delete_all_documents()
        else:
            docs = await self._metadata_service.get_documents_by_session(session_id)
            for doc in docs:
                async with self._chroma_lock:
                    await asyncio.to_thread(
                        self._vector_database.delete,
                        where={"document_id": doc.document_id}
                    )
                await self._metadata_service.delete_document(doc.document_id)


    async def _convert_chromadb_queryresult_to_sources(self, result: QueryResult) -> List[Source]:
        '''
        Converts a QueryResult object to List[Source]

        Params:
            - result - The QueryResult object to be converted
        
        Returns:
            A list of Sources generated from the QueryResult.
        '''
        if not result['ids'] or not result['ids'][0]:
            return []
        
        chunk_ids = result['ids'][0]
        chunk_texts = result['documents'][0]
        document_ids = [metadata['document_id'] for metadata in result['metadatas'][0]]

        sources = []
        for chunk_id, chunk_text, document_id in zip(chunk_ids, chunk_texts, document_ids):
            doc = await self._metadata_service.get_document(document_id)

            if doc:
                sources.append(
                    Source(
                        chunk_id=chunk_id,
                        chunk_text = chunk_text,
                        document_id = document_id
                ))

        return sources
    

    async def _update_access_times(self, sources: List[Source]) -> List[DocumentMetadata]:
        """
        Update last_accessed timestamps for all retrieved sources, in document-records SQLite db, and get DocumentMetadatas for retrieved sources.

        ### Params:
            - sources: List[Source] - The Sources retrieved from ChromaDB. Update last_accessed timestamp on all associated document records.
        
        ### Returns:
            - List[DocumentMetadata] - The DocumentMetadatas for the given list of sources.
        """
        seen_doc_ids = set()
        seen_doc_metadatas = []
        for source in sources:
            if source.document_id not in seen_doc_ids:
                await self._metadata_service.update_last_accessed(source.document_id)
                seen_doc_ids.add(source.document_id)
                doc = await self._metadata_service.get_document(source.document_id)
                seen_doc_metadatas.append(doc)
        return seen_doc_metadatas    
    

    async def maybe_auto_delete(self) -> None:
        """Delete least accessed documents if storage exceeds maximum storage threshold"""
        async with self._chroma_lock:
            count = await asyncio.to_thread(self._vector_database.count)
            
        while count > settings.MAX_CHUNKS:
            stale_doc = await self._metadata_service.get_most_stale_document()
            if stale_doc:
                await self.delete_document(stale_doc.document_id)
                
            async with self._chroma_lock:
                count = await asyncio.to_thread(self._vector_database.count)
    

    async def is_owner(self, document_id: str, session_id: str) -> bool:
        """
        Check if a session owns a document (i.e. that document was created within that session).
        
        ### Params:
            - document_id: str - The document ID
            - session_id: str - The session ID
        
        ### Returns:
            Boolean determining whether the session owns the document.
        """
        record = await self._metadata_service.get_document(document_id)
        return (record is not None and record.session_id == session_id)