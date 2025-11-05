import unittest
import asyncio
import tempfile
import os
import json
from unittest.mock import AsyncMock, MagicMock, patch
from pageindex.cross_document_index import (
    CrossDocumentIndex,
    DocumentDescriptor,
    DocumentSelector,
    CrossDocumentSearch,
    DocumentMetadata
)

class TestDocumentDescriptor(unittest.TestCase):
    """Test document description generation"""

    def setUp(self):
        self.descriptor = DocumentDescriptor(model="gpt-4o-2024-11-20")

    @patch('pageindex.cross_document_index.ChatGPT_API_async')
    async def test_generate_description_basic(self, mock_api):
        """Test basic description generation"""
        mock_api.return_value = "A comprehensive guide to financial regulations and compliance requirements."

        tree_structure = {
            'title': 'Financial Regulations Guide',
            'nodes': [
                {'title': 'Introduction', 'summary': 'Overview of financial regulations'},
                {'title': 'Compliance Requirements', 'summary': 'Detailed compliance guidelines'},
                {'title': 'Risk Management', 'summary': 'Risk assessment frameworks'}
            ]
        }

        description = await self.descriptor.generate_description(tree_structure)

        self.assertEqual(description, "A comprehensive guide to financial regulations and compliance requirements.")
        mock_api.assert_called_once()

    @patch('pageindex.cross_document_index.ChatGPT_API_async')
    async def test_generate_description_with_custom_requirements(self, mock_api):
        """Test description generation with custom requirements"""
        mock_api.return_value = "A technical manual for software engineers focusing on API integration patterns."

        tree_structure = {
            'title': 'API Integration Guide',
            'nodes': [
                {'title': 'REST APIs', 'summary': 'RESTful API design principles'},
                {'title': 'Authentication', 'summary': 'OAuth and token-based auth'}
            ]
        }

        custom_requirements = "Focus on technical implementation details for developers"
        description = await self.descriptor.generate_description(tree_structure, custom_requirements)

        self.assertIn("technical manual", description.lower())
        mock_api.assert_called_once()

    @patch('pageindex.cross_document_index.ChatGPT_API_async')
    async def test_generate_description_fallback(self, mock_api):
        """Test fallback behavior when API fails"""
        mock_api.side_effect = Exception("API Error")

        tree_structure = {
            'title': 'Test Document',
            'nodes': [
                {'title': 'Section 1', 'summary': 'Content 1'},
                {'title': 'Section 2', 'summary': 'Content 2'}
            ]
        }

        description = await self.descriptor.generate_description(tree_structure)

        # Should use fallback description
        self.assertIn("Test Document", description)
        self.assertIn("2", description)  # Number of sections

class TestDocumentSelector(unittest.TestCase):
    """Test document selection functionality"""

    def setUp(self):
        self.selector = DocumentSelector(model="gpt-4o-2024-11-20")

    @patch('pageindex.cross_document_index.ChatGPT_API_async')
    async def test_select_documents_success(self, mock_api):
        """Test successful document selection"""
        mock_api.return_value = '''{
            "thinking": "User is asking about financial regulations, so documents 1 and 3 are relevant",
            "answer": ["doc1", "doc3"]
        }'''

        documents = [
            DocumentMetadata(
                doc_id="doc1",
                filename="financial_guide.pdf",
                filepath="/path/to/financial_guide.pdf",
                description="A comprehensive guide to financial regulations",
                tree_structure={},
                created_at="2024-01-01T00:00:00",
                file_type="pdf",
                file_size=1000000,
                tree_path="/path/to/tree.json"
            ),
            DocumentMetadata(
                doc_id="doc2",
                filename="tech_manual.pdf",
                filepath="/path/to/tech_manual.pdf",
                description="Technical implementation guide",
                tree_structure={},
                created_at="2024-01-01T00:00:00",
                file_type="pdf",
                file_size=500000,
                tree_path="/path/to/tree2.json"
            ),
            DocumentMetadata(
                doc_id="doc3",
                filename="compliance_handbook.pdf",
                filepath="/path/to/compliance_handbook.pdf",
                description="Compliance requirements and best practices",
                tree_structure={},
                created_at="2024-01-01T00:00:00",
                file_type="pdf",
                file_size=750000,
                tree_path="/path/to/tree3.json"
            )
        ]

        selected_ids = await self.selector.select_documents("What are the financial compliance requirements?", documents)

        self.assertEqual(selected_ids, ["doc1", "doc3"])
        mock_api.assert_called_once()

    async def test_select_documents_empty_list(self):
        """Test selection with empty document list"""
        selected_ids = await self.selector.select_documents("test query", [])
        self.assertEqual(selected_ids, [])

    @patch('pageindex.cross_document_index.ChatGPT_API_async')
    async def test_select_documents_api_failure(self, mock_api):
        """Test selection when API fails"""
        mock_api.side_effect = Exception("API Error")

        documents = [
            DocumentMetadata(
                doc_id="doc1",
                filename="test.pdf",
                filepath="/path/to/test.pdf",
                description="Test document",
                tree_structure={},
                created_at="2024-01-01T00:00:00",
                file_type="pdf",
                file_size=100000,
                tree_path="/path/to/tree.json"
            )
        ]

        selected_ids = await self.selector.select_documents("test query", documents)
        self.assertEqual(selected_ids, [])

