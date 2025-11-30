from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

# Enum Classes
class DocumentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

# Upload Schemas
class DocumentMetadata(BaseModel):
    document_id: str                            # The document id
    filename: str                               # The name of the document
    upload_time: datetime                       # The time which the file was uploaded
    last_accessed: Optional[datetime] = None    # The time in which the document was last accessed
    session_id: str                             # The session ID in which the document was uploaded
    num_chunks: int                             # The number of chunks the document was split into
    status: DocumentStatus                      # The upload status of the document


class UploadResponse(BaseModel):
    document_metadata: DocumentMetadata     # The metadata for the document, returned when upload is complete or errors


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500)        # The question the user is asking the LLM


class Source(BaseModel):
    chunk_id: str                       # The chunk text ID
    chunk_text: str                     # The raw chunk text
    document_id: str                    # The document ID associated with the chunk text


class QueryResponse(BaseModel):
    answer: str                         # The answer returned by the LLM client
    sources: List[Source]               # The sources retrieved by the RAG model
    document_metadatas: List[DocumentMetadata]   # The document sources used by the RAG model for this query


# List Documents Schemas
class DocumentListResponse(BaseModel):
    documents: Optional[List[DocumentMetadata]] = None  # The documents being listed
    count: int                                          # The total number of uploaded documents


class DeleteResponse(BaseModel):
    deleted: bool                       # Whether or not the deletion was successful. False may indicate the file was never in the database to begin with.