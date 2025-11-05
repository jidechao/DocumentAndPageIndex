"""
Tree Search functionality for PageIndex
Automatically locates relevant nodes within document trees based on search queries.
"""

import os
import json
import asyncio
import logging
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from .utils import ChatGPT_API_async, extract_json, ConfigLoader


@dataclass
class NodeResult:
    """Represents a single node result from tree search"""
    node_id: str
    node_title: str
    node_path: List[str]
    relevance_score: float
    reasoning: str
    content_preview: str
    text: str = ""


@dataclass
class TreeSearchResult:
    """Represents tree search results for a single document"""
    document_id: str
    document_name: str
    relevant_nodes: List[NodeResult]
    search_confidence: float
    total_nodes_analyzed: int
    processing_time: float


class NodeAnalyzer:
    """Handles LLM-based node relevance evaluation"""

    def __init__(self, model: str = None, config: Optional[Dict] = None):
        from .utils import ConfigLoader
        config_loader = ConfigLoader()
        config_data = config_loader.load()
        
        # Use provided model, or get from config, or default to Qwen
        if model is None:
            model = getattr(config_data, 'model', 'Qwen/Qwen3-235B-A22B-Instruct-2507')
        
        self.model = model
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.max_retries = self.config.get('max_retries', 3)
        self.retry_delay = self.config.get('retry_delay', 1.0)

    async def analyze_nodes(self, query: str, tree_structure: Dict[str, Any],
                          max_nodes: int = 5) -> List[NodeResult]:
        """
        Analyze tree structure to find relevant nodes for the query

        Args:
            query: User's search query
            tree_structure: Document tree structure from PageIndex
            max_nodes: Maximum number of nodes to return

        Returns:
            List of relevant nodes with scores and reasoning
        """
        try:
            # Create the LLM prompt based on tutorial examples
            prompt = self._create_node_selection_prompt(query, tree_structure)

            # Call LLM with retry logic
            response = await self._call_llm_with_retry(prompt)

            # Parse and validate response
            node_ids = self._parse_llm_response(response)

            # Convert node IDs to NodeResult objects
            nodes = self._create_node_results(node_ids, tree_structure)

            # Limit to max_nodes and sort by relevance
            return nodes[:max_nodes]

        except Exception as e:
            self.logger.error(f"Error analyzing nodes: {e}")
            return []

    def _create_node_selection_prompt(self, query: str, tree_structure: Dict[str, Any]) -> str:
        """Create LLM prompt for node selection"""
        return f"""
You are given a query and the tree structure of a document.
You need to find all nodes that are likely to contain the answer.

Query: {query}

Document tree structure: {json.dumps(tree_structure, ensure_ascii=False, indent=2)}

Reply in the following JSON format:
{{
  "thinking": <your reasoning about which nodes are relevant>,
  "node_list": [node_id1, node_id2, ...]
}}

Directly return the final JSON structure. Do not output anything else."""

    async def _call_llm_with_retry(self, prompt: str) -> str:
        """Call LLM with exponential backoff retry logic"""
        for attempt in range(self.max_retries):
            try:
                response = await ChatGPT_API_async(model=self.model, prompt=prompt)
                return response
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise e

                wait_time = self.retry_delay * (2 ** attempt)
                self.logger.warning(f"LLM call failed (attempt {attempt + 1}), retrying in {wait_time}s: {e}")
                await asyncio.sleep(wait_time)

    def _parse_llm_response(self, response: str) -> List[str]:
        """Parse LLM response and extract node IDs"""
        try:
            parsed = extract_json(response)
            if 'node_list' in parsed and isinstance(parsed['node_list'], list):
                return parsed['node_list']
            else:
                self.logger.warning(f"Invalid response format: {parsed}")
                return []
        except Exception as e:
            self.logger.error(f"Error parsing LLM response: {e}")
            return []

    def _create_node_results(self, node_ids: List[str], tree_structure: Dict[str, Any]) -> List[NodeResult]:
        """Convert node IDs to NodeResult objects with full metadata"""
        nodes = []
        node_map = self._build_node_map(tree_structure)

        for node_id in node_ids:
            if node_id in node_map:
                node_info = node_map[node_id]
                
                # Ensure node_path is a list
                node_path = node_info.get('path', [])
 
                if not isinstance(node_path, list):
                    node_path = [str(node_path)] if node_path else []
                
                # Debug summary field
                summary = node_info.get('summary', '')

                
                # Ensure summary is a string before slicing
                summary_str = str(summary) if summary is not None else ''
                content_preview = (summary_str[:200] + "...") if summary_str else ""
                
                # Debug text field
                text = node_info.get('text', '')
   
                
                node = NodeResult(
                    node_id=node_id,
                    node_title=node_info.get('title', ''),
                    node_path=node_path,
                    relevance_score=0.8,  # Default score, could be enhanced
                    reasoning="Selected by LLM as relevant to query",
                    content_preview=content_preview,
                    text=str(text) if text is not None else ''
                )
                nodes.append(node)

        return nodes

    def _build_node_map(self, tree_structure: Dict[str, Any], prefix: str = "") -> Dict[str, Dict]:
        """Build a map of node_id -> node_info for easy lookup"""
        node_map = {}

        # Handle both nested tree structure and flat structure
        if 'structure' in tree_structure:
            # Handle flat structure (list of nodes) - including nested nodes
            def traverse_structure_nodes(nodes, path=[]):
                for node in nodes:
                    node_id = node.get('node_id', f"node_{len(node_map)}")
                    current_path = path + [node.get('title', '')]

                    node_map[node_id] = {
                        'title': node.get('title', ''),
                        'path': current_path,
                        'summary': node.get('summary', ''),
                        'content': node.get('content', ''),
                        'text': node.get('text', '')
                    }

                    # Recursively process nested 'nodes' if they exist
                    if 'nodes' in node and isinstance(node.get('nodes'), list):
                        traverse_structure_nodes(node['nodes'], current_path)

            traverse_structure_nodes(tree_structure['structure'])

        elif 'nodes' in tree_structure:
            # Handle nested tree structure
            def traverse_nodes(nodes, path=[]):
                for node in nodes:
                    node_id = node.get('node_id', f"node_{len(node_map)}")
                    current_path = path + [node.get('title', '')]

                    node_map[node_id] = {
                        'title': node.get('title', ''),
                        'path': current_path,
                        'summary': node.get('summary', ''),
                        'content': node.get('content', ''),
                        'text': node.get('text', '')
                    }

                    # Recursively process children
                    if 'children' in node:
                        traverse_nodes(node['children'], current_path)

            traverse_nodes(tree_structure['nodes'])

        return node_map


