import os
import json
from dotenv import load_dotenv
from pathlib import Path
from src.document_processor import DocumentProcessor

def create_sample_txt():
    sample_text = """
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
    filepath = Path("sample_document.txt")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(sample_text.strip())
    
    return filepath

def test_basic_functionality():
    print("TEST 1: Basic Functionality Test")
    print("==" * 40)

    load_dotenv()

    processor = DocumentProcessor(
        chunk_size=int(os.getenv("CHUNK_SIZE", 300)),
        overlap_size=int(os.getenv("OVERLAP_SIZE", 50)),
        embedding_model=os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        )
    sample_file = create_sample_txt()
    result = processor.process_document(sample_file)


    metadata = result['metadata']
    text = result['text']
    chunks = result['chunks']
    embeddings = result['embeddings']

    print("\nMetadata:")
    print(json.dumps(metadata, indent=4))
    print("\nExtracted Text (first 500 characters):")
    print(text[:500] + "...")
    print(f"\nNumber of Chunks Created: {len(chunks)}")
    print(f"Embeddings Size: {len(embeddings)} X {len(embeddings[0])}")

    # Clean up
    os.remove(sample_file)

def main():
    test_basic_functionality()

if __name__ == "__main__":
    main()
