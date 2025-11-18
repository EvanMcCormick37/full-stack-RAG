from datetime import datetime
from typing import List
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb import QueryResult

from app.config import settings
from app.core import document_processing
from app.core.interfaces import (
    DocumentProcessor,
    LLMClient
)
from app.core.exceptions import (
    VectorStoreError,
)
from app.models.schemas import Source, QueryResponse, PromptStyle, DocumentListResponse, DocumentMetadata
import logging

logger = logging.getLogger(__name__)


class RAGService:
    """
    Orchestrates document processing, embedding generation, context retrieval, and LLM question-answering.
    """

    def __init__(
        self,
        llm_client: LLMClient,
    ):
        logger.info("Initializing RAG Service...")
        
        self._llm_client = llm_client
        self._embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
        self._vector_database = chromadb.PersistentClient().get_or_create_collection(
            name = settings.COLLECTION_NAME
        )

        logger.info("RAG Service Initialized.")
    

    def process_document(
        self,
        document_id: str,
        filename: str,
        file_path: str,
        upload_time: datetime
    ) -> int:
        '''
        Processes a single document

        Params:
            document_id - Document ID of document
            filename - The name of the file
            file_path - Path to file
            upload_time - The time which the file was uploaded

        Returns:
            The number of chunks the document was chunked into.
        '''
        text = document_processing.extract_text(file_path)
        chunks = document_processing.chunk_text(text)
        embeddings = self._embedding_model.encode(
            chunks,
            show_progress_bar = True,
            convert_to_numpy = True
        )
        document_metadata = {
            'document_id': document_id,
            'filename': filename,
            'upload_time': upload_time
            }
        metadatas = [document_metadata]*len(chunks)
        chunk_ids = [f"{document_id}_{i}" for i in range(len(chunks))]

        try:
            self._vector_database.add(
                documents = chunks,
                embeddings = embeddings,
                metadatas = metadatas,
                ids = chunk_ids
            )
            
            return len(chunks)
        except Exception as e:
            raise VectorStoreError(f"Failed to add document chunks to the database: {str(e)}")
    

    def query(
        self,
        question: str,
        style: PromptStyle,
        n_results: int = settings.N_SEARCH_RESULTS,
        return_context: bool = settings.RETURN_CONTEXT
    ) -> QueryResponse:
        """
        Query the RAG system for a response with context.

        Params:
            question - The user's question
            n_results - Optional number of context chunks the user wants to use as context.

        Returns:
            QueryResponse with answer, sources, and metadata
        """
        logger.info(f"Processing query: {question[:100]}...")

        embedding = self._embedding_model.encode(question).tolist()

        chromadb_queryresult = self._vector_database.query(
            query_embeddings = embedding,
            n_results = n_results
        )


        sources = self._convert_chromadb_queryresult_to_sources(chromadb_queryresult)
        answer = self._llm_client.answer(
            question,
            sources,
            style
        )

        response = QueryResponse(
            answer = answer,
            context = sources if return_context else None
        )

        return response
    

    def list_documents(self) -> DocumentListResponse:
        """
        Get a list of unique document sources in the vector store.
        
        Returns:
            DocumentList of document filenames
        """
        # Get all documents
        all_docs = self._vector_database.get()
        
        # Extract unique sources
        sources = set()
        if all_docs['metadatas']:
            for metadata in all_docs['metadatas']:
                if 'source' in metadata:
                    sources.add(metadata['source'])

        response = DocumentListResponse(
            sources=sorted(list(sources)),
            total=len(list(sources))
        )
        
        return response



    def get_document(self, document_id: str) -> DocumentMetadata | None:
        """
        Get the metadata for a single document from the vector store.

        Params:
            document_id - The ID of the document to get metadata for

        Returns:
            DocumentMetadata with the metadata for the document ID
        """
        doc = self._vector_database.get(ids=document_id)
        if doc['metadatas']:
            metadata = doc['metadatas'][0]
            response = DocumentMetadata(
                document_id = document_id,
                filename = metadata['name'],
                file_size = metadata['size'],
                upload_time = metadata['upload_time'],
                num_chunks=len(doc['metadatas'])
            )
            return response
        return None


    def delete_document(self, document_id: str) -> bool:
        '''
        Delete a document from the vector store.

        Params:
            document_id - The ID of the document to be deleted.

        Returns:
            bool representing the success of the deletion. True -> success, False -> failure
        '''
        self._vector_database.delete(
            where={"document_id": document_id}
        )
        results = self._vector_database.get(ids = document_id)

        return (len(results['ids'])==0)


    def _convert_chromadb_queryresult_to_sources(self, chromadb_queryresult: QueryResult) -> List[Source]:
        '''
        Converts a QueryResult object to List[Source]

        Params:
            chromadb_queryresult - The QueryResult object to be converted
        
        Returns:
            A list of Sources generated from the QueryResult.
        '''
        ids = chromadb_queryresult['ids'][0]
        documents = chromadb_queryresult['documents'][0]
        metadatas = chromadb_queryresult['metadatas'][0]

        sources = [
            Source(
                document_id = id,
                filename = metadata['name'],
                upload_time = metadata['upload_time'],
                chunk_text = document
            ) for (id, document, metadata) in zip(ids, documents, metadatas)]

        return sources