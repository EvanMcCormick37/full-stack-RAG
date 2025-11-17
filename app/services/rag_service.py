from typing import List, Dict, Optional, Any
import asyncio
import time
from sentence_transformers import SentenceTransformer
import chromadb
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
from app.config import settings
from app.core.interfaces import (
    DocumentProcessor,
    LLMClient
)
from app.core.config import RAGConfig
from app.core.exceptions import (
    DocumentProcessingError,
    EmbeddingGenerationError,
    VectorStoreError,
    LLMError
)
from app.models.schemas import Source, QueryResponse, PromptStyle
import logging

logger = logging.getLogger(__name__)


class RAGService:
    """
    Orchestrates document processing, embedding generation, context retrieval, and LLM question-answering.
    """

    def __init__(
        self,
        document_processor: DocumentProcessor,
        llm_client: LLMClient,
    ):
        logger.info("Initializing RAG Service...")
        
        self._document_processor = document_processor
        self._llm_client = llm_client
        self._embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
        self._vector_database = chromadb.PersistentClient().get_or_create_collection(
            name = settings.COLLECTION_NAME
        )

        logger.info("RAG Service Initialized.")
    

    def process_document(
        self,
        file_path: str,
        document_id: str,
        document_metadata: Dict[str, Any]
    ) -> int:
        '''
        Params:
        file_path - Path to file to be processed
        document_id - Document ID of document to be processed

        Processes a single document

        Returns:
        DocumentParameters for the successfully processed document.
        '''
        text = self._document_processor.extract_text(file_path)
        
        chunks = self._document_processor.chunk_text(text)
        embeddings = self._embedding_model.encode(
            chunks,
            show_progress_bar = True,
            convert_to_numpy = True
        )
        metadatas = [document_metadata*len(chunks)]
        chunk_ids = [f"{document_id}_{i}" for i in range(len(chunks))]

        try:
            self._vector_database.add(
                documents = chunks,
                embeddings = embeddings,
                metadatas = metadatas,
                ids = chunk_ids
            )
        except Exception as e:
            raise VectorStoreError("Failed to add document chunks to the database: {e}")
        
        return len(chunks)
    

    def query(
        self,
        question: str,
        style: PromptStyle,
        n_results: int = settings.N_SEARCH_RESULTS
    ):
        """
        Query the RAG system for a response with context.

        Params:
            question - The user's question
            n_results - Optional number of context chunks the user wants to use as context.

        Returns:
            QueryResponse with answer, sources, and metadata
        Raises:
            LLMError if answer generation fails
            EmbeddingGenerationError: If query embedding fails
            VectorStoreError: If search fails
        """
        logger.info(f"Processing query: {question[:100]}...")

        embedding = self._embedding_model.encode(question).tolist()

        context = self._vector_database.query(
            query_embeddings=embedding,
            n_results=n_results
        )

        context_docs = context['documents'][0]
        answer = self._llm_client.answer(
            question,
            context_docs,
            style
        )

        return answer