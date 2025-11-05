## Context
The current PageIndex system creates hierarchical tree structures for individual documents. Users need to search across multiple documents to find relevant information across document collections. The reference implementation in `tutorials/doc-search/description.md` shows a manual approach using LLM-generated descriptions, but this should be integrated into the core system.

## Goals / Non-Goals
- Goals:
  - Seamless cross-document search functionality
  - Automatic document description generation
  - LLM-based document selection for queries
  - Integration with existing PageIndex workflow
- Non-Goals:
  - Vector-based similarity search (maintain reasoning-based approach)
  - Complex document clustering (focus on description-based selection)
  - Real-time document updates (batch processing approach)

## Decisions
- Decision: Use LLM-generated descriptions for document selection rather than vector similarity
  - Rationale: Maintains reasoning-based approach, works well with small-to-medium document collections
  - Alternatives considered: Vector embeddings, keyword matching, metadata-based filtering
- Decision: Extend existing PageIndex workflow rather than create separate system
  - Rationale: Leverages existing tree structures and retrieval capabilities
  - Alternatives considered: Standalone cross-document service, separate indexing pipeline

## Risks / Trade-offs
- Performance: LLM-based document selection adds latency compared to vector search
  - Mitigation: Cache descriptions, use streaming for large document sets
- Scalability: Description-based approach works best with small-to-medium document collections
  - Mitigation: Implement document batching, hierarchical filtering for large collections
- Cost: Additional OpenAI API calls for description generation and document selection
  - Mitigation: Batch processing, caching, configurable models

## Migration Plan
1. Add cross-document module alongside existing page_index.py
2. Extend run_pageindex.py with multi-document options
3. Add new API endpoints for cross-document search
4. Update configuration to support cross-document settings

## Open Questions
- Should document descriptions be stored persistently or generated on-demand?
- How to handle large document collections (>100 documents) efficiently?
- Should we support different description generation strategies?