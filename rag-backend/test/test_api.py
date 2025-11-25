"""
Simple automated tests for RAG API endpoints
Basic functionality tests for /documents and /query endpoints
"""
import pytest
import io
from fastapi.testclient import TestClient
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app
from app.config import settings

AUTH_HEADERS={ settings.API_KEY_NAME: settings.API_KEY }

client = TestClient(app)


class TestHealthChecks:
    """Test all health check endpoints"""
    
    def test_main_health(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_documents_health(self):
        response = client.get(f"{settings.API_PREFIX}/documents/health", headers=AUTH_HEADERS)
        assert response.status_code == 200
        assert response.json()["status"] == "operational"
    
    def test_query_health(self):
        response = client.get(f"{settings.API_PREFIX}/query/health", headers=AUTH_HEADERS)
        assert response.status_code == 200
        assert response.json()["status"] == "operational"


class TestSecurity:
    """Test API Key security enforcement"""
    
    # Test a protected endpoint without any header
    def test_access_without_key(self):
        response = client.get(f"{settings.API_PREFIX}/documents/")
        assert response.status_code == 403
        assert response.json()["detail"] == "Not authenticated"

    # Test a protected endpoint with an incorrect key
    def test_access_with_wrong_key(self):
        wrong_headers = {settings.API_KEY_NAME: "wrong_secret"}
        response = client.get(f"{settings.API_PREFIX}/documents/", headers=wrong_headers)
        assert response.status_code == 403
        assert response.json()["detail"] == "Could not validate credentials"

    # Test successful access with the correct key
    def test_access_with_correct_key(self):
        response = client.get(f"{settings.API_PREFIX}/documents/", headers=AUTH_HEADERS)
        assert response.status_code == 200 # Should now succeed

class TestDocumentEndpoints:
    """Test document upload, list, get, and delete"""
    
    def test_upload_and_delete_document(self):
        """Test uploading a document and then deleting it"""
        # Create sample file
        content = b"Machine learning is a branch of AI that enables systems to learn from data."
        file = ("test.txt", io.BytesIO(content), "text/plain")
        
        # Upload
        upload_response = client.post(f"{settings.API_PREFIX}/documents/", files={"file": file}, headers=AUTH_HEADERS)
        assert upload_response.status_code == 200
        
        data = upload_response.json()
        assert "document_metadata" in data
        assert "document_id" in data["document_metadata"]
        assert data["document_metadata"]["num_chunks"] > 0
        
        document_id = data["document_metadata"]["document_id"]
        
        # Delete
        delete_response = client.delete(f"{settings.API_PREFIX}/documents/{document_id}", headers=AUTH_HEADERS)
        assert delete_response.status_code == 200
        assert delete_response.json()["deleted"] == True

    def test_upload_and_delete_all_documents(self):
        """Test uploading multiple documents and then deleting them all at once"""
        # Create sample file
        content1 = b"Machine learning is a branch of AI that enables systems to learn from data."
        content2 = b"GPT stands for Generative Pre-trained Transformer. GPTs form the basic architecture of all modern LLMs."
        file1 = ("test.txt", io.BytesIO(content1), "text/plain")
        file2 = ("test2.txt", io.BytesIO(content2),"text/plain")
        
        # Upload
        upload_response1 = client.post(f"{settings.API_PREFIX}/documents/", files={"file": file1}, headers=AUTH_HEADERS)
        upload_response2 = client.post(f"{settings.API_PREFIX}/documents/", files={"file": file2}, headers=AUTH_HEADERS)
        assert upload_response1.status_code == 200
        
        data1 = upload_response1.json()
        data2 = upload_response2.json()
        assert "document_metadata" in data1
        assert "document_id" in data1["document_metadata"]
        assert data1["document_metadata"]["num_chunks"] > 0
        assert "document_metadata" in data2
        assert "document_id" in data2["document_metadata"]
        assert data2["document_metadata"]["num_chunks"] > 0
        
        # Delete
        delete_response = client.delete(f"{settings.API_PREFIX}/documents/", params={'confirm': True}, headers=AUTH_HEADERS)
        assert delete_response.status_code == 200
        assert delete_response.json()["deleted"] == True
    
    def test_list_documents(self):
        """Test listing documents"""
        response = client.get(f"{settings.API_PREFIX}/documents/", headers=AUTH_HEADERS)
        assert response.status_code == 200
        
        data = response.json()
        assert "count" in data
    
    def test_get_nonexistent_document(self):
        """Test getting a document that doesn't exist"""
        response = client.get(f"{settings.API_PREFIX}/documents/fake_id_12345", headers=AUTH_HEADERS)
        assert response.status_code == 404


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
        file = ("ai_info.txt", io.BytesIO(content), "text/plain")
        
        response = client.post(f"{settings.API_PREFIX}/documents/", files={"file": file}, headers=AUTH_HEADERS)
        assert response.status_code == 200
        
        self.document_id = response.json()["document_metadata"]["document_id"]
        
        yield
        
        # Cleanup after test
        client.delete(f"{settings.API_PREFIX}/documents/{self.document_id}")
    
    def test_simple_query(self):
        """Test a basic query"""
        query_data = {
            "question": "What is machine learning?",
            "style": "simple"
        }
        
        response = client.post(f"{settings.API_PREFIX}/query/", json=query_data, headers=AUTH_HEADERS)
        assert response.status_code == 200
        
        data = response.json()
        assert "answer" in data
        assert len(data["answer"]) > 0
    
    def test_query_with_context(self):
        """Test query that returns context"""
        query_data = {
            "question": "What is AI?",
            "style": "simple",
            "return_context": True,
            "n_results": 3
        }
        
        response = client.post(f"{settings.API_PREFIX}/query/", json=query_data, headers=AUTH_HEADERS)
        assert response.status_code == 200
        
        data = response.json()
        assert "answer" in data
    
    def test_query_scholar_style(self):
        """Test query with scholar style"""
        query_data = {
            "question": "Explain deep learning",
            "style": "scholar"
        }
        
        response = client.post(f"{settings.API_PREFIX}/query/", json=query_data, headers=AUTH_HEADERS)
        assert response.status_code == 200
        assert "answer" in response.json()
    
    def test_query_distracted_style(self):
        """Test query with distracted style"""
        query_data = {
            "question": "What is NLP?",
            "style": "distracted"
        }
        
        response = client.post(f"{settings.API_PREFIX}/query/", json=query_data, headers=AUTH_HEADERS)
        assert response.status_code == 200
        assert "answer" in response.json()
    
    def test_invalid_query(self):
        """Test query with empty question"""
        query_data = {
            "question": "",
            "style": "simple"
        }
        
        response = client.post(f"{settings.API_PREFIX}/query/", json=query_data, headers=AUTH_HEADERS)
        # Should fail validation
        assert response.status_code == 422


class TestEndToEndWorkflow:
    """Test complete user workflow"""
    
    def test_complete_workflow(self):
        """Test upload -> query -> delete workflow"""
        # 1. Upload document
        content = b"Quantum computing uses quantum mechanics to process information."
        file = ("quantum.txt", io.BytesIO(content), "text/plain")
        
        upload_resp = client.post(f"{settings.API_PREFIX}/documents/", files={"file": file}, headers=AUTH_HEADERS)
        assert upload_resp.status_code == 200
        doc_id = upload_resp.json()["document_metadata"]["document_id"]
        
        # 2. Query the document
        query_data = {"question": "What is quantum computing?", "style": "simple"}
        query_resp = client.post(f"{settings.API_PREFIX}/query/", json=query_data, headers=AUTH_HEADERS)
        assert query_resp.status_code == 200
        assert "quantum" in query_resp.json()["answer"].lower()
        
        # 3. Delete the document
        delete_resp = client.delete(f"{settings.API_PREFIX}/documents/{doc_id}", headers=AUTH_HEADERS)
        assert delete_resp.status_code == 200
        assert delete_resp.json()["deleted"] == True
        
        # 4. Verify deletion
        get_resp = client.get(f"{settings.API_PREFIX}/documents/{doc_id}", headers=AUTH_HEADERS)
        assert get_resp.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])