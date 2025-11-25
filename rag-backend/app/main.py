from contextlib import asynccontextmanager
from fastapi import FastAPI, Security, Depends, HTTPException
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.api.endpoints import query, documents
from app.core.exceptions import RAGException
import logging
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

api_key_header = APIKeyHeader(name=settings.API_KEY_NAME, auto_error="false")

async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == settings.API_KEY:
        return api_key_header
    raise HTTPException(
        status_code=403,
        detail="Could not validate credentials"
    )
    
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
    title = settings.API_TITLE,
    version = settings.API_VERSION,
    description = "RAG-Powered Q&A System",
    lifespan = lifespan
)


# CORS middleware - STRICT
origins = [
    "http://localhost:5173", #Dev mode
    "https://full-stack-rag-neon.vercel.app/"
]

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
    tags=["Documents"],
    dependencies=[Depends(get_api_key)]
)
app.include_router(
    query.router,
    prefix=f"{settings.API_PREFIX}/query",
    tags=["Query"],
    dependencies=[Depends(get_api_key)]
)