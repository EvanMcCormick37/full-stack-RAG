import pytest
from datetime import datetime
from unittest.mock import Mock, patch
import numpy as np
from app.services.rag_service import RAGService
from app.models.schemas import (
    Source,
    QueryResponse,
    PromptStyle,
    DocumentListResponse,
    DocumentMetadata
)
from app.core.exceptions import VectorStoreError


@pytest.fixture
def mock_llm_client():
    """Create a mock LLM client"""
    client = Mock()
    client.answer = Mock(return_value="This is a test answer from the LLM.")
    return client


@pytest.fixture
def mock_embedding_model():
    """Create a mock SentenceTransformer"""
    model = Mock()
    # Mock encode to return fake embeddings
    model.encode = Mock(side_effect=lambda x, **kwargs: 
        np.random.rand(len(x) if isinstance(x, list) else 1, 384).tolist()
        if isinstance(x, list) 
        else np.random.rand(384).tolist()
    )
    return model


@pytest.fixture
def mock_vector_database():
    """Create a mock ChromaDB collection"""
    db = Mock()
    db.add = Mock()
    db.query = Mock(return_value={
        'ids': [['doc1_0', 'doc1_1']],
        'documents': [['First chunk text', 'Second chunk text']],
        'metadatas': [[
            {'document_id': 'doc1', 'filename': 'test.pdf', 'file_size': 10240, 'upload_time': datetime.now().timestamp()},
            {'document_id': 'doc1', 'filename': 'test.pdf', 'file_size': 10240, 'upload_time': datetime.now().timestamp()}
        ]],
        'distances': [[0.1, 0.2]]
    })
    db.get = Mock(return_value={
        'ids': ['doc1_0', 'doc1_1'],
        'documents': ['First chunk', 'Second chunk'],
        'metadatas': [
            {'document_id': 'doc1', 'filename': 'test.pdf', 'file_size': 10240, 'upload_time': datetime.now().timestamp()},
            {'document_id': 'doc1', 'filename': 'test.pdf', 'file_size': 10240, 'upload_time': datetime.now().timestamp()}
        ]
    })
    db.delete = Mock()
    return db


@pytest.fixture
def rag_service(mock_llm_client, mock_embedding_model, mock_vector_database):
    """Create a RAGService instance with mocked dependencies"""
    with patch('app.services.rag_service.SentenceTransformer', return_value=mock_embedding_model):
        # Patch client and set its collection return value
        with patch('app.services.rag_service.chromadb.PersistentClient') as mock_client:
            mock_client.return_value.get_or_create_collection.return_value = mock_vector_database
            service = RAGService(llm_client=mock_llm_client)
            return service


@pytest.fixture
def sample_document(tmp_path):
    """Create a sample text document for testing"""
    doc_path = tmp_path / "sample.txt"
    doc_path.write_text("""
    This is a sample document for testing the RAG system.
    It contains multiple sentences and paragraphs.
    
    The document discusses various topics including artificial intelligence,
    machine learning, and natural language processing.
    
    This is sufficient content for testing document processing.
    """)
    return str(doc_path)


class TestProcessDocument:
    """Tests for process_document method"""
    
    def test_process_document_success(self, rag_service, sample_document, mock_vector_database):
        """Test successful document processing"""
        document_id = "test_doc_123"
        filename = "sample.txt"
        file_size = 1024
        upload_time = datetime.now()
        
        with patch('app.services.document_service.extract_text', return_value="Sample text content"):
            with patch('app.services.document_service.chunk_text', return_value=["chunk1", "chunk2", "chunk3"]):
                num_chunks = rag_service.process_document(
                    document_id=document_id,
                    filename=filename,
                    file_size=file_size,
                    file_path=sample_document,
                    upload_time=upload_time
                )
        
        # Verify chunks were returned
        assert num_chunks == 3
        
        # Verify vector database was called
        mock_vector_database.add.assert_called_once()
        
        # Verify the call arguments
        call_args = mock_vector_database.add.call_args
        assert call_args.kwargs['documents'] == ["chunk1", "chunk2", "chunk3"]
        assert len(call_args.kwargs['embeddings']) == 3
        assert len(call_args.kwargs['metadatas']) == 3
        assert len(call_args.kwargs['ids']) == 3
    
    def test_process_document_metadata(self, rag_service, sample_document, mock_vector_database):
        """Test that document metadata is correctly stored"""
        document_id = "doc456"
        filename = "test.pdf"
        file_size = 1024
        upload_time = datetime(2024, 1, 15, 10, 30)
        
        with patch('app.services.document_service.extract_text', return_value="Text"):
            with patch('app.services.document_service.chunk_text', return_value=["chunk1"]):
                rag_service.process_document(
                    document_id=document_id,
                    filename=filename,
                    file_size=file_size,
                    file_path=sample_document,
                    upload_time=upload_time
                )
        
        # Check metadata
        call_args = mock_vector_database.add.call_args
        metadata = call_args.kwargs['metadatas'][0]
        assert metadata['document_id'] == document_id
        assert metadata['filename'] == filename
        assert metadata['file_size'] == file_size
        assert metadata['upload_time'] == upload_time.timestamp()
    
    def test_process_document_chunk_ids(self, rag_service, sample_document, mock_vector_database):
        """Test that chunk IDs are correctly generated"""
        document_id = "doc789"
        
        with patch('app.services.document_service.extract_text', return_value="Text"):
            with patch('app.services.document_service.chunk_text', return_value=["c1", "c2", "c3"]):
                rag_service.process_document(
                    document_id=document_id,
                    filename="test.txt",
                    file_size=1024,
                    file_path=sample_document,
                    upload_time=datetime.now()
                )
        
        call_args = mock_vector_database.add.call_args
        chunk_ids = call_args.kwargs['ids']
        assert chunk_ids == [f"{document_id}_0", f"{document_id}_1", f"{document_id}_2"]
    
    def test_process_document_database_error(self, rag_service, sample_document, mock_vector_database):
        """Test handling of database errors"""
        mock_vector_database.add.side_effect = Exception("Database error")
        
        with patch('app.services.document_service.extract_text', return_value="Text"):
            with patch('app.services.document_service.chunk_text', return_value=["chunk1"]):
                with pytest.raises(VectorStoreError) as exc_info:
                    rag_service.process_document(
                        document_id="doc",
                        filename="test.txt",
                        file_size=1024,
                        file_path=sample_document,
                        upload_time=datetime.now()
                    )
                assert "Failed to add document chunks" in str(exc_info.value)


