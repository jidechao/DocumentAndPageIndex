"""
Tests for Tree Search functionality
"""

import pytest
import asyncio
import json
import os
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import asdict

# Add the parent directory to the path so we can import pageindex modules
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from pageindex.tree_search import TreeSearch, NodeAnalyzer, NodeResult, TreeSearchResult
from pageindex.cross_document_index import DocumentMetadata


class TestNodeAnalyzer:
    """Test cases for NodeAnalyzer class"""

    @pytest.fixture
    def analyzer(self):
        """Create a NodeAnalyzer instance for testing"""
        config = {
            'max_retries': 2,
            'retry_delay': 0.1
        }
        return NodeAnalyzer(model="gpt-4o", config=config)

    @pytest.fixture
    def sample_tree_structure(self):
        """Sample tree structure for testing"""
        return {
            "title": "Test Document",
            "nodes": [
                {
                    "node_id": "node_1",
                    "title": "Introduction",
                    "summary": "This is the introduction section",
                    "content": "Introduction content here...",
                    "children": [
                        {
                            "node_id": "node_1_1",
                            "title": "Background",
                            "summary": "Background information",
                            "content": "Background content..."
                        }
                    ]
                },
                {
                    "node_id": "node_2",
                    "title": "Financial Analysis",
                    "summary": "Financial data and analysis",
                    "content": "Financial analysis content..."
                }
            ]
        }

    @pytest.mark.asyncio
    async def test_analyze_nodes_success(self, analyzer, sample_tree_structure):
        """Test successful node analysis"""
        # Mock the LLM response
        mock_response = json.dumps({
            "thinking": "The query asks about financial information, so the Financial Analysis node is most relevant",
            "node_list": ["node_2"]
        })

        with patch('pageindex.tree_search.ChatGPT_API_async', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_response

            result = await analyzer.analyze_nodes("financial information", sample_tree_structure, max_nodes=5)

            assert len(result) == 1
            assert result[0].node_id == "node_2"
            assert result[0].node_title == "Financial Analysis"
            assert result[0].relevance_score > 0

    @pytest.mark.asyncio
    async def test_analyze_nodes_invalid_response(self, analyzer, sample_tree_structure):
        """Test handling of invalid LLM response"""
        mock_response = "Invalid JSON response"

        with patch('pageindex.tree_search.ChatGPT_API_async', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_response

            result = await analyzer.analyze_nodes("test query", sample_tree_structure)

            assert len(result) == 0  # Should return empty list on invalid response

    def test_build_node_map(self, analyzer, sample_tree_structure):
        """Test node map building functionality"""
        node_map = analyzer._build_node_map(sample_tree_structure)

        assert "node_1" in node_map
        assert "node_2" in node_map
        assert "node_1_1" in node_map

        assert node_map["node_1"]["title"] == "Introduction"
        assert node_map["node_2"]["title"] == "Financial Analysis"
        assert node_map["node_1_1"]["title"] == "Background"


class TestTreeSearch:
    """Test cases for TreeSearch class"""

    @pytest.fixture
    def tree_search(self):
        """Create a TreeSearch instance for testing"""
        config = {
            'max_nodes_per_document': 3,
            'cache_enabled': False  # Disable caching for tests
        }
        return TreeSearch(model="gpt-4o", config_path=None)

    @pytest.fixture
    def sample_document_metadata(self):
        """Sample document metadata for testing"""
        return DocumentMetadata(
            doc_id="doc_1",
            filename="test_document.pdf",
            filepath="/path/to/test_document.pdf",
            description="A test document about financial analysis",
            tree_structure={
                "title": "Test Document",
                "nodes": [
                    {
                        "node_id": "node_1",
                        "title": "Financial Overview",
                        "summary": "Financial overview section"
                    }
                ]
            },
            created_at="2024-01-01T00:00:00Z",
            file_type="pdf",
            file_size=1024,
            tree_path="/path/to/tree_structure.json"
        )

    @pytest.mark.asyncio
    async def test_search_nodes_success(self, tree_search, sample_document_metadata):
        """Test successful node search across documents"""
        # Mock the NodeAnalyzer
        mock_node_result = NodeResult(
            node_id="node_1",
            node_title="Financial Overview",
            node_path=["Financial Overview"],
            relevance_score=0.9,
            reasoning="Relevant to financial query",
            content_preview="Financial overview content..."
        )

        with patch.object(tree_search.node_analyzer, 'analyze_nodes', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = [mock_node_result]

            with patch.object(tree_search, '_load_tree_structure', new_callable=AsyncMock) as mock_load:
                mock_load.return_value = sample_document_metadata.tree_structure

                results = await tree_search.search_nodes(
                    query="financial information",
                    document_ids=["doc_1"],
                    document_metadata={"doc_1": sample_document_metadata},
                    max_nodes_per_doc=5
                )

                assert len(results) == 1
                assert isinstance(results[0], TreeSearchResult)
                assert results[0].document_id == "doc_1"
                assert len(results[0].relevant_nodes) == 1
                assert results[0].relevant_nodes[0].node_id == "node_1"

    @pytest.mark.asyncio
    async def test_search_nodes_missing_tree(self, tree_search, sample_document_metadata):
        """Test handling of missing tree structure"""
        with patch.object(tree_search, '_load_tree_structure', new_callable=AsyncMock) as mock_load:
            mock_load.return_value = None  # Missing tree

            results = await tree_search.search_nodes(
                query="test query",
                document_ids=["doc_1"],
                document_metadata={"doc_1": sample_document_metadata},
                max_nodes_per_doc=5
            )

            assert len(results) == 1
            assert results[0].document_id == "doc_1"
            assert len(results[0].relevant_nodes) == 0  # No nodes found
            assert results[0].search_confidence == 0.0

    def test_count_total_nodes(self, tree_search):
        """Test node counting functionality"""
        tree_structure = {
            "nodes": [
                {"node_id": "node_1"},
                {
                    "node_id": "node_2",
                    "children": [
                        {"node_id": "node_2_1"},
                        {"node_id": "node_2_2"}
                    ]
                }
            ]
        }

        count = tree_search._count_total_nodes(tree_structure)
        assert count == 4  # node_1, node_2, node_2_1, node_2_2


class TestIntegration:
    """Integration tests for Tree Search functionality"""

    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self):
        """Test end-to-end workflow with mocked components"""
        # This would be a more comprehensive test
        # For now, we'll test the basic workflow structure

        # Create sample data
        tree_structure = {
            "title": "Financial Report",
            "nodes": [
                {
                    "node_id": "node_1",
                    "title": "Revenue",
                    "summary": "Revenue information"
                }
            ]
        }

        mock_response = json.dumps({
            "thinking": "The query asks about revenue",
            "node_list": ["node_1"]
        })

        # Test the complete workflow
        config = {
            'max_nodes_per_document': 5,
            'cache_enabled': False,
            'max_retries': 2,
            'retry_delay': 0.1
        }

        tree_search = TreeSearch(model="gpt-4o", config_path=None)
        tree_search.config = config

        with patch('pageindex.tree_search.ChatGPT_API_async', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_response

            analyzer = NodeAnalyzer(model="gpt-4o", config=config)
            nodes = await analyzer.analyze_nodes("revenue", tree_structure)

            assert len(nodes) == 1
            assert nodes[0].node_id == "node_1"


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])