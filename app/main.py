from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.api.endpoints import upload, query, documents
from app.utils.exceptions import RAGException
import logging
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Setup Lifespan Manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting RAG API...")
    # Initialize directories
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.TEMP_DIR, exist_ok=True)
    logger.info("API startup complete.")

    yield
    
    logger.info("Shutting down RAG API.")

# Initialize FastAPI
app = FastAPI(
    title = settings.TITLE,
    version = settings.API_VERSION,
    description = "RAG-Powered Q&A System",
    lifespan = lifespan
)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Global Exception Handler
@app.exception_handler(RAGException)
async def rag_exception_handler(request, e: RAGException):
    return JSONResponse(
        status_code = e.status_code,
        content = {"detail": e.detail, "error_type": e.error_type}
    )


# Health Check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.API_VERSION}

# Include Routers
app.include_router(
    documents.router,
    prefix=f"{settings.API_PREFIX}/documents",
    tags=["Documents"]
)
app.include_router(
    query.router,
    prefix=f"{settings.API_PREFIX}/query",
    tags=["Query"]
)