class TestQuery:
    """Tests for query method"""
    
    def test_query_success(self, rag_service, mock_llm_client, mock_vector_database):
        """Test successful query execution"""
        question = "What is machine learning?"
        
        response = rag_service.query(
            question=question,
            style=PromptStyle.SIMPLE,
            n_results=5,
            return_context=False
        )
        
        # Verify response structure
        assert isinstance(response, QueryResponse)
        assert response.answer == "This is a test answer from the LLM."
        assert response.context is None
        
        # Verify embedding was generated
        rag_service._embedding_model.encode.assert_called_once_with(question)
        
        # Verify vector database was queried
        mock_vector_database.query.assert_called_once()
        
        # Verify LLM was called
        mock_llm_client.answer.assert_called_once()
    
    def test_query_with_context(self, rag_service):
        """Test query with context returned"""
        question = "What is AI?"
        
        response = rag_service.query(
            question=question,
            style=PromptStyle.SCHOLAR,
            n_results=3,
            return_context=True
        )
        
        # Verify context is included
        assert response.context is not None
        assert isinstance(response.context, list)
        assert len(response.context) > 0
        assert all(isinstance(src, Source) for src in response.context)
    
    def test_query_different_styles(self, rag_service, mock_llm_client):
        """Test query with different prompt styles"""
        question = "Explain transformers"
        
        # Test different styles
        for style in [PromptStyle.SIMPLE, PromptStyle.DISTRACTED, PromptStyle.SCHOLAR]:
            response = rag_service.query(
                question=question,
                style=style,
                n_results=5
            )
            assert isinstance(response, QueryResponse)
        
        # Verify LLM was called multiple times
        assert mock_llm_client.answer.call_count == 3
    
    def test_query_custom_n_results(self, rag_service):
        """Test query with custom number of results"""
        question = "Test query"
        n_results = 10
        
        rag_service.query(
            question=question,
            style=PromptStyle.SIMPLE,
            n_results=n_results
        )
        
        # Verify query was called with correct n_results
        call_args = mock_vector_database.query.call_args
        assert call_args.kwargs['n_results'] == n_results


class TestListDocuments:
    """Tests for list_documents method"""
    
    def test_list_documents_with_documents(self, rag_service, mock_vector_database):
        """Test listing documents when documents exist"""
        # Mock database response with documents
        mock_vector_database.get.return_value = {
            'ids': ['doc1_0', 'doc1_1', 'doc2_0'],
            'documents': ['chunk1', 'chunk2', 'chunk3'],
            'metadatas': [
                {'source': 'document1.pdf'},
                {'source': 'document1.pdf'},
                {'source': 'document2.txt'}
            ]
        }
        
        response = rag_service.list_documents()
        
        # Verify response structure
        assert isinstance(response, DocumentListResponse)
        assert 'document1.pdf' in response.documents
        assert 'document2.txt' in response.documents
        assert response.count == 2
        assert response.documents == sorted(response.documents)  # Should be sorted
    
    def test_list_documents_empty(self, rag_service, mock_vector_database):
        """Test listing documents when no documents exist"""
        mock_vector_database.get.return_value = {
            'ids': [],
            'documents': [],
            'metadatas': []
        }
        
        response = rag_service.list_documents()
        
        assert isinstance(response, DocumentListResponse)
        assert response.documents == []
        assert response.count == 0
    
    def test_list_documents_no_duplicates(self, rag_service, mock_vector_database):
        """Test that duplicate sources are removed"""
        mock_vector_database.get.return_value = {
            'ids': ['doc1_0', 'doc1_1', 'doc1_2'],
            'metadatas': [
                {'source': 'same_doc.pdf'},
                {'source': 'same_doc.pdf'},
                {'source': 'same_doc.pdf'}
            ]
        }
        
        response = rag_service.list_documents()
        
        assert len(response.documents) == 1
        assert response.count == 1

