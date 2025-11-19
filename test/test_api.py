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

client = TestClient(app)

SAMPLE_TEXT = """
    Retrieval-Augmented Generation (RAG) is an innovative AI framework that enhances the output of large language models (LLMs) by giving them access to up-to-date, relevant, and authoritative external knowledge bases before generating a response. Instead of relying solely on the static data from their initial training, RAG models dynamically retrieve pertinent information to ground their responses in facts. This addresses key limitations of standard LLMs, such as producing outdated information, fabricating answers ("hallucinations"), or lacking domain-specific expertise.
The framework operates in two distinct stages: ingestion and inference.
The Ingestion Stage: Preparing the knowledge base
This preparatory stage is performed offline, before a user ever submits a query.
Data Sourcing: The first step involves gathering the external data to be used. This information can come from diverse sources, including documents (PDFs, Word files), web pages, databases, and APIs. This data is organized into a knowledge base that is separate from the LLM's core training data.
Chunking: To make the data manageable, documents are broken down into smaller, semantically coherent blocks of text called "chunks". The size of these chunks is a crucial parameter, as it must be large enough to retain context but small enough to fit within the LLM's context window.
Embedding and Vectorization: An embedding model converts each text chunk into a numerical vector. This process is known as vectorization. These vectors are multi-dimensional representations that capture the semantic meaning of the text. Text chunks with similar meanings are mapped to vectors that are close to each other in this high-dimensional space.
Vector Storage: The generated vectors are stored and indexed in a specialized database, known as a vector database. This allows for fast and efficient "semantic search," where the system can look for meaning rather than just keywords.
The Inference Stage: Generating a grounded response
This stage is triggered when a user submits a query to the RAG system.
Query Embedding: The user's input is first transformed into a vector using the same embedding model used during the ingestion stage.
Retrieval: The system uses this query vector to perform a semantic search in the vector database. It identifies and retrieves the most relevant data chunks, based on their vector similarity to the user's query.
Prompt Augmentation: The retrieved information is integrated into a new, more comprehensive prompt. This augmented prompt, now enriched with relevant context, is then passed to the LLM. This is often called "prompt stuffing" or "in-context learning."
Generation: The generative LLM uses the augmented prompt to formulate its response. By referencing the retrieved, up-to-date information, the model can produce a more accurate, contextually relevant, and grounded answer.
Response Handling: The LLM's final output is presented to the user. Some advanced RAG systems can also provide citations, allowing users to verify the sources used for the response.
"""


class TestHealthChecks:
    """Test all health check endpoints"""
    
    def test_main_health(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_documents_health(self):
        response = client.get("/api/v1/documents/health")
        assert response.status_code == 200
        assert response.json()["status"] == "operational"
    
    def test_query_health(self):
        response = client.get("/api/v1/query/health")
        assert response.status_code == 200
        assert response.json()["status"] == "operational"


class TestDocumentEndpoints:
    """Test document upload, list, get, and delete"""
    
    def test_upload_and_delete_document(self):
        """Test uploading a document and then deleting it"""
        # Create sample file
        content = b"Machine learning is a branch of AI that enables systems to learn from data."
        file = ("test.txt", io.BytesIO(content), "text/plain")
        
        # Upload
        upload_response = client.post("/api/v1/documents/", files={"file": file})
        assert upload_response.status_code == 200
        
        data = upload_response.json()
        assert "document_metadata" in data
        assert "document_id" in data["document_metadata"]
        assert data["document_metadata"]["num_chunks"] > 0
        
        document_id = data["document_metadata"]["document_id"]
        
        # Delete
        delete_response = client.delete(f"/api/v1/documents/{document_id}")
        assert delete_response.status_code == 200
        assert delete_response.json()["deleted"] == True
    
    def test_list_documents(self):
        """Test listing documents"""
        response = client.get("/api/v1/documents/")
        assert response.status_code == 200
        
        data = response.json()
        assert "count" in data
    
    def test_get_nonexistent_document(self):
        """Test getting a document that doesn't exist"""
        response = client.get("/api/v1/documents/fake_id_12345")
        assert response.status_code == 404
    
    def test_delete_nonexistent_document(self):
        """Test deleting a document that doesn't exist"""
        response = client.delete("/api/v1/documents/fake_id_12345")
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
        
        response = client.post("/api/v1/documents/", files={"file": file})
        assert response.status_code == 200
        
        self.document_id = response.json()["document_metadata"]["document_id"]
        
        yield
        
        # Cleanup after test
        client.delete(f"/api/v1/documents/{self.document_id}")
    
    def test_simple_query(self):
        """Test a basic query"""
        query_data = {
            "question": "What is machine learning?",
            "style": "simple"
        }
        
        response = client.post("/api/v1/query/", json=query_data)
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
        
        response = client.post("/api/v1/query/", json=query_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "answer" in data
    
    def test_query_scholar_style(self):
        """Test query with scholar style"""
        query_data = {
            "question": "Explain deep learning",
            "style": "scholar"
        }
        
        response = client.post("/api/v1/query/", json=query_data)
        assert response.status_code == 200
        assert "answer" in response.json()
    
    def test_query_distracted_style(self):
        """Test query with distracted style"""
        query_data = {
            "question": "What is NLP?",
            "style": "distracted"
        }
        
        response = client.post("/api/v1/query/", json=query_data)
        assert response.status_code == 200
        assert "answer" in response.json()
    
    def test_invalid_query(self):
        """Test query with empty question"""
        query_data = {
            "question": "",
            "style": "simple"
        }
        
        response = client.post("/api/v1/query/", json=query_data)
        # Should fail validation
        assert response.status_code == 422


class TestEndToEndWorkflow:
    """Test complete user workflow"""
    
    def test_complete_workflow(self):
        """Test upload -> query -> delete workflow"""
        # 1. Upload document
        content = b"Quantum computing uses quantum mechanics to process information."
        file = ("quantum.txt", io.BytesIO(content), "text/plain")
        
        upload_resp = client.post("/api/v1/documents/", files={"file": file})
        assert upload_resp.status_code == 200
        doc_id = upload_resp.json()["document_metadata"]["document_id"]
        
        # 2. Query the document
        query_data = {"question": "What is quantum computing?", "style": "simple"}
        query_resp = client.post("/api/v1/query/", json=query_data)
        assert query_resp.status_code == 200
        assert "quantum" in query_resp.json()["answer"].lower()
        
        # 3. Delete the document
        delete_resp = client.delete(f"/api/v1/documents/{doc_id}")
        assert delete_resp.status_code == 200
        assert delete_resp.json()["deleted"] == True
        
        # 4. Verify deletion
        get_resp = client.get(f"/api/v1/documents/{doc_id}")
        assert get_resp.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])