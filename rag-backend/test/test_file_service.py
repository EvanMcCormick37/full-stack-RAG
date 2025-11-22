import os
import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock
from io import BytesIO
from fastapi import UploadFile
from app.services.file_service import (
    validate_file,
    save_upload,
    delete_file,
    generate_document_id
)
from app.core.exceptions import FileValidationError
from app.config import settings


@pytest.fixture
def temp_test_dir(tmp_path):
    """Create a temporary directory for testing"""
    test_dir = tmp_path / "test_uploads"
    test_dir.mkdir()
    return test_dir


@pytest.fixture
def mock_upload_file():
    """Create a mock UploadFile for testing"""
    def _create_mock(filename: str, content: bytes = b"test content", size: int = 100):
        file_mock = Mock(spec=UploadFile)
        file_mock.filename = filename
        file_mock.size = size
        file_mock.file = BytesIO(content)
        return file_mock
    return _create_mock


class TestValidateFile:
    """Tests for validate_file function"""
    
    def test_validate_file_valid_pdf(self, mock_upload_file):
        """Test validation of valid PDF file"""
        file = mock_upload_file("document.pdf", size=1000)
        # Should not raise an exception
        validate_file(file)
    
    def test_validate_file_valid_docx(self, mock_upload_file):
        """Test validation of valid DOCX file"""
        file = mock_upload_file("document.docx", size=1000)
        validate_file(file)
    
    def test_validate_file_valid_txt(self, mock_upload_file):
        """Test validation of valid TXT file"""
        file = mock_upload_file("document.txt", size=1000)
        validate_file(file)
    
    def test_validate_file_invalid_extension(self, mock_upload_file):
        """Test validation fails for invalid file extension"""
        file = mock_upload_file("document.exe", size=1000)
        with pytest.raises(FileValidationError) as exc_info:
            validate_file(file)
        assert "not allowed" in str(exc_info.value)
    
    def test_validate_file_too_large(self, mock_upload_file):
        """Test validation fails for file exceeding size limit"""
        file = mock_upload_file("document.pdf", size=settings.MAX_FILE_SIZE + 1)
        with pytest.raises(FileValidationError) as exc_info:
            validate_file(file)
        assert "too large" in str(exc_info.value)
    
    def test_validate_file_case_insensitive(self, mock_upload_file):
        """Test that file extension validation is case-insensitive"""
        file = mock_upload_file("document.PDF", size=1000)
        validate_file(file)


class TestSaveUpload:
    """Tests for save_upload function"""
    
    def test_save_upload_success(self, mock_upload_file, tmp_path, monkeypatch):
        """Test successful file save"""
        # Set temporary directory
        monkeypatch.setattr(settings, 'TEMP_DIR', str(tmp_path))
        
        file = mock_upload_file("test.pdf", content=b"PDF content here")
        document_id = "abc123"
        
        file_path = save_upload(file, document_id)
        
        # Verify file was created
        assert os.path.exists(file_path)
        assert file_path == str(tmp_path / f"{document_id}.pdf")
        
        # Verify content
        with open(file_path, 'rb') as f:
            assert f.read() == b"PDF content here"
        
        # Cleanup
        os.remove(file_path)
    
    def test_save_upload_creates_directory(self, mock_upload_file, tmp_path, monkeypatch):
        """Test that save_upload creates directory if it doesn't exist"""
        # Set non-existent directory
        non_existent = tmp_path / "non_existent"
        monkeypatch.setattr(settings, 'TEMP_DIR', str(non_existent))
        
        file = mock_upload_file("test.txt", content=b"Text content")
        document_id = "xyz789"
        
        file_path = save_upload(file, document_id)
        
        # Verify directory was created
        assert non_existent.exists()
        assert os.path.exists(file_path)
        
        # Cleanup
        os.remove(file_path)
    
    def test_save_upload_preserves_extension(self, mock_upload_file, tmp_path, monkeypatch):
        """Test that file extension is preserved"""
        monkeypatch.setattr(settings, 'TEMP_DIR', str(tmp_path))
        
        file = mock_upload_file("document.docx", content=b"Word doc")
        document_id = "doc123"
        
        file_path = save_upload(file, document_id)
        
        assert file_path.endswith(".docx")
        
        # Cleanup
        os.remove(file_path)


class TestDeleteFile:
    """Tests for delete_file function"""
    
    def test_delete_file_exists(self, tmp_path):
        """Test deleting a file that exists"""
        # Create a test file
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("test content")
        
        # Delete it
        result = delete_file(str(test_file))
        
        assert result is True
        assert not test_file.exists()
    
    def test_delete_file_not_exists(self, tmp_path):
        """Test deleting a file that doesn't exist"""
        non_existent = tmp_path / "non_existent.txt"
        
        result = delete_file(str(non_existent))
        
        assert result is False
    
    def test_delete_file_with_content(self, tmp_path):
        """Test deleting a file with actual content"""
        test_file = tmp_path / "content_file.pdf"
        test_file.write_bytes(b"PDF content here with some binary data")
        
        assert test_file.exists()
        
        result = delete_file(str(test_file))
        
        assert result is True
        assert not test_file.exists()


class TestGenerateDocumentId:
    """Tests for generate_document_id function"""
    
    def test_generate_document_id_format(self):
        """Test that generated ID has correct format"""
        filename = "test_document.pdf"
        doc_id = generate_document_id(filename)
        
        # Should be 16 characters long (MD5 hash truncated)
        assert len(doc_id) == 16
        # Should be hexadecimal
        assert all(c in "0123456789abcdef" for c in doc_id)
    
    def test_generate_document_id_unique(self):
        """Test that generated IDs are unique for same filename"""
        filename = "test.pdf"
        
        id1 = generate_document_id(filename)
        id2 = generate_document_id(filename)
        
        # Should be different due to UUID timestamp
        assert id1 != id2
    
    def test_generate_document_id_different_files(self):
        """Test IDs for different filenames"""
        id1 = generate_document_id("file1.pdf")
        id2 = generate_document_id("file2.pdf")
        
        assert id1 != id2
    
    def test_generate_document_id_special_characters(self):
        """Test ID generation with special characters in filename"""
        filename = "test document (1) [final].pdf"
        doc_id = generate_document_id(filename)
        
        assert len(doc_id) == 16
        assert all(c in "0123456789abcdef" for c in doc_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