class TestGetDocument:
    """Tests for get_document method"""
    
    def test_get_document_exists(self, rag_service,):
        """Test getting a document that exists"""
        document_id = "test_doc_123"
        upload_time = datetime(2024, 1, 15, 10, 30)
        
        mock_vector_database.get.return_value = {
            'ids': [document_id],
            'metadatas': [{
                'name': 'test.pdf',
                'size': 1024,
                'upload_time': upload_time
            }]
        }
        
        result = rag_service.get_document(document_id)
        
        # Verify result
        assert result is not None
        assert isinstance(result, DocumentMetadata)
        assert result.document_id == document_id
        assert result.filename == 'test.pdf'
        assert result.file_size == 1024
        assert result.upload_time == upload_time
    
    def test_get_document_not_exists(self, rag_service, mock_vector_database):
        """Test getting a document that doesn't exist"""
        mock_vector_database.get.return_value = {
            'ids': [],
            'metadatas': []
        }
        
        result = rag_service.get_document("nonexistent_doc")
        
        assert result is None
    
    def test_get_document_calls_database(self, rag_service, mock_vector_database):
        """Test that get_document calls the database correctly"""
        document_id = "doc456"
        
        mock_vector_database.get.return_value = {
            'ids': [document_id],
            'metadatas': [{'name': 'test.txt', 'size': 500, 'upload_time': datetime.now().timestamp()}]
        }
        
        rag_service.get_document(document_id)
        
        # Verify database was called with correct ID
        mock_vector_database.get.assert_called_once_with(ids=document_id)


class TestDeleteDocument:
    """Tests for delete_document method"""
    
    def test_delete_document_not_found(self, rag_service, mock_vector_database):
        """Test deleting a document that doesn't exist"""
        document_id = "nonexistent_doc"
        
        # Mock that document still exists after delete (deletion failed)
        mock_vector_database.get.return_value = {
            'ids': [document_id]
        }
        
        result = rag_service.delete_document(document_id)
        
        # Verify deletion failed
        assert result is False
    
    def test_delete_document_calls_correct_methods(self, rag_service, mock_vector_database):
        """Test that delete_document calls methods in correct order"""
        document_id = "doc123"
        
        mock_vector_database.get.return_value = {'ids': []}
        
        rag_service.delete_document(document_id)
        
        # Verify both delete and get were called
        assert mock_vector_database.delete.called
        assert mock_vector_database.get.called


class TestConvertChromaDBQueryResult:
    """Tests for _convert_chromadb_queryresult_to_sources method"""
    
    def test_convert_queryresult(self, rag_service):
        """Test conversion of ChromaDB query result to Source objects"""
        upload_time = datetime(2024, 1, 15, 10, 30)
        
        queryresult = {
            'ids': [['doc1_0', 'doc1_1', 'doc2_0']],
            'documents': [['First chunk', 'Second chunk', 'Third chunk']],
            'metadatas': [[
                {'document_id': 'doc1', 'filename': 'doc1.pdf', 'file_size': 1024, 'upload_time': upload_time.timestamp()},
                {'document_id': 'doc1', 'filename': 'doc1.pdf', 'file_size': 1024, 'upload_time': upload_time.timestamp()},
                {'document_id': 'doc2', 'filename': 'doc2.txt', 'file_size': 1024, 'upload_time': upload_time.timestamp()}
            ]]
        }
        
        sources = rag_service._convert_chromadb_queryresult_to_sources(queryresult)
        
        # Verify conversion
        assert len(sources) == 3
        assert all(isinstance(src, Source) for src in sources)
        
        # Check first source
        assert sources[0].document_id == 'doc1'
        assert sources[0].chunk_text == 'First chunk'
        assert sources[0].filename == 'doc1.pdf'
        assert sources[0].file_size == 1024
        assert sources[0].upload_time == upload_time
    
    def test_convert_empty_result(self, rag_service):
        """Test conversion of empty query result"""
        query_result = {
            'ids': [[]],
            'documents': [[]],
            'metadatas': [[]]
        }
        
        sources = rag_service._convert_chromadb_queryresult_to_sources(query_result)
        
        assert sources == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
