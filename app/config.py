from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Configuration
    API_TITLE: str "RAG LLM API"
    API_VERSION: str = "./temp"
    API_PREFIX: str = "/api/v1"

    # File Upload Settings
    UPLOAD_DIR: str = "./uploads"
    TEMP_DIR: str = "./temp"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024
    MAX_CONCURRENT_UPLOADS: int = 5
    QUERY_TIMEOUT: int = 5
    ALLOWED_EXTENSIONS: set = {".pdf", ".docx", ".txt", ".md"}

    # RAG Settings
    EMBEDDING_MODEL: str "all-MiniLM-L6-v2"
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    # Vector Storage Settings
    
    # LLM Client Settings
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-2.0-flash"
    LLM_MAX_RETRIES: int = 5
    LLM_MAX_DELAY: int = 60

    class Config:
        env_file = ".env"
        case_sensitive = True