"""
Automated tests for RAG API endpoints
Tests for /documents and /query endpoints
"""
import pytest
import io
from fastapi.testclient import TestClient
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app
from app.config import settings

# Auth headers required for all protected endpoints
AUTH_HEADERS = {settings.API_KEY_NAME: settings.API_KEY}

# Test session ID for document ownership
TEST_SESSION_ID = "test-session-123"

client = TestClient(app)


def get_headers(session_id: str = None) -> dict:
    """Build headers dict with auth and optional session ID"""
    headers = AUTH_HEADERS.copy()
    if session_id:
        headers["X-Session-ID"] = session_id
    return headers


def upload_test_document(content: bytes, filename: str, session_id: str = None) -> dict:
    """Helper to upload a test document and return the response data"""
    file = (filename, io.BytesIO(content), "text/plain")
    response = client.post(
        f"{settings.API_PREFIX}/documents/",
        files={"file": file},
        headers=get_headers(session_id)
    )
    assert response.status_code == 200, f"Upload failed: {response.json()}"
    return response.json()


def delete_test_document(document_id: str, session_id: str = None) -> dict:
    """Helper to delete a test document"""
    response = client.delete(
        f"{settings.API_PREFIX}/documents/{document_id}",
        headers=get_headers(session_id)
    )
    return response


