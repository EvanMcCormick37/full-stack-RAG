import os
import tempfile
from pathlib import Path

# Import the functions to test
from app.services.document_service import (
    extract_text,
    clean_text,
    find_sentence_boundary,
    chunk_text
)


def test_clean_text():
    """Test clean_text function"""
    print("\n" + "="*60)
    print("Testing clean_text function")
    print("="*60)
    
    # Test 1: Multiple newlines
    text = "Line 1\n\n\n\nLine 2"
    result = clean_text(text)
    assert result == "Line 1\n\nLine 2", f"Failed: {result}"
    print("✓ Multiple newlines reduced correctly")
    
    # Test 2: Multiple spaces
    text = "Word1    Word2     Word3"
    result = clean_text(text)
    assert result == "Word1 Word2 Word3", f"Failed: {result}"
    print("✓ Multiple spaces reduced correctly")
    
    # Test 3: Control characters removed
    text = "Normal text\x00with\x08control\x1fcharacters"
    result = clean_text(text)
    assert "\x00" not in result
    assert "\x08" not in result
    assert "\x1f" not in result
    print("✓ Control characters removed")
    
    # Test 4: Strip whitespace
    text = "   Text with spaces   "
    result = clean_text(text)
    assert result == "Text with spaces", f"Failed: {result}"
    print("✓ Leading/trailing whitespace stripped")
    
    # Test 5: Empty string
    result = clean_text("")
    assert result == "", f"Failed: {result}"
    print("✓ Empty string handled")
    
    # Test 6: Already clean text
    text = "This is clean text."
    result = clean_text(text)
    assert result == text, f"Failed: {result}"
    print("✓ Already clean text unchanged")
    
    print("\n✅ All clean_text tests passed!\n")


def test_find_sentence_boundary():
    """Test find_sentence_boundary function"""
    print("="*60)
    print("Testing find_sentence_boundary function")
    print("="*60)
    
    # Test 1: Period with space
    text = "First sentence. Second sentence."
    result = find_sentence_boundary(text)
    assert result == 16, f"Failed: expected 16, got {result}"
    print("✓ Period + space boundary found")
    
    # Test 2: Question mark
    text = "Is this a question? Yes it is."
    result = find_sentence_boundary(text)
    assert result == 20, f"Failed: expected 20, got {result}"
    print("✓ Question mark boundary found")
    
    # Test 3: Exclamation mark
    text = "This is exciting! Really exciting."
    result = find_sentence_boundary(text)
    assert result == 18, f"Failed: expected 18, got {result}"
    print("✓ Exclamation mark boundary found")
    
    # Test 4: Period with newline
    text = "First sentence.\nSecond sentence."
    result = find_sentence_boundary(text)
    assert result == 16, f"Failed: expected 16, got {result}"
    print("✓ Period + newline boundary found")
    
    # Test 5: Multiple endings (should find last one)
    text = "First sentence. Second sentence. Third sentence."
    result = find_sentence_boundary(text)
    assert result == 33, f"Failed: expected 33, got {result}"
    print("✓ Last sentence boundary found")
    
    # Test 6: No boundary
    text = "No sentence boundary here"
    result = find_sentence_boundary(text)
    assert result == -1, f"Failed: expected -1, got {result}"
    print("✓ No boundary returns -1")
    
    # Test 7: Empty string
    result = find_sentence_boundary("")
    assert result == -1, f"Failed: expected -1, got {result}"
    print("✓ Empty string returns -1")
    
    print("\n✅ All find_sentence_boundary tests passed!\n")


def test_chunk_text():
    """Test chunk_text function"""
    print("="*60)
    print("Testing chunk_text function")
    print("="*60)
    
    # Temporarily modify settings for testing
    from app.config import settings
    original_chunk_size = settings.CHUNK_SIZE
    original_overlap = settings.CHUNK_OVERLAP
    
    try:
        # Test 1: Basic chunking
        settings.CHUNK_SIZE = 50
        settings.CHUNK_OVERLAP = 10
        text = "This is a test sentence. " * 10
        result = chunk_text(text)
        assert len(result) > 1, f"Failed: expected multiple chunks, got {len(result)}"
        assert all(isinstance(chunk, str) for chunk in result)
        print("✓ Basic chunking creates multiple chunks")
        
        # Test 2: Short text (single chunk)
        settings.CHUNK_SIZE = 1000
        settings.CHUNK_OVERLAP = 100
        text = "This is a short text."
        result = chunk_text(text)
        assert len(result) == 1, f"Failed: expected 1 chunk, got {len(result)}"
        assert result[0] == "This is a short text.", f"Failed: {result[0]}"
        print("✓ Short text creates single chunk")
        
        # Test 3: Text cleaning during chunking
        settings.CHUNK_SIZE = 100
        settings.CHUNK_OVERLAP = 20
        text = "Text with    multiple   spaces\n\n\n\nand newlines."
        result = chunk_text(text)
        assert "    " not in result[0], "Failed: multiple spaces not cleaned"
        print("✓ Text is cleaned during chunking")
        
        # Test 4: Empty string
        result = chunk_text("")
        assert result == [], f"Failed: expected empty list, got {result}"
        print("✓ Empty string returns empty list")
        
        # Test 5: Overlap creates multiple chunks
        settings.CHUNK_SIZE = 100
        settings.CHUNK_OVERLAP = 30
        text = "A" * 200
        result = chunk_text(text)
        assert len(result) >= 2, f"Failed: expected >= 2 chunks, got {len(result)}"
        print("✓ Overlap parameter works")
        
        # Test 6: Long document
        settings.CHUNK_SIZE = 200
        settings.CHUNK_OVERLAP = 50
        text = """
        This is the first paragraph. It contains several sentences. 
        Each sentence adds to the content. This makes it realistic.
        
        This is the second paragraph. It also has multiple sentences.
        The content continues to grow. This tests chunking behavior.
        """ * 3
        result = chunk_text(text)
        assert len(result) >= 2, f"Failed: expected >= 2 chunks, got {len(result)}"
        assert all(len(chunk.strip()) > 0 for chunk in result), "Failed: empty chunks found"
        print("✓ Long document chunked correctly")
        
    finally:
        # Restore original settings
        settings.CHUNK_SIZE = original_chunk_size
        settings.CHUNK_OVERLAP = original_overlap
    
    print("\n✅ All chunk_text tests passed!\n")


