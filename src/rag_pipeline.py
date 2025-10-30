import logging
import os
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
from sentence_transformers import SentenceTransformer
import chromadb
from dotenv import load_dotenv
from src.document_processor import DocumentProcessor
from src.llm_client import LLMClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGPipeline:
    def __init__(
            self,
            chunk_size: Optional[int] = None,
            overlap_size: Optional[int] = None,
            embedding_model: Optional[str] = None,
            collection_name: str = "documents",
            persist_directory: Optional[str] = None,
    ):
        """
        Initialize the RAG Pipeline

        Args:
            processor: Document processor instance (created if not provided).
            vector_store Vector store instance (created if not provided).
            chunk_size: Size of document chunks (uses .env if not provided).
            overlap_size: Overlap size between chunks (uses .env if not provided).
            embedding_model: Embedding model name (uses .env if not provided).
            collection_name: Name for the vector store collection.
            persist_directory: Directory to persist vector store data (uses .env if not provided).
        """

        load_dotenv()

        logger.info("Initializing RAG Pipeline...")

        self._embedding_model_name = embedding_model if embedding_model else os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        self._chunk_size = chunk_size if chunk_size else int(os.getenv("CHUNK_SIZE", 500))
        self._overlap_size = overlap_size if overlap_size else int(os.getenv("OVERLAP_SIZE", 50))
        self._persist_directory = persist_directory if persist_directory else os.getenv("VECTOR_STORE", None)
        self._collection_name = collection_name

        self._document_processor = DocumentProcessor(
                chunk_size = self._chunk_size,
                overlap_size = self._overlap_size,
                embedding_model = self._embedding_model_name
            )
        
        self._llm_client = LLMClient(
            api_key=os.getenv("GEMINI_API_KEY"),
            model_name=os.getenv("LLM_MODEL", "gemini-2.0-flash"),
            max_retries=int(os.getenv("LLM_MAX_RETRIES", 5)),
            max_delay=int(os.getenv("LLM_MAX_DELAY", 60)),
        )
        
        self._client = chromadb.PersistentClient(
            path=self._persist_directory
            )
        
        self._collection = self._client.get_or_create_collection(
            name=self._collection_name
        )
        
        logger.info("RAG Pipeline initialized successfully.")

    def ingestDocument(
            self,
            document_path: Union[str, Path],
    ) -> Dict[str, Any]:
        """
        Ingest a document into the RAG pipeline.

        Args:
            document_path: Path to the document to ingest.

        Returns:
            A dictionary with ingestion results.
        """
        logger.info(f"Ingesting document: {document_path}")

        # Process the document
        processed = self._document_processor.process_document(document_path)

        # Add to vector store
        self._collection.add(
            documents=[chunk['text'] for chunk in processed['chunks']],
            embeddings=processed['embeddings'],
            metadatas=[processed['metadata']] * len(processed['chunks']),
            ids = [ f"{processed['metadata']['source']}_chunk_{i}" for i in range(len(processed['chunks'])) ]
        )

        logger.info(f"Document ingested successfully: {document_path}.\nProcessed {len(processed['chunks'])} chunks.")

        return processed
    
    def getContext(
            self,
            query_text: str,
            n_results: int = 5,
            where: Optional[Dict[str, Any]] = None
    ) -> str :
        """
        Add context to a query by retrieving relevant documents.

        Args:
            query_text: The input query string.
            n_results: Number of top similar documents to retrieve.
            embedding_model: Embedding model name (uses .env if not provided).
            where: Optional metadata filter for the search.

        Returns:
            A formatted prompt containing the user query and added context.
        """
        logger.info(f"Querying vector storage for {n_results} chunks.")

        self._embedding_model = SentenceTransformer(self._embedding_model_name)
        query_embeddings = self._embedding_model.encode(query_text).tolist()
        results = self._collection.query(
            query_embeddings=query_embeddings,
            n_results=n_results,
            where=where
        )

        documents = results['documents'][0]
        sources = [metadata['source'] for metadata in results['metadatas'][0]]

        context = ",\n".join(
            [f"{doc}\n(Source: {src})" for (doc, src) in zip(documents, sources)]
            )
        context_prompt = (
            f"Answer the user's question, using the provided context to augment your existing knowledge. Trust the provided context over raw intuition. Cite the source of the context you use. \n\nContext:\n{context},\n\nQuestion: {query_text}"
            )

        logger.info(f"Query returned {len(results['documents'])} documents.")

        return context_prompt

    def queryWithContext(
            self,
            query_text: str,
            n_results: int = 5,
            where: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Query the LLM with added context from the vector store.

        Args:
            query_text: The input query string.
            n_results: Number of top similar documents to retrieve.
            where: Optional metadata filter for the search.
        Returns:
            response: str, The LLM's response text.
        """
        context_prompt = self.getContext(
            query_text=query_text,
            n_results=n_results,
            where=where
        )

        response = self._llm_client.query(context_prompt)

        return response
    def listDocuments(self) -> List[str]:
        """
        Get a list of unique document sources in the vector store.
        
        Returns:
            List of document filenames
        """
        # Get all documents
        all_docs = self._collection.get()
        
        # Extract unique sources
        sources = set()
        if all_docs['metadatas']:
            for metadata in all_docs['metadatas']:
                if 'source' in metadata:
                    sources.add(metadata['source'])
        
        return sorted(list(sources))
    
    def getStats(self) -> Dict[str, Any]:
        """
        Get statistics about the RAG pipeline.
        
        Returns:
            Dictionary with pipeline statistics
        """
        return {
            'total_chunks': self._collection.count(),
            'total_documents': len(self.listDocuments()),
            'collection_name': self._collection_name,
            'persist_directory': self._persist_directory,
            'embedding_config': {
                'chunk_size': self._chunk_size,
                'overlap_size': self._overlap_size,
                'embedding_model': self._embedding_model_name
            }
        }
    
    def reset(self) -> None:
        """
        Reset the vector store (delete all documents).
        
        Warning: This is irreversible!
        """
        self._collection.delete()
        logger.info("Vector store has been reset")
    
    def __repr__(self) -> str:
        """String representation of RAGPipeline."""
        stats = self.getStats()
        return (
            f"RAGPipeline(documents={stats['total_documents']}, "
            f"chunks={stats['total_chunks']}, "
            f"collection='{stats['collection_name']}')"
        )