# =============================================================================
# Health Check Tests
# =============================================================================
class TestHealthChecks:
    """Test all health check endpoints"""
    
    def test_main_health(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_documents_health(self):
        response = client.get(
            f"{settings.API_PREFIX}/documents/health",
            headers=AUTH_HEADERS
        )
        assert response.status_code == 200
        assert response.json()["status"] == "operational"
    
    def test_query_health(self):
        response = client.get(
            f"{settings.API_PREFIX}/query/health",
            headers=AUTH_HEADERS
        )
        assert response.status_code == 200
        assert response.json()["status"] == "operational"


# =============================================================================
# Security Tests
# =============================================================================
class TestSecurity:
    """Test API Key security enforcement"""
    
    def test_access_without_key(self):
        """Protected endpoint should reject requests without API key"""
        response = client.get(f"{settings.API_PREFIX}/documents/")
        assert response.status_code == 403
        assert response.json()["detail"] == "Not authenticated"

    def test_access_with_wrong_key(self):
        """Protected endpoint should reject requests with wrong API key"""
        wrong_headers = {settings.API_KEY_NAME: "wrong_secret"}
        response = client.get(
            f"{settings.API_PREFIX}/documents/",
            headers=wrong_headers
        )
        assert response.status_code == 403
        assert response.json()["detail"] == "Could not validate credentials"

    def test_access_with_correct_key(self):
        """Protected endpoint should accept requests with correct API key"""
        response = client.get(
            f"{settings.API_PREFIX}/documents/",
            headers=AUTH_HEADERS
        )
        assert response.status_code == 200


# =============================================================================
# Document Endpoint Tests
# =============================================================================
class TestDocumentEndpoints:
    """Test document upload, list, get, and delete"""
    
    def test_upload_and_delete_document(self):
        """Test uploading a document and then deleting it"""
        content = b"Machine learning is a branch of AI that enables systems to learn from data."
        
        # Upload
        data = upload_test_document(content, "test.txt", TEST_SESSION_ID)
        assert "document_metadata" in data
        assert "document_id" in data["document_metadata"]
        assert data["document_metadata"]["num_chunks"] > 0
        
        document_id = data["document_metadata"]["document_id"]
        
        # Delete
        delete_response = delete_test_document(document_id, TEST_SESSION_ID)
        assert delete_response.status_code == 200
        assert delete_response.json()["deleted"] == True

    def test_upload_multiple_and_delete_all(self):
        """Test uploading multiple documents and deleting them all"""
        content1 = b"Machine learning is a branch of AI."
        content2 = b"GPT stands for Generative Pre-trained Transformer."
        
        # Upload two documents
        data1 = upload_test_document(content1, "test1.txt", TEST_SESSION_ID)
        data2 = upload_test_document(content2, "test2.txt", TEST_SESSION_ID)
        
        assert data1["document_metadata"]["num_chunks"] > 0
        assert data2["document_metadata"]["num_chunks"] > 0
        
        # Delete all
        delete_response = client.delete(
            f"{settings.API_PREFIX}/documents/",
            headers=get_headers(TEST_SESSION_ID)
        )
        assert delete_response.status_code == 200
        assert delete_response.json()["deleted"] == True
    
    def test_list_documents(self):
        """Test listing documents"""
        response = client.get(
            f"{settings.API_PREFIX}/documents/",
            headers=AUTH_HEADERS
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "count" in data
    
    def test_get_nonexistent_document(self):
        """Test getting a document that doesn't exist"""
        response = client.get(
            f"{settings.API_PREFIX}/documents/fake_id_12345",
            headers=AUTH_HEADERS
        )
        assert response.status_code == 404

    def test_get_existing_document(self):
        """Test getting an existing document's metadata"""
        content = b"Test content for document retrieval."
        
        # Upload
        data = upload_test_document(content, "retrieve_test.txt", TEST_SESSION_ID)
        document_id = data["document_metadata"]["document_id"]
        
        # Get
        response = client.get(
            f"{settings.API_PREFIX}/documents/{document_id}",
            headers=AUTH_HEADERS
        )
        assert response.status_code == 200
        assert response.json()["document_id"] == document_id
        
        # Cleanup
        delete_test_document(document_id, TEST_SESSION_ID)


# =============================================================================
# Query Endpoint Tests
# =============================================================================
class TestQueryEndpoint:
    """Test query endpoint functionality"""
    
    @pytest.fixture(autouse=True)
    def setup_document(self):
        """Upload a test document before each query test"""
        content = b"""
        Artificial Intelligence (AI) is intelligence demonstrated by machines.
        Machine Learning is a subset of AI that enables computers to learn from data.
        Deep Learning uses neural networks with multiple layers.
        Natural Language Processing helps computers understand human language.
        """
        
        data = upload_test_document(content, "ai_info.txt", TEST_SESSION_ID)
        self.document_id = data["document_metadata"]["document_id"]
        
        yield
        
        # Cleanup after test
        delete_test_document(self.document_id, TEST_SESSION_ID)
    
    def test_simple_query(self):
        """Test a basic query"""
        query_data = {"question": "What is machine learning?"}
        
        response = client.post(
            f"{settings.API_PREFIX}/query/",
            json=query_data,
            headers=AUTH_HEADERS
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "answer" in data
        assert len(data["answer"]) > 0
    
    def test_query_about_ai(self):
        """Test query about AI content"""
        query_data = {"question": "What is artificial intelligence?"}
        
        response = client.post(
            f"{settings.API_PREFIX}/query/",
            json=query_data,
            headers=AUTH_HEADERS
        )
        assert response.status_code == 200
        assert "answer" in response.json()
    
    def test_query_about_deep_learning(self):
        """Test query about deep learning"""
        query_data = {"question": "What is deep learning?"}
        
        response = client.post(
            f"{settings.API_PREFIX}/query/",
            json=query_data,
            headers=AUTH_HEADERS
        )
        assert response.status_code == 200
        assert "answer" in response.json()
    
    def test_invalid_query_empty(self):
        """Test query with empty question (should fail validation)"""
        query_data = {"question": ""}
        
        response = client.post(
            f"{settings.API_PREFIX}/query/",
            json=query_data,
            headers=AUTH_HEADERS
        )
        assert response.status_code == 422

    def test_invalid_query_too_short(self):
        """Test query with question too short (should fail validation)"""
        query_data = {"question": "Hi"}
        
        response = client.post(
            f"{settings.API_PREFIX}/query/",
            json=query_data,
            headers=AUTH_HEADERS
        )
        assert response.status_code == 422


# =============================================================================
# End-to-End Workflow Tests
# =============================================================================
class TestEndToEndWorkflow:
    """Test complete user workflows"""
    
    def test_upload_query_delete_workflow(self):
        """Test complete upload -> query -> delete workflow"""
        # 1. Upload document
        content = b"Quantum computing uses quantum mechanics to process information."
        data = upload_test_document(content, "quantum.txt", TEST_SESSION_ID)
        doc_id = data["document_metadata"]["document_id"]
        
        # 2. Query the document
        query_data = {"question": "What is quantum computing?"}
        query_response = client.post(
            f"{settings.API_PREFIX}/query/",
            json=query_data,
            headers=AUTH_HEADERS
        )
        assert query_response.status_code == 200
        assert "quantum" in query_response.json()["answer"].lower()
        
        # 3. Delete the document
        delete_response = delete_test_document(doc_id, TEST_SESSION_ID)
        assert delete_response.status_code == 200
        assert delete_response.json()["deleted"] == True
        
        # 4. Verify deletion
        get_response = client.get(
            f"{settings.API_PREFIX}/documents/{doc_id}",
            headers=AUTH_HEADERS
        )
        assert get_response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])