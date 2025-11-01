# RAG Pipeline CLI

A comprehensive command-line interface for testing and interacting with your RAG (Retrieval-Augmented Generation) system.

## Features

- 🚀 **Interactive Mode**: Menu-driven interface for all operations
- 📄 **Document Ingestion**: Upload PDFs, DOCX, and TXT files
- 🔍 **Query System**: Ask questions with context retrieval
- 📊 **Statistics**: View pipeline metrics and configuration
- 🧪 **Edge Case Testing**: Built-in test suite for validation
- 🎨 **Rich Output**: Beautiful formatted output with tables and markdown

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up your `.env` file:
```env
# Required
GEMINI_API_KEY=your_api_key_here

# Optional (defaults shown)
CHUNK_SIZE=500
OVERLAP_SIZE=50
EMBEDDING_MODEL=all-MiniLM-L6-v2
LLM_MODEL=gemini-2.0-flash
LLM_MAX_RETRIES=5
LLM_MAX_DELAY=60
VECTOR_STORE=./chroma_db
```

## Usage

#### Ingest a Document
```bash
python cli.py ingest path/to/document.pdf

# With verbose output
python cli.py ingest document.pdf --verbose
```

#### Query the System
```bash
python cli.py query "What is machine learning?"

# Retrieve more context chunks
python cli.py query "What is AI?" --results 10

# Show retrieved context
python cli.py query "Explain transformers" --show-context

# Get context only (without LLM query)
python cli.py query "What is RAG?" --no-llm
```

#### List Documents
```bash
python cli.py list
```

#### View Statistics
```bash
python cli.py stats

# JSON output
python cli.py stats --json-output
```

#### Reset Pipeline
```bash
python cli.py reset
```
**Warning**: This deletes all documents from the vector store!

#### Run Test Suite
```bash
python cli.py test-suite
```

This runs comprehensive edge case tests including:
- Empty pipeline queries
- Empty/whitespace queries
- Very long queries (>900k chars)
- Special characters handling
- Caching validation

## Edge Case Testing

The CLI includes built-in edge case testing to help you validate your RAG pipeline:

### Using Test Suite
Run the automated test suite:
```bash
python cli.py test-suite
```

This will test:
- ✅ Empty pipeline queries
- ✅ Input validation (empty, whitespace)
- ✅ Length limits (900k+ characters)
- ✅ Special characters and Unicode
- ✅ Caching mechanism

## Examples

### Example 1: Basic Workflow
```bash
# 1. Ingest a document
python cli.py ingest research_paper.pdf

# 2. Query it
python cli.py query "What are the main findings?"

# 3. Check stats
python cli.py stats
```

### Example 2: Interactive Testing Session
```bash
# Start interactive mode
python cli.py interactive

# Then follow the menu:
# 1 → Ingest multiple documents
# 2 → Test queries with different parameters
# 6 → Run edge case tests
# 4 → Check statistics
```

### Example 3: Edge Case Testing
```bash
# Run the full test suite
python cli.py test-suite

# Or test specific edge cases interactively
python cli.py interactive
# → Select 6 (Test edge cases)
# → Try each test scenario
```

## Testing Strategies

### Recommended Edge Cases to Test Manually

1. **Document Variety**:
   - Small files (<100 words)
   - Large files (>10,000 words)
   - Files with images/tables
   - Corrupted or partially readable files

2. **Query Types**:
   - Very short queries (1-2 words)
   - Very long queries (paragraphs)
   - Queries in different languages
   - Queries with typos
   - Domain-specific technical queries

3. **Context Retrieval**:
   - n_results = 1 (minimal context)
   - n_results = 20+ (maximum context)
   - Queries with no relevant documents
   - Queries matching all documents

4. **System Stress**:
   - Multiple rapid queries (test caching)
   - Large batch ingestion
   - Reset and re-populate
   - Concurrent operations (if applicable)

## Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'click'`
```bash
pip install click rich
```

**Issue**: `GEMINI_API_KEY not found`
- Make sure `.env` file exists in the root directory
- Verify `GEMINI_API_KEY` is set in `.env`

**Issue**: Pipeline initialization fails
- Check vector store permissions
- Verify embedding model can be downloaded
- Ensure sufficient disk space

**Issue**: Query returns no context
- Verify documents are ingested: `python cli.py list`
- Check pipeline stats: `python cli.py stats`
- Try a broader query

## Output Format

The CLI uses **Rich** library for beautiful output:
- 🎨 Color-coded status messages
- 📋 Formatted tables for data
- 📝 Markdown rendering for responses
- ⚡ Spinners for long operations
- 📦 Panels for organized information

## Advanced Usage

### Custom Configuration
Override defaults via command-line or environment variables:
```python
# In your code
pipeline = RAGPipeline(
    chunk_size=300,
    overlap_size=25,
    embedding_model="all-mpnet-base-v2"
)
```

### Programmatic Access
```python
from cli import get_pipeline

pipe = get_pipeline()
result = pipe.ingestDocument("document.pdf")
response = pipe.queryWithContext("Your question?")
```

## Next Steps

After manual testing with the CLI, consider:
1. ✅ Document successful test cases
2. 🐛 Log any bugs or edge cases found
3. 📈 Measure performance metrics
4. 🔧 Tune parameters based on results
5. 🚀 Move to FastAPI backend development

## Support

For issues or questions:
1. Check the main project README
2. Review error messages in verbose mode
3. Test with the built-in test suite
4. Verify `.env` configuration

---

**Happy Testing!** 🧪🔍