class TestCrossDocumentIndex(unittest.TestCase):
    """Test cross-document index management"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.index_path = os.path.join(self.temp_dir, "test_index.json")
        self.trees_dir = os.path.join(self.temp_dir, "trees")
        self.index = CrossDocumentIndex(index_path=self.index_path, model="gpt-4o-2024-11-20")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init_creates_directories(self):
        """Test that initialization creates necessary directories"""
        self.assertTrue(os.path.exists(os.path.dirname(self.index_path)))

    def test_generate_doc_id(self):
        """Test document ID generation"""
        # Create a temporary file
        temp_file = os.path.join(self.temp_dir, "test.txt")
        with open(temp_file, 'w') as f:
            f.write("test content")

        doc_id1 = self.index._generate_doc_id(temp_file)
        doc_id2 = self.index._generate_doc_id(temp_file)

        # Same file should generate same ID
        self.assertEqual(doc_id1, doc_id2)
        self.assertEqual(len(doc_id1), 12)  # MD5 hash truncated to 12 chars

    def test_add_remove_document_sync(self):
        """Test document addition and removal (synchronous parts)"""
        # Test document metadata creation
        doc = DocumentMetadata(
            doc_id="test123",
            filename="test.pdf",
            filepath="/path/to/test.pdf",
            description="Test document",
            tree_structure={"title": "Test"},
            created_at="2024-01-01T00:00:00",
            file_type="pdf",
            file_size=1000,
            tree_path="/path/to/tree.json"
        )

        # Add to index
        self.index.documents[doc.doc_id] = doc
        self.index._save_index()

        # Verify it was saved
        self.assertIn(doc.doc_id, self.index.documents)
        self.assertTrue(os.path.exists(self.index_path))

        # Remove from index
        result = self.index.remove_document(doc.doc_id)
        self.assertTrue(result)
        self.assertNotIn(doc.doc_id, self.index.documents)

    def test_list_documents(self):
        """Test listing documents"""
        # Add some test documents
        for i in range(3):
            doc = DocumentMetadata(
                doc_id=f"doc{i}",
                filename=f"test{i}.pdf",
                filepath=f"/path/to/test{i}.pdf",
                description=f"Test document {i}",
                tree_structure={},
                created_at="2024-01-01T00:00:00",
                file_type="pdf",
                file_size=1000,
                tree_path=f"/path/to/tree{i}.json"
            )
            self.index.documents[doc.doc_id] = doc

        docs = self.index.list_documents()
        self.assertEqual(len(docs), 3)

    def test_get_document(self):
        """Test retrieving a specific document"""
        doc_id = "test123"
        doc = DocumentMetadata(
            doc_id=doc_id,
            filename="test.pdf",
            filepath="/path/to/test.pdf",
            description="Test document",
            tree_structure={},
            created_at="2024-01-01T00:00:00",
            file_type="pdf",
            file_size=1000,
            tree_path="/path/to/tree.json"
        )
        self.index.documents[doc_id] = doc

        retrieved = self.index.get_document(doc_id)
        self.assertEqual(retrieved.doc_id, doc_id)
        self.assertEqual(retrieved.filename, "test.pdf")

        # Test non-existent document
        non_existent = self.index.get_document("nonexistent")
        self.assertIsNone(non_existent)

class TestCrossDocumentSearch(unittest.TestCase):
    """Test cross-document search functionality"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.index_path = os.path.join(self.temp_dir, "test_index.json")
        self.index = CrossDocumentIndex(index_path=self.index_path)
        self.search = CrossDocumentSearch(self.index)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch.object(CrossDocumentIndex, 'search_documents', new_callable=AsyncMock)
    async def test_search_with_results(self, mock_search_docs):
        """Test search with results"""
        mock_docs = [
            DocumentMetadata(
                doc_id="doc1",
                filename="financial.pdf",
                filepath="/path/to/financial.pdf",
                description="Financial regulations guide",
                tree_structure={
                    'title': 'Financial Guide',
                    'nodes': [
                        {'node_id': '001', 'title': 'Introduction', 'summary': 'Overview of finance'},
                        {'node_id': '002', 'title': 'Regulations', 'summary': 'Regulatory framework'}
                    ]
                },
                created_at="2024-01-01T00:00:00",
                file_type="pdf",
                file_size=1000000,
                tree_path="/path/to/tree.json"
            )
        ]
        mock_search_docs.return_value = mock_docs

        results = await self.search.search("financial regulations")

        self.assertEqual(len(results['results']), 1)
        self.assertEqual(results['results'][0]['doc_id'], 'doc1')
        self.assertEqual(results['results'][0]['filename'], 'financial.pdf')
        self.assertEqual(len(results['results'][0]['sections']), 2)
        mock_search_docs.assert_called_once_with("financial regulations", 3, 5)

    @patch.object(CrossDocumentIndex, 'search_documents', new_callable=AsyncMock)
    async def test_search_no_results(self, mock_search_docs):
        """Test search with no results"""
        mock_search_docs.return_value = []

        results = await self.search.search("nonexistent topic")

        self.assertEqual(len(results['results']), 0)
        self.assertIn("No relevant documents found", results['message'])
        mock_search_docs.assert_called_once()

# Helper function to run async tests
def run_async_test(test_func):
    """Helper to run async test functions"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(test_func())
    finally:
        loop.close()

# Test runner for async tests
class AsyncTestRunner(unittest.TestCase):
    """Base class for async tests"""

    def run_async(self, coro):
        """Run async coroutine in test"""
        return run_async_test(lambda: coro)

if __name__ == '__main__':
    unittest.main()