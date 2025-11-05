# Project Context

## Purpose
PageIndex is a reasoning-based RAG (Retrieval-Augmented Generation) system that creates hierarchical tree structures from long documents without using vector databases or chunking. It simulates how human experts navigate complex documents through tree search, enabling LLMs to reason about document relevance rather than relying on semantic similarity. The system achieves 98.7% accuracy on FinanceBench and is designed for professional documents like financial reports, regulatory filings, academic textbooks, and legal manuals.

## Tech Stack
- **Python 3.x** - Primary programming language
- **OpenAI API** - LLM model integration (GPT-4o)
- **PyMuPDF** - PDF text extraction
- **PyPDF2** - Alternative PDF processing
- **tiktoken** - Token counting for text processing
- **python-dotenv** - Environment variable management
- **PyYAML** - Configuration file management
- **asyncio** - Asynchronous processing for API calls

## Project Conventions

### Code Style
- Python standard conventions (PEP 8)
- Async/await patterns for OpenAI API calls
- Configuration-driven approach using YAML config files
- Modular architecture with separate modules for PDF and Markdown processing

### Architecture Patterns
- **Tree-based indexing**: Documents are organized into hierarchical tree structures
- **Reasoning-based retrieval**: Uses LLM reasoning instead of vector similarity
- **Async processing**: Concurrent API calls for efficiency
- **Configuration management**: Centralized config system with YAML files
- **Separate modules**: `page_index.py` for PDFs, `page_index_md.py` for Markdown

### Testing Strategy
- Test documents located in `tests/pdfs/` directory
- Generated tree structures saved in `tests/results/` directory
- JSON format for structured output validation
- Manual testing through command-line interface

### Git Workflow
- Main branch for stable releases
- Conventional commit messages following the project's existing patterns
- Clean working directory expected before new changes

## Domain Context
**Document Processing & RAG Systems**: This project operates in the domain of document analysis and retrieval systems. Key concepts include:
- **Tree indexing**: Creating hierarchical document structures similar to table of contents
- **Reasoning-based RAG**: Using LLM reasoning to find relevant content instead of semantic similarity
- **Document navigation**: Simulating human expert document traversal patterns
- **Professional document analysis**: Focused on financial, legal, academic, and technical documents

## Important Constraints
- **No vector databases**: Intentionally avoids traditional vector-based retrieval
- **No document chunking**: Preserves natural document structure
- **OpenAI API dependency**: Requires valid API key and internet connectivity
- **Token limits**: Configurable token limits per node (default: 20,000 tokens)
- **Page limits**: Configurable page limits per node (default: 10 pages)
- **Context preservation**: Maintains document hierarchy and relationships

## External Dependencies
- **OpenAI API**: Primary LLM service for reasoning and document analysis
- **Environment variables**: `.env` file with `CHATGPT_API_KEY` configuration
- **File system**: Local file access for PDF/Markdown input and JSON output
- **Configuration files**: `pageindex/config.yaml` for default settings