def test_extract_text():
    """Test extract_text function"""
    print("="*60)
    print("Testing extract_text function")
    print("="*60)
    
    # Create a temporary directory for test files
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Test 1: Basic text file
        txt_file = temp_path / "sample.txt"
        content = "This is a sample text file.\nIt has multiple lines.\nFor testing purposes."
        txt_file.write_text(content, encoding='utf-8')
        
        result = extract_text(txt_file)
        assert "This is a sample text file." in result
        assert "It has multiple lines." in result
        assert "For testing purposes." in result
        print("✓ Text file extraction works (Path object)")
        
        # Test 2: String path
        result = extract_text(str(txt_file))
        assert "This is a sample text file." in result
        assert isinstance(result, str)
        print("✓ Text file extraction works (string path)")
        
        # Test 3: Empty file
        empty_file = temp_path / "empty.txt"
        empty_file.write_text("")
        result = extract_text(empty_file)
        assert result == "", f"Failed: expected empty string, got '{result}'"
        print("✓ Empty file returns empty string")
        
        # Test 4: Multi-line text
        multiline_file = temp_path / "multiline.txt"
        multiline_content = "Line 1\nLine 2\nLine 3\nLine 4"
        multiline_file.write_text(multiline_content)
        result = extract_text(multiline_file)
        assert "Line 1" in result
        assert "Line 2" in result
        assert "Line 3" in result
        assert "Line 4" in result
        print("✓ Multi-line text extracted correctly")
        
        # Test 5: Special encoding (latin-1)
        special_file = temp_path / "special.txt"
        special_content = "Café résumé naïve"
        special_file.write_bytes(special_content.encode('latin-1'))
        result = extract_text(special_file)
        assert len(result) > 0
        print("✓ Special encoding handled (latin-1 fallback)")
        
        # Test 6: Unsupported file type
        unsupported_file = temp_path / "file.xyz"
        unsupported_file.write_text("content")
        try:
            extract_text(unsupported_file)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Unsupported file type" in str(e)
            print("✓ Unsupported file type raises ValueError")
    
    print("\n✅ All extract_text tests passed!\n")


def test_integration():
    """Test integration of multiple functions"""
    print("="*60)
    print("Testing integration workflow")
    print("="*60)
    
    # Temporarily modify settings
    from app.config import settings
    original_chunk_size = settings.CHUNK_SIZE
    original_overlap = settings.CHUNK_OVERLAP
    
    try:
        settings.CHUNK_SIZE = 100
        settings.CHUNK_OVERLAP = 20
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Test 1: Extract -> Chunk workflow
            doc_path = temp_path / "test.txt"
            content = "This is sentence one. This is sentence two. " * 10
            doc_path.write_text(content)
            
            extracted = extract_text(doc_path)
            chunks = chunk_text(extracted)
            
            assert len(extracted) > 0
            assert len(chunks) > 1
            assert all(isinstance(chunk, str) for chunk in chunks)
            print("✓ Extract -> Chunk workflow works")
            
            # Test 2: Extract -> Clean -> Chunk workflow
            messy_doc = temp_path / "messy.txt"
            messy_content = "Sentence 1.    Sentence 2.\n\n\n\nSentence 3.     Sentence 4."
            messy_doc.write_text(messy_content)
            
            extracted = extract_text(messy_doc)
            cleaned = clean_text(extracted)
            chunks = chunk_text(extracted)
            
            assert "    " not in cleaned
            assert len(chunks) > 0
            print("✓ Extract -> Clean -> Chunk workflow works")
    
    finally:
        settings.CHUNK_SIZE = original_chunk_size
        settings.CHUNK_OVERLAP = original_overlap
    
    print("\n✅ All integration tests passed!\n")


def main():
    """Run all tests"""
    print("\n" + "🔬 Starting Document Service Tests" + "\n")
    
    tests = [
        test_clean_text,
        test_find_sentence_boundary,
        test_chunk_text,
        test_extract_text,
        test_integration
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"\n❌ {test.__name__} FAILED: {e}\n")
            failed += 1
        except Exception as e:
            print(f"\n❌ {test.__name__} ERROR: {e}\n")
            failed += 1
    
    print("\n" + "="*60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("="*60)
    
    if failed == 0:
        print("\n🎉 All tests passed successfully!\n")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed\n")
        return 1


if __name__ == "__main__":
    exit(main())