class TreeSearch:
    """Main Tree Search class for automated node discovery"""

    def __init__(self, model: str = None, config_path: Optional[str] = None):
        from .utils import ConfigLoader
        config_loader = ConfigLoader()
        config_data = config_loader.load()
        
        # Use provided model, or get from config, or default to Qwen
        if model is None:
            model = getattr(config_data, 'model', 'Qwen/Qwen3-235B-A22B-Instruct-2507')
        
        self.model = model
        self.config = self._load_config(config_path)
        self.node_analyzer = NodeAnalyzer(model=model, config=self.config)
        self.logger = logging.getLogger(__name__)
        self._tree_cache = {}  # Simple cache for tree structures

    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Load configuration from file or use defaults"""
        default_config = {
            'max_nodes_per_document': 5,
            'min_relevance_score': 0.3,
            'include_content_preview': True,
            'preview_max_length': 200,
            'batch_size': 3,
            'cache_enabled': True,
            'max_retries': 3,
            'retry_delay': 1.0
        }

        if config_path and os.path.exists(config_path):
            try:
                config_loader = ConfigLoader(config_path)
                tree_search_config = config_loader.get('tree_search', {})
                default_config.update(tree_search_config)
            except Exception as e:
                self.logger.warning(f"Error loading config from {config_path}: {e}, using defaults")

        return default_config

    async def search_nodes(self, query: str, document_ids: List[str],
                          document_metadata: Dict[str, Any],
                          max_nodes_per_doc: Optional[int] = None) -> List[TreeSearchResult]:
        """
        Search for relevant nodes across multiple documents

        Args:
            query: User's search query
            document_ids: List of document IDs to search
            document_metadata: Mapping of document_id -> DocumentMetadata
            max_nodes_per_doc: Override config for max nodes per document

        Returns:
            List of TreeSearchResult objects
        """
        start_time = time.time()
        max_nodes = max_nodes_per_doc or self.config.get('max_nodes_per_document', 5)

        # Process documents concurrently
        tasks = []
        for doc_id in document_ids:
            if doc_id in document_metadata:
                task = self._analyze_document(query, doc_id, document_metadata[doc_id], max_nodes)
                tasks.append(task)

        if not tasks:
            self.logger.warning("No valid documents to analyze")
            return []

        # Execute tasks concurrently
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Filter out exceptions and collect valid results
            valid_results = []
            for result in results:
                if isinstance(result, Exception):
                    self.logger.error(f"Error processing document: {result}")
                elif isinstance(result, TreeSearchResult):
                    valid_results.append(result)

            processing_time = time.time() - start_time
            self.logger.info(f"Processed {len(valid_results)} documents in {processing_time:.2f}s")

            return valid_results

        except Exception as e:
            self.logger.error(f"Error in concurrent processing: {e}")
            return []

    async def _analyze_document(self, query: str, document_id: str,
                              document_metadata: Any, max_nodes: int) -> TreeSearchResult:
        """Analyze a single document for relevant nodes"""
        start_time = time.time()

        try:
            # Load tree structure
            tree_structure = await self._load_tree_structure(document_metadata)

            if not tree_structure:
                return TreeSearchResult(
                    document_id=document_id,
                    document_name=getattr(document_metadata, 'filename', document_id),
                    relevant_nodes=[],
                    search_confidence=0.0,
                    total_nodes_analyzed=0,
                    processing_time=time.time() - start_time
                )

            # Analyze nodes
            nodes = await self.node_analyzer.analyze_nodes(query, tree_structure, max_nodes)

            # Calculate confidence based on number of relevant nodes found
            confidence = min(len(nodes) / max_nodes, 1.0) if max_nodes > 0 else 0.0

            return TreeSearchResult(
                document_id=document_id,
                document_name=getattr(document_metadata, 'filename', document_id),
                relevant_nodes=nodes,
                search_confidence=confidence,
                total_nodes_analyzed=self._count_total_nodes(tree_structure),
                processing_time=time.time() - start_time
            )

        except Exception as e:
            self.logger.error(f"Error analyzing document {document_id}: {e}")
            return TreeSearchResult(
                document_id=document_id,
                document_name=getattr(document_metadata, 'filename', document_id),
                relevant_nodes=[],
                search_confidence=0.0,
                total_nodes_analyzed=0,
                processing_time=time.time() - start_time
            )

    async def _load_tree_structure(self, document_metadata: Any) -> Optional[Dict[str, Any]]:
        """Load tree structure for a document"""
        try:
            # Check cache first
            if self.config.get('cache_enabled', True):
                doc_id = getattr(document_metadata, 'doc_id', str(document_metadata))
                if doc_id in self._tree_cache:
                    return self._tree_cache[doc_id]

            # Load from file
            tree_path = getattr(document_metadata, 'tree_path', None)
            if not tree_path or not os.path.exists(tree_path):
                self.logger.warning(f"Tree file not found for document: {getattr(document_metadata, 'filename', 'unknown')}")
                return None

            with open(tree_path, 'r', encoding='utf-8') as f:
                tree_structure = json.load(f)

            # Cache the result
            if self.config.get('cache_enabled', True):
                doc_id = getattr(document_metadata, 'doc_id', str(document_metadata))
                self._tree_cache[doc_id] = tree_structure

            return tree_structure

        except Exception as e:
            self.logger.error(f"Error loading tree structure: {e}")
            return None

    def _count_total_nodes(self, tree_structure: Dict[str, Any]) -> int:
        """Count total nodes in tree structure"""
        def count_nodes(nodes):
            count = len(nodes)
            for node in nodes:
                if 'children' in node:
                    count += count_nodes(node['children'])
            return count

        if 'nodes' in tree_structure:
            return count_nodes(tree_structure['nodes'])
        return 0

    def clear_cache(self):
        """Clear the tree structure cache"""
        self._tree_cache.clear()
        self.logger.info("Tree cache cleared")
