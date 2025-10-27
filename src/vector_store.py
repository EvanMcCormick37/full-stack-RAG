import os
import logging
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import chromadb
import uuid

logging.basicConfig(level = logging.INFO)
logger = logging.getLogger(__name__)

class VectorStore:
    # Vector store for managing document embeddings using ChromaDB
    # Handles:
    # -Adding Documents with embeddings
    # -Similarity search
    # -Metadata management
    # -Persistence

    def __init__(
            self,
            collection_name: str = "documents",
            embedding_function: Optional[Any] = None,
            persist_directory: str = "data/vector_store"
            ):
        self.collection_name = collection_name
        self._embedding_function = embedding_function
        self.persist_directory = persist_directory

        if self.persist_directory:
            persist_path = Path(self.persist_directory)
            persist_path.mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(
                path=str(persist_path)
                )
            logger.info(f"Initialized Persistent ChromaDB client at {self.persist_directory}")
        self._collection = self._client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "RAG Document Embeddings"}
        )

        logger.info(f"VectorStore initialized with collection: {self.collection_name}")
        logger.info(f"persist={self.persist_directory if self.persist_directory else 'in-memory'}")

    @property
    def collection(self):
        return self._collection
    
    @property
    def embedding_function(self):
        return self._embedding_function
    
    @property
    def client(self):
        return self._client
    
    def add_documents(
            self,
            documents: List[str],
            embeddings: List[List[float]],
            metadatas: Optional[List[Dict[str, Any]]] = None,
            ids: Optional[List[str]] = None
            ) -> List[str]:
        
        if not documents:
            logger.warning("No documents provided to add to vector store.")
            return []
        
        if len(documents) != len(embeddings):
            raise ValueError(f"Number of documents ({len(documents)}) must match number of embeddings({len(embeddings)}).")

        if ids is None:
            ids = [str(uuid.uuid4()) for _ in range(len(documents))]

        if metadatas is None:
            metadatas = [{} for _ in range(len(documents))]

        if len(metadatas) != len(documents):
            raise ValueError(f"Number of metadatas ({len(metadatas)}) must match number of documents({len(documents)}).")
        try:
            self._collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Added {len(documents)} documents to vector store.")
            return ids
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {str(e)}")
            raise


    def search(
        self,
        query_embedding: List[float],
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None
        ) -> Dict[str, Any]:
        try:
            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where,
                where_document=where_document
            )

            logger.info(f"Retrieved {len(results['ids'][0])} results from similarity search.")

            return {
                'ids': results['ids'][0],
                'documents': results['documents'][0],
                'metadatas': results['metadatas'][0],
                'distances': results['distances'][0]
            }
        
        except Exception as e:
            logger.error(f"Error during similarity search: {str(e)}")
            raise

    def search_by_text(
            self,
            query_text: str,
            embedding_function: Any,
            n_results: int = 5,
            where: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        if embedding_function is None:
            raise ValueError("An embedding function must be provided for text-based search.")

        query_embedding = embedding_function([query_text])[0]

        return self.search(
            query_embedding=query_embedding,
            n_results=n_results,
            where=where
        )
    
    def delete(
            self,
            ids: Optional[List[str]] = None,
            where: Optional[Dict[str, Any]] = None
    ) -> None:
        try:
            if ids:
                self._collection.delete(ids=ids)
                logger.info(f"Deleted {len(ids)} documents from vector store by IDs.")
            elif where and len(where) > 0:
                self._collection.delete(where=where)
                logger.info(f"Deleted documents from vector store by metadata filter: {where}.")
            else:
                raise ValueError("Either ids or where filter must be provided for deletion.")
        except Exception as e:
            logger.error(f"Error deleting documents from vector store: {str(e)}")
            raise

    def get_by_ids(self, ids: List[str]) -> Dict[str, Any]:
        try:
            results = self._collection.get(ids=ids)
            logger.info(f"Retrieved {len(results['ids'])} documents by IDs.")
            return results
        except Exception as e:
            logger.error(f"Error retrieving documents by IDs: {str(e)}")
            raise

    def count(self) -> int:
        return self._collection.count()
    
    def clear(self) -> None:
        try:
            all_data = self._collection.get()
            if all_data['ids']:
                self._collection.delete(ids=all_data['ids'])
                logger.info("Cleared all documents from vector store.")
        except Exception as e:
            logger.error(f"Error clearing vector store: {str(e)}")
            raise
    
    def reset(self) -> None:
        try:
            self._client.delete_collection(name=self.collection_name)
            logger.info(f"Deleted vector store collection: {self.collection_name}.")
            self._collection = self._client.create_collection(
                name=self.collection_name,
                metadata={"description": "RAG Document Embeddings"}
                )
            logger.info(f"Reset vector store collection: {self.collection_name}.")
        except Exception as e:
            logger.error(f"Error resetting vector store: {str(e)}")
            raise

    def get_collection_info(self) -> Dict[str, Any]:
        return {
            'name': self.collection_name,
            'count': self.count(),
            'metadata': self._collection.get_metadata(),
            'persist_directory': self.persist_directory
        }