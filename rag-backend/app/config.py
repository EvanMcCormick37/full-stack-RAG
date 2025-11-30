from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Backend configuration settings
    """
    # API
    API_VERSION: str = "./temp"
    API_PREFIX: str = "/api/v1.1"
    API_KEY: str

    # Document Upload
    MAX_FILE_SIZE: int = 100 * 1024 * 1024
    ALLOWED_EXTENSIONS: set = {".pdf", ".docx", ".txt", ".md"}

    # Document Processing
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # Vector
    COLLECTION_NAME: str = "chunks"
    N_SEARCH_RESULTS: int = 25
    MAX_CHUNKS: int = 100000
    
    # LLM Client
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-2.0-flash"
    LLM_MAX_RETRIES: int = 5
    LLM_MAX_DELAY: int = 60
    MAX_CACHE_SIZE:int = 100
    RETURN_CONTEXT: bool = False

    #Directories and paths
    UPLOAD_DIR: str = "./uploads"
    TEMP_DIR: str = "./temp"
    CHROMADB_PERSIST_DIR: str = "./chroma"
    METADATA_DB_PATH: str = "./chroma/metadata.db"

    model_config = SettingsConfigDict(
        env_file = ".env"
    )

settings = Settings()
