# Project CLAUDE.md

This file provides guidance to Kiro Code  when working with code in this repository.

## Project Overview

**PageIndex** is a reasoning-based, vectorless RAG (Retrieval-Augmented Generation) system that processes long documents by generating hierarchical tree structures instead of using traditional vector databases and chunking. The system simulates how human experts navigate complex documents through tree search and reasoning.

### Core Architecture

- **Main Entry Point**: `run_pageindex.py` - CLI interface for processing PDF and Markdown files
- **Core Processing**: `pageindex/page_index.py` - PDF processing pipeline with TOC extraction and tree construction
- **Markdown Support**: `pageindex/page_index_md.py` - Markdown processing with header-based tree generation
- **Utilities**: `pageindex/utils.py` - OpenAI API integration, token counting, PDF text extraction, configuration management
- **Configuration**: `pageindex/config.yaml` - Default parameters for processing

### Key Processing Pipeline

1. **Document Input**: PDF or Markdown files
2. **Text Extraction**: Uses PyMuFit and PyPDF2 for PDF processing
3. **TOC Detection**: Analyzes document structure to identify table of contents
4. **Tree Generation**: Creates hierarchical structure with titles, summaries, and page indices
5. **Output**: JSON structure with document tree metadata

### Dependencies

- `openai==1.101.0` - LLM API integration
- `pymupdf==1.26.4` - PDF text extraction
- `PyPDF2==3.0.1` - Alternative PDF processing
- `tiktoken==0.11.0` - Token counting
- `pyyaml==6.0.2` - Configuration management
- `python-dotenv==1.1.0` - Environment variables

## Common Development Commands

### Setup Environment
```bash
pip3 install --upgrade -r requirements.txt
```

### Set API Key
Create `.env` file:
```bash
CHATGPT_API_KEY=your_openai_key_here
```

### Process PDF Documents
```bash
# Basic usage
python3 run_pageindex.py --pdf_path /path/to/document.pdf

# With custom parameters
python3 run_pageindex.py --pdf_path document.pdf \
    --model gpt-4o-2024-11-20 \
    --toc-check-pages 20 \
    --max-pages-per-node 10 \
    --max-tokens-per-node 20000 \
    --if-add-node-summary yes \
    --if-add-node-id yes
```

### Process Markdown Documents
```bash
# Basic usage
python3 run_pageindex.py --md_path /path/to/document.md

# With tree thinning for large documents
python3 run_pageindex.py --md_path document.md \
    --if-thinning yes \
    --thinning-threshold 5000 \
    --summary-token-threshold 200
```

### Output Structure
Results are saved to `./results/` directory as `filename_structure.json` containing:
- Document metadata
- Hierarchical tree structure with node IDs
- Page indices and content summaries
- Optional text content and descriptions

## Configuration Management

The system uses `pageindex/config.yaml` for defaults:
- `model`: OpenAI model to use (default: gpt-4o-2024-11-20)
- `max_page_num_each_node`: Maximum pages per tree node (default: 10)
- `max_token_num_each_node`: Maximum tokens per node (default: 20000)
- `if_add_node_id`: Include node IDs (default: "yes")
- `if_add_node_summary`: Include node summaries (default: "yes")

## Testing and Examples

### Example Notebooks
- `cookbook/pageindex_RAG_simple.ipynb` - Basic vectorless RAG example
- `cookbook/vision_RAG_pageindex.ipynb` - Vision-based retrieval without OCR

### Test Documents
- `tests/pdfs/` - Sample PDF files for testing
- `tests/results/` - Expected output structures for validation

## Key Implementation Details

### PDF Processing Flow
1. Extract text using PyMuFit for better formatting preservation
2. Detect and parse table of contents from early pages
3. Match TOC entries to actual document content through LLM reasoning
4. Build hierarchical tree structure with parent-child relationships
5. Validate page mappings through concurrent API calls

### Markdown Processing Flow
1. Parse headers using `#`, `##`, `###` hierarchy
2. Build tree structure from header levels
3. Optional tree thinning for large documents
4. Generate summaries for each node using LLM

### Async Processing
The system heavily uses async/await patterns for concurrent API calls to improve performance when processing multiple document sections simultaneously.

### Error Handling
- Implements retry logic for OpenAI API calls (max 10 retries)
- Bounds checking for page array access
- Graceful fallback between PDF parsing libraries

## API Integration

The system requires OpenAI API integration for:
- Document structure analysis
- TOC entry validation
- Content summarization
- Title matching and verification

The OpenAI API key should be set as `CHATGPT_API_KEY` environment variable.