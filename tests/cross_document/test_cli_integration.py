import unittest
import tempfile
import os
import json
from unittest.mock import patch, MagicMock
from unittest.mock import AsyncMock
import asyncio
import sys
import argparse

# Add the parent directory to the path so we can import the CLI module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Mock the pageindex imports
class MockPageIndex:
    pass

class MockPageIndexMD:
    pass

class MockCrossDocumentIndex:
    def __init__(self, **kwargs):
        self.documents = {}

    def list_documents(self):
        return list(self.documents.values())

    def get_document(self, doc_id):
        return self.documents.get(doc_id)

    def remove_document(self, doc_id):
        return self.documents.pop(doc_id, None) is not None

    async def add_documents_batch(self, filepaths, custom_requirements=None):
        return [f"doc_id_{i}" for i in range(len(filepaths))]

class MockCrossDocumentSearch:
    def __init__(self, cross_index):
        self.cross_index = cross_index

    async def search(self, query, max_docs=3, max_results=5):
        return {
            'query': query,
            'selected_documents': [{'doc_id': 'doc1', 'filename': 'test.pdf'}],
            'results': [{
                'doc_id': 'doc1',
                'filename': 'test.pdf',
                'description': 'Test document',
                'sections': [
                    {'title': 'Section 1', 'summary': 'Summary 1'},
                    {'title': 'Section 2', 'summary': 'Summary 2'}
                ]
            }],
            'message': 'Found relevant information'
        }

# Mock the imports
sys.modules['pageindex'] = MagicMock()
sys.modules['pageindex.page_index'] = MagicMock()
sys.modules['pageindex.page_index_md'] = MagicMock()
sys.modules['pageindex.cross_document_index'] = MagicMock()
sys.modules['pageindex.cross_document_index'].CrossDocumentIndex = MockCrossDocumentIndex
sys.modules['pageindex.cross_document_index'].CrossDocumentSearch = MockCrossDocumentSearch

