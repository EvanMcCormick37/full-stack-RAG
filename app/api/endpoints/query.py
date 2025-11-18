from fastapi import APIRouter, HTTPException
from app.models.schemas import QueryRequest, QueryResponse
from app.services import rag_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/", response_model = QueryResponse)
def query(request: QueryRequest):
    """
    Query the RAG model

    Params:
        request - A QueryRequest with the question, prompt-style, optional metadata filter, n_results, and return_context.
    """
    try:
        response = rag_service.query(
            question = request.question,
            style = request.style,
            n_results = request.n_results,
            return_context = request.return_context
        )
        return response
    except Exception as e:
        raise HTTPException(
            status_code = 500,
            detail = f"Query failed: {str(e)}"
        )
    
@router.get("/health")
async def query_health():
    '''
    Check if query service is online
    '''
    return {"status": "operational","endpoint":"query"}