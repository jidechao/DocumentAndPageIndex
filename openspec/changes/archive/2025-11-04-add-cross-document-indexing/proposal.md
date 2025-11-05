## Why
The current PageIndex system processes individual documents and creates tree structures for each document separately. However, users often need to search across multiple documents simultaneously to find relevant information across a document collection. The reference document shows a lightweight approach using LLM-generated descriptions for document selection, but this should be integrated into the core PageIndex system for a seamless cross-document search experience.

## What Changes
- Add cross-document indexing module that creates a unified index across multiple PageIndex trees
- Implement document description generation based on PageIndex tree structures
- Add LLM-based document selection functionality for cross-document queries
- Create unified search API that works across multiple documents
- Add cross-document retrieval methods that integrate with existing PageIndex workflow

## Impact
- Affected specs: New capability `cross-document-indexing`
- Affected code: New module `pageindex/cross_document_index.py`, modifications to `run_pageindex.py`
- New API endpoints for multi-document search and document collection management