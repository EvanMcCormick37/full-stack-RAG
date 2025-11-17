class RAGException(Exception):
    """Base exception for RAG operations"""
    pass


class DocumentProcessingError(RAGException):
    """Error during document processing"""
    pass


class EmbeddingGenerationError(RAGException):
    """Error during embedding generation"""
    pass


class VectorStoreError(RAGException):
    """Error with vector store operations"""
    pass


class LLMError(RAGException):
    """Error with LLM generation"""
    pass


class FileValidationError(RAGException):
    """File validation failed"""
    pass


class FileOperationError(RAGException):
    """Error during file operations"""
    pass