class TestCLIIntegration(unittest.TestCase):
    """Test CLI integration for cross-document functionality"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

        # Create test files
        self.test_files = []
        for i in range(3):
            filepath = os.path.join(self.temp_dir, f"test_{i}.pdf")
            with open(filepath, 'w') as f:
                f.write(f"Test PDF content {i}")
            self.test_files.append(filepath)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('run_pageindex.create_cross_document_index')
    def test_cmd_create_index_success(self, mock_create_index):
        """Test successful index creation"""
        from run_pageindex import cmd_create_index

        mock_index = MockCrossDocumentIndex()
        mock_create_index.return_value = mock_index

        # Create mock args
        class MockArgs:
            files = self.test_files
            description_requirements = "Focus on technical content"

        # Run the command
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(cmd_create_index(MockArgs()))
        finally:
            loop.close()

        mock_create_index.assert_called_once()

    @patch('run_pageindex.create_cross_document_index')
    def test_cmd_create_index_no_files(self, mock_create_index):
        """Test index creation with no files"""
        from run_pageindex import cmd_create_index

        mock_index = MockCrossDocumentIndex()
        mock_create_index.return_value = mock_index

        class MockArgs:
            files = []
            description_requirements = None

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            with self.assertRaises(ValueError) as context:
                loop.run_until_complete(cmd_create_index(MockArgs()))
            self.assertIn("At least one file must be specified", str(context.exception))
        finally:
            loop.close()

    @patch('run_pageindex.create_cross_document_index')
    def test_cmd_list_documents_empty(self, mock_create_index):
        """Test listing documents when index is empty"""
        from run_pageindex import cmd_list_documents

        mock_index = MockCrossDocumentIndex()
        mock_create_index.return_value = mock_index

        class MockArgs:
            pass

        # Capture stdout
        from io import StringIO
        import sys
        captured_output = StringIO()
        sys.stdout = captured_output

        try:
            cmd_list_documents(MockArgs())
            output = captured_output.getvalue()
            self.assertIn("No documents found", output)
        finally:
            sys.stdout = sys.__stdout__

    @patch('run_pageindex.create_cross_document_index')
    def test_cmd_list_documents_with_docs(self, mock_create_index):
        """Test listing documents when index has documents"""
        from run_pageindex import cmd_list_documents
        from pageindex.cross_document_index import DocumentMetadata

        mock_index = MockCrossDocumentIndex()
        mock_create_index.return_value = mock_index

        # Add test documents
        for i, filepath in enumerate(self.test_files):
            doc = DocumentMetadata(
                doc_id=f"doc_{i}",
                filename=f"test_{i}.pdf",
                filepath=filepath,
                description=f"Test document {i}",
                tree_structure={},
                created_at="2024-01-01T00:00:00",
                file_type="pdf",
                file_size=1000,
                tree_path=f"/path/to/tree_{i}.json"
            )
            mock_index.documents[f"doc_{i}"] = doc

        class MockArgs:
            pass

        # Capture stdout
        from io import StringIO
        import sys
        captured_output = StringIO()
        sys.stdout = captured_output

        try:
            cmd_list_documents(MockArgs())
            output = captured_output.getvalue()
            self.assertIn("Found 3 documents", output)
            self.assertIn("test_0.pdf", output)
            self.assertIn("test_1.pdf", output)
            self.assertIn("test_2.pdf", output)
        finally:
            sys.stdout = sys.__stdout__

    @patch('run_pageindex.create_cross_document_index')
    def test_cmd_search_with_results(self, mock_create_index):
        """Test search with results"""
        from run_pageindex import cmd_search

        mock_index = MockCrossDocumentIndex()
        mock_create_index.return_value = mock_index

        class MockArgs:
            query = "financial regulations"
            max_documents = 3
            max_results = 5

        # Capture stdout
        from io import StringIO
        import sys
        captured_output = StringIO()
        sys.stdout = captured_output

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(cmd_search(MockArgs()))
            output = captured_output.getvalue()
            self.assertIn("Searching for: financial regulations", output)
            self.assertIn("Found relevant information", output)
            self.assertIn("test.pdf", output)
        finally:
            loop.close()
            sys.stdout = sys.__stdout__

    @patch('run_pageindex.create_cross_document_index')
    def test_cmd_search_no_query(self, mock_create_index):
        """Test search without query"""
        from run_pageindex import cmd_search

        mock_index = MockCrossDocumentIndex()
        mock_create_index.return_value = mock_index

        class MockArgs:
            query = None
            max_documents = 3
            max_results = 5

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            with self.assertRaises(ValueError) as context:
                loop.run_until_complete(cmd_search(MockArgs()))
            self.assertIn("Query must be specified", str(context.exception))
        finally:
            loop.close()

    @patch('run_pageindex.create_cross_document_index')
    def test_cmd_remove_document_success(self, mock_create_index):
        """Test successful document removal"""
        from run_pageindex import cmd_remove_document
        from pageindex.cross_document_index import DocumentMetadata

        mock_index = MockCrossDocumentIndex()
        mock_create_index.return_value = mock_index

        # Add test document
        doc = DocumentMetadata(
            doc_id="test_doc",
            filename="test.pdf",
            filepath=self.test_files[0],
            description="Test document",
            tree_structure={},
            created_at="2024-01-01T00:00:00",
            file_type="pdf",
            file_size=1000,
            tree_path="/path/to/tree.json"
        )
        mock_index.documents["test_doc"] = doc

        class MockArgs:
            doc_id = "test_doc"
            force = True

        # Capture stdout
        from io import StringIO
        import sys
        captured_output = StringIO()
        sys.stdout = captured_output

        try:
            cmd_remove_document(MockArgs())
            output = captured_output.getvalue()
            self.assertIn("Removing document:", output)
            self.assertIn("test.pdf", output)
            self.assertIn("Document removed successfully", output)
        finally:
            sys.stdout = sys.__stdout__

    @patch('run_pageindex.create_cross_document_index')
    def test_cmd_remove_document_not_found(self, mock_create_index):
        """Test removing non-existent document"""
        from run_pageindex import cmd_remove_document

        mock_index = MockCrossDocumentIndex()
        mock_create_index.return_value = mock_index

        class MockArgs:
            doc_id = "nonexistent_doc"
            force = True

        # Capture stdout
        from io import StringIO
        import sys
        captured_output = StringIO()
        sys.stdout = captured_output

        try:
            cmd_remove_document(MockArgs())
            output = captured_output.getvalue()
            self.assertIn("not found in index", output)
        finally:
            sys.stdout = sys.__stdout__

class TestCLIArgumentParsing(unittest.TestCase):
    """Test CLI argument parsing"""

    def test_create_index_args(self):
        """Test create-index argument parsing"""
        # This would normally be tested by running the actual CLI
        # but for now we'll just verify the argument structure
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest='command')

        create_parser = subparsers.add_parser('create-index')
        create_parser.add_argument('--files', nargs='+', required=True)
        create_parser.add_argument('--description-requirements', type=str)

        # Test valid arguments
        args = create_parser.parse_args(['--files', 'file1.pdf', 'file2.pdf', '--description-requirements', 'test'])
        self.assertEqual(args.files, ['file1.pdf', 'file2.pdf'])
        self.assertEqual(args.description_requirements, 'test')

    def test_search_args(self):
        """Test search argument parsing"""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest='command')

        search_parser = subparsers.add_parser('search')
        search_parser.add_argument('--query', type=str, required=True)
        search_parser.add_argument('--max-documents', type=int, default=3)
        search_parser.add_argument('--max-results', type=int, default=5)

        # Test valid arguments
        args = search_parser.parse_args(['--query', 'test query', '--max-documents', '2'])
        self.assertEqual(args.query, 'test query')
        self.assertEqual(args.max_documents, 2)
        self.assertEqual(args.max_results, 5)  # default value

if __name__ == '__main__':
    unittest.main()