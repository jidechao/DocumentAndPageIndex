# Tree Search Feature Design

## Architecture Overview

### Components
1. **TreeSearch Class** - Core logic for node analysis and selection
2. **NodeAnalyzer** - LLM-based node relevance evaluation
3. **TreeSearchResult** - Structured output containing relevant nodes
4. **Integration Layer** - Connects with existing cross-document search

### Data Flow
```
User Query → Document Search → Document IDs → Tree Search → Relevant Nodes → Final Results
```

## Detailed Design

### TreeSearch Class
```python
class TreeSearch:
    def __init__(self, model: str = "gpt-4o-2024-11-20")

    async def search_nodes(
        self,
        query: str,
        document_ids: List[str],
        max_nodes_per_doc: int = 5
    ) -> List[TreeSearchResult]

    async def analyze_document_nodes(
        self,
        query: str,
        document: DocumentMetadata,
        tree_structure: Dict
    ) -> List[NodeResult]
```

### Node Selection Strategy
Based on the tutorial examples, implement LLM-based reasoning:

**Prompt Template:**
```python
prompt = f"""
You are given a query and the tree structure of a document.
You need to find all nodes that are likely to contain the answer.

Query: {query}
Document tree structure: {tree_structure}

Reply in the following JSON format:
{{
  "thinking": <your reasoning about which nodes are relevant>,
  "node_list": [node_id1, node_id2, ...]
}}
"""
```

### TreeSearchResult Structure
```python
@dataclass
class TreeSearchResult:
    document_id: str
    document_name: str
    relevant_nodes: List[NodeResult]
    search_confidence: float

@dataclass
class NodeResult:
    node_id: str
    node_title: str
    node_path: List[str]
    relevance_score: float
    reasoning: str
    content_preview: str
```

## Integration Points

### With CrossDocumentIndex
- Extend `search()` method to include node analysis
- Add optional `include_nodes: bool = True` parameter
- Return enhanced results with node information

### CLI Integration
- Add `--include-nodes` flag to existing search commands
- Provide verbose output showing node paths and relevance

### API Integration
- New endpoint for node-level search
- Backward compatibility with existing search endpoints

## Performance Considerations

### Batch Processing
- Process multiple documents concurrently
- Implement rate limiting for API calls
- Cache tree structures when possible

### Token Management
- Limit tree structure size sent to LLM
- Implement chunking for large trees
- Monitor token usage per query

## Error Handling

### Tree Loading Errors
- Handle missing or corrupted tree files
- Provide fallback to document-level results
- Log warnings for debugging

### LLM API Errors
- Implement retry logic with exponential backoff
- Provide graceful degradation
- Maintain partial results when possible

### Invalid Responses
- Validate JSON structure from LLM
- Handle malformed node IDs
- Provide default relevance scores

## Configuration

### New Config Options
```yaml
tree_search:
  max_nodes_per_document: 5
  min_relevance_score: 0.3
  include_content_preview: true
  preview_max_length: 200
  batch_size: 3
```

### Model Selection
- Support different models for node analysis
- Allow model switching per query
- Fallback models for reliability

## Testing Strategy

### Unit Tests
- Test node selection logic
- Validate prompt engineering
- Test result structure generation

### Integration Tests
- Test with real document trees
- Validate cross-document search integration
- Test CLI and API interfaces

### Performance Tests
- Benchmark with large document sets
- Test concurrent processing
- Validate memory usage

## Future Enhancements

### Advanced Features
- Implement MCTS (Monte Carlo Tree Search) as mentioned in tutorial
- Add user preference integration
- Support for custom node selection criteria

### Optimization
- Implement vector-based pre-filtering
- Add result caching
- Optimize tree structure transmission