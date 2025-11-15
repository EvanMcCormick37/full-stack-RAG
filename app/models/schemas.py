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

class ContextSettings(str,Enum):
    RESPONSE_ONLY = "response_only"
    WITH_CONTEXT = "with_context"
    CONTEXT_ONLY = "context_only"

class PromptStyle(str, Enum):
    SIMPLE = "simple"
    DISTRACTED = "distracted"
    SCHOLAR = "scholar"

# Upload Schemas
class DocumentMetadata(BaseModel):
    filename: str                  # The name of the document
    file_size: int                  # The size of the document
    upload_time: datetime           # The time which the file was uploaded
    status: DocumentStatus          # The status of the document being uploaded
    num_chunks: int                 # The number of chunks the document was split into
    error: Optional[str] = None     # The error message if document upload failed


class UploadRequest(BaseModel):
    filepath: str                   # The filepath to the documents being uploaded
    filenames: Optional[List[str]]  # The filenames of the documents being uploaded

class UploadResponse(BaseModel):
    filename: str                   # The filename of the document being uploaded
    status: DocumentStatus          # The status of the document being uploaded
    documentMetadata: Optional[DocumentMetadata] = None     # The metadata for the document, returned when upload is complete or errors
    error: Optional[str] = None     # The error message when upload fails


# Query Schemas
class QueryMetadata(BaseModel):
    documents: Optional[List[str]] = None           # Filter for only these documents when querying
    min_upload_date: Optional[datetime] = None      # The earliest upload date to filter for
    max_upload_date: Optional[datetime] = None      # The latest upload date to filter for


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500)        # The question the user is asking the LLM
    metadata: Optional[QueryMetadata] = None                        # Optional metadata to filter query on
    n_results: Optional[int] = None                                 # Optional number of document chunks to use as context
    style: PromptStyle = PromptStyle.SIMPLE                         # The custom prompt to use with the context/query in the llm client
    context_settings: ContextSettings = ContextSettings.RESPONSE_ONLY       # Whether to return just the response, the response and context, or just the context


class Source(BaseModel):
    filename: str                       # The name of the source document
    page_number: Optional[int] = None   # The page number of the context text within the document
    chunk_text: str                     # The raw context text


class QueryResponse(BaseModel):
    answer: Optional[str] = None                # The answer returned by the LLM client
    sources: Optional[List[Source]] = None      # The sources retrieved by the RAG model
    error: Optional[str] = None                 # The error returned if queryResponse fails

# List Documents Schemas
class DocumentList(BaseModel):
    documents: List[DocumentMetadata]           # The documents being listed
    total: int                                  # The total number of uploaded documents

# Delete Documents Schemas
class DeleteRequest(BaseModel):
    filenames: List[str]                           # The filenames of the documents to be deleted
    by_metadata: Optional[QueryMetadata] = None     # The optional metadata filter to delete documents by


class DeleteResponse(BaseModel):
    filenames: List[str]           # The name of the files deleted
    error: Optional[str] = None     # The error message if deletion fails