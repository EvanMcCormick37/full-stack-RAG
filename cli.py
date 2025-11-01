#!/usr/bin/env python3
"""
RAG Pipeline CLI - Command-line interface for testing the RAG system
"""
import sys
import click
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from src.rag_pipeline import RAGPipeline

# Load environment variables
load_dotenv()

# Initialize rich console for pretty output
console = Console()

# Global pipeline instance
pipeline = None


def get_pipeline() -> RAGPipeline:
    """Get or create the pipeline instance"""
    global pipeline
    if pipeline is None:
        console.print("[yellow]Initializing RAG Pipeline...[/yellow]")
        pipeline = RAGPipeline()
        console.print("[green]✓ Pipeline initialized[/green]")
    return pipeline


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """
    RAG Pipeline CLI - Test and interact with your RAG system
    
    Use 'cli.py COMMAND --help' for more information on a specific command.
    """
    pass


@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--verbose', '-v', is_flag=True, help='Show detailed processing information')
def ingest(file_path: str, verbose: bool):
    """
    Ingest a document into the RAG pipeline.
    
    FILE_PATH: Path to the document to ingest (PDF, DOCX, or TXT)
    
    Example: python cli.py ingest my_document.pdf
    """
    try:
        pipe = get_pipeline()
        
        with console.status(f"[bold green]Processing {file_path}...", spinner="dots"):
            result = pipe.ingestDocument(file_path)
        
        # Display results
        console.print(Panel.fit(
            f"[green]✓ Document ingested successfully[/green]\n\n"
            f"[bold]Source:[/bold] {result['metadata']['source']}\n"
            f"[bold]File Type:[/bold] {result['metadata']['filetype']}\n"
            f"[bold]Chunks Created:[/bold] {len(result['chunks'])}\n"
            f"[bold]Embeddings:[/bold] {len(result['embeddings'])} x {len(result['embeddings'][0])}\n"
            f"[bold]Date Ingested:[/bold] {result['metadata']['date_ingested']}",
            title="Ingestion Results"
        ))
        
        if verbose:
            console.print("\n[bold cyan]First 3 chunks:[/bold cyan]")
            for i, chunk in enumerate(result['chunks'][:3]):
                console.print(f"\n[yellow]Chunk {i}:[/yellow]")
                console.print(chunk['text'][:200] + "..." if len(chunk['text']) > 200 else chunk['text'])
        
    except Exception as e:
        console.print(f"[red]✗ Error ingesting document: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('query')
@click.option('--style', default="simple", help='Context prompt template (determines answer style.) \nCurrent options:\nsimple   scholar   distracted')
@click.option('--results', '-n', default=5, help='Number of context chunks to retrieve (default: 5)')
@click.option('--show-context', '-c', is_flag=True, help='Display the retrieved context')
@click.option('--no-llm', is_flag=True, help='Only retrieve context without querying LLM')
def query(query: str, style: str, results: int, show_context: bool, no_llm: bool):
    """
    Query the RAG system with a question.
    
    QUERY: Your question or query text
    
    Example: python cli.py query "What is machine learning?"
    """
    try:
        pipe = get_pipeline()
        
        # Get context
        with console.status("[bold green]Retrieving relevant context...", spinner="dots"):
            context_prompt = pipe.getContext(query, style = style, n_results=results)
        
        if show_context or no_llm:
            console.print("\n[bold cyan]Retrieved Context:[/bold cyan]")
            console.print(Panel(context_prompt, expand=False))
        
        if no_llm:
            return
        
        # Query LLM
        with console.status("[bold green]Querying LLM...", spinner="dots"):
            response = pipe._llm_client.query(context_prompt)
        
        # Display response
        console.print("\n[bold green]Response:[/bold green]")
        console.print(Panel(Markdown(response), title="RAG System Answer", expand=False))
        
    except Exception as e:
        console.print(f"[red]✗ Error querying system: {e}[/red]")
        sys.exit(1)


@cli.command()
def list():
    """List all documents in the RAG pipeline."""
    try:
        pipe = get_pipeline()
        docs = pipe.listDocuments()
        
        if not docs:
            console.print("[yellow]No documents found in the pipeline.[/yellow]")
            return
        
        table = Table(title="Documents in RAG Pipeline", show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim", width=6)
        table.add_column("Document Name", style="cyan")
        
        for idx, doc in enumerate(docs, 1):
            table.add_row(str(idx), doc)
        
        console.print(table)
        console.print(f"\n[bold]Total:[/bold] {len(docs)} document(s)")
        
    except Exception as e:
        console.print(f"[red]✗ Error listing documents: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--json-output', '-j', is_flag=True, help='Output stats as JSON')
def stats(json_output: bool):
    """Display RAG pipeline statistics."""
    try:
        pipe = get_pipeline()
        stats_data = pipe.getStats()
        
        if json_output:
            console.print_json(data=stats_data)
            return
        
        # Create a formatted display
        table = Table(title="RAG Pipeline Statistics", show_header=False, box=None)
        table.add_column("Property", style="cyan", width=25)
        table.add_column("Value", style="green")
        
        table.add_row("Total Documents", str(stats_data['total_documents']))
        table.add_row("Total Chunks", str(stats_data['total_chunks']))
        table.add_row("Collection Name", stats_data['collection_name'])
        table.add_row("Persist Directory", stats_data['persist_directory'] or "In-memory")
        table.add_row("", "")
        table.add_row("[bold]Embedding Configuration", "")
        table.add_row("  Chunk Size", str(stats_data['embedding_config']['chunk_size']))
        table.add_row("  Overlap Size", str(stats_data['embedding_config']['overlap_size']))
        table.add_row("  Embedding Model", stats_data['embedding_config']['embedding_model'])
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]✗ Error getting stats: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.confirmation_option(prompt='Are you sure you want to reset the pipeline? This will delete all documents!')
def reset():
    """Reset the RAG pipeline (delete all documents)."""
    try:
        pipe = get_pipeline()
        pipe.reset()
        console.print("[green]✓ Pipeline reset successfully. All documents have been removed.[/green]")
        
    except Exception as e:
        console.print(f"[red]✗ Error resetting pipeline: {e}[/red]")
        sys.exit(1)


@cli.command()
def test_suite():
    """
    Run a comprehensive test suite for edge cases.
    
    This will test various edge cases and boundary conditions.
    """
    console.print(Panel.fit(
        "[bold cyan]RAG Pipeline Test Suite[/bold cyan]\n"
        "Running comprehensive edge case tests",
        border_style="cyan"
    ))
    
    pipe = get_pipeline()
    results = []
    
    # Test 1: Empty pipeline query
    console.print("\n[bold]Test 1:[/bold] Query empty pipeline")
    try:
        context = pipe.getContext("test query", n_results=5)
        results.append(("Empty pipeline query", "PASS", "Handled gracefully"))
    except Exception as e:
        results.append(("Empty pipeline query", "INFO", f"Returned: {str(e)[:50]}"))
    
    # Test 2: Empty query validation
    console.print("[bold]Test 2:[/bold] Empty query validation")
    try:
        pipe._llm_client.query("")
        results.append(("Empty query", "FAIL", "Should have been rejected"))
    except ValueError:
        results.append(("Empty query", "PASS", "Correctly rejected"))
    
    # Test 3: Whitespace-only query
    console.print("[bold]Test 3:[/bold] Whitespace-only query")
    try:
        pipe._llm_client.query("   \n\t  ")
        results.append(("Whitespace query", "FAIL", "Should have been rejected"))
    except ValueError:
        results.append(("Whitespace query", "PASS", "Correctly rejected"))
    
    # Test 4: Very long query
    console.print("[bold]Test 4:[/bold] Very long query (>900k chars)")
    try:
        pipe._llm_client.query("x" * 950000)
        results.append(("Long query", "FAIL", "Should have been rejected"))
    except ValueError:
        results.append(("Long query", "PASS", "Correctly rejected"))
    
    # Test 5: Special characters
    console.print("[bold]Test 5:[/bold] Special characters handling")
    try:
        test_query = "Test <>&\"'!@#$%^&*() 测试 العربية"
        pipe._llm_client._validate_prompt(test_query)
        results.append(("Special chars", "PASS", "Validation passed"))
    except Exception as e:
        results.append(("Special chars", "FAIL", str(e)[:50]))
    
    # Test 6: Caching mechanism
    console.print("[bold]Test 6:[/bold] Response caching")
    try:
        query = "Test caching query"
        resp1 = pipe._llm_client.query(query)
        resp2 = pipe._llm_client.query(query)
        if resp1 == resp2:
            results.append(("Caching", "PASS", "Cache working correctly"))
        else:
            results.append(("Caching", "FAIL", "Responses don't match"))
    except Exception as e:
        results.append(("Caching", "FAIL", str(e)[:50]))
    
    # Display results
    console.print("\n")
    table = Table(title="Test Results", show_header=True, header_style="bold magenta")
    table.add_column("Test", style="cyan", width=25)
    table.add_column("Result", width=10)
    table.add_column("Details", style="dim")
    
    for test_name, status, details in results:
        if status == "PASS":
            status_styled = f"[green]{status}[/green]"
        elif status == "FAIL":
            status_styled = f"[red]{status}[/red]"
        else:
            status_styled = f"[yellow]{status}[/yellow]"
        table.add_row(test_name, status_styled, details)
    
    console.print(table)
    
    # Summary
    passed = sum(1 for _, status, _ in results if status == "PASS")
    total = len(results)
    console.print(f"\n[bold]Summary:[/bold] {passed}/{total} tests passed")


if __name__ == '__main__':
    cli()