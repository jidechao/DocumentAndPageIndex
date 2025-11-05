import os
import json
import asyncio
import hashlib
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, asdict
from datetime import datetime
from .page_index import page_index_main
from .page_index_md import md_to_tree
from .utils import ChatGPT_API_async, extract_json, ConfigLoader
from .tree_search import TreeSearch, TreeSearchResult, NodeResult
import logging

@dataclass
class DocumentMetadata:
    """Metadata for a document in the cross-document index"""
    doc_id: str
    filename: str
    filepath: str
    description: str
    tree_structure: Dict[str, Any]
    created_at: str
    file_type: str  # 'pdf' or 'markdown'
    file_size: int
    tree_path: str  # path to the saved tree structure file

class DocumentDescriptor:
    """Handles generation of document descriptions based on PageIndex tree structures"""

    def __init__(self, model: str = None):
        from .utils import ConfigLoader
        config_loader = ConfigLoader()
        config_data = config_loader.load()
        
        # Use provided model, or get from config, or default to Qwen
        if model is None:
            model = getattr(config_data, 'model', 'Qwen/Qwen3-235B-A22B-Instruct-2507')
        
        self.model = model
        self.logger = logging.getLogger(__name__)

    async def generate_description(self, tree_structure: Dict[str, Any],
                                 custom_requirements: Optional[str] = None) -> str:
        """Generate a one-sentence description for a document based on its tree structure"""

        # Extract key information from tree structure
        title = tree_structure.get('title', 'Unknown Document')
        top_level_sections = []

        if 'nodes' in tree_structure:
            for node in tree_structure['nodes'][:5]:  # Limit to top 5 sections
                section_title = node.get('title', '')
                section_summary = node.get('summary', '')
                if section_title:
                    top_level_sections.append(f"{section_title}: {section_summary}" if section_summary else section_title)

        sections_text = "\n".join(top_level_sections) if top_level_sections else "No sections available"

        custom_part = f"\nAdditional requirements: {custom_requirements}" if custom_requirements else ""

        prompt = f"""
You are given a table of contents structure of a document.
Your task is to generate a one-sentence description for the document that makes it easy to distinguish from other documents.

Document title: {title}
Document tree structure:
{sections_text}{custom_part}

Directly return the description, do not include any other text.
"""

        try:
            response = await ChatGPT_API_async(model=self.model, prompt=prompt)
            # Clean up response to ensure it's just the description
            description = response.strip().strip('"').strip("'")
            return description
        except Exception as e:
            self.logger.error(f"Error generating description: {e}")
            # Fallback to title-based description
            return f"Document titled '{title}' covering {len(top_level_sections)} main sections"

class DocumentSelector:
    """Handles LLM-based document selection for cross-document queries"""

    def __init__(self, model: str = None):
        from .utils import ConfigLoader
        config_loader = ConfigLoader()
        config_data = config_loader.load()
        
        # Use provided model, or get from config, or default to Qwen
        if model is None:
            model = getattr(config_data, 'model', 'Qwen/Qwen3-235B-A22B-Instruct-2507')
        
        self.model = model
        self.logger = logging.getLogger(__name__)

    async def select_documents(self, query: str, documents: List[DocumentMetadata],
                             max_results: int = 5) -> List[str]:
        """Select relevant documents for a given query using LLM reasoning"""

        if not documents:
            return []

        # Prepare document list for LLM
        doc_list = []
        for doc in documents:
            doc_list.append({
                "doc_id": doc.doc_id,
                "doc_name": doc.filename,
                "doc_description": doc.description
            })

        doc_list_json = json.dumps(doc_list, indent=2, ensure_ascii=False)

        prompt = f"""
You are given a list of documents with their IDs, file names, and descriptions. Your task is to select documents that may contain information relevant to answering the user query.

Query: {query}

Documents: {doc_list_json}

Response Format:
{{
    "thinking": "<Your reasoning for document selection>",
    "answer": <Python list of relevant doc_ids>, e.g. ['doc_id1', 'doc_id2']. Return [] if no documents are relevant.
}}

Return only the JSON structure, with no additional output.
"""

        try:
            response = await ChatGPT_API_async(model=self.model, prompt=prompt)
            response_json = extract_json(response)

            if 'answer' in response_json and isinstance(response_json['answer'], list):
                selected_ids = response_json['answer'][:max_results]  # Limit results
                return [doc_id for doc_id in selected_ids if doc_id in [doc.doc_id for doc in documents]]
            else:
                self.logger.warning("Invalid response format from document selection")
                return []

        except Exception as e:
            self.logger.error(f"Error in document selection: {e}")
            return []

class CrossDocumentIndex:
    """Main class for managing cross-document indices"""

    def __init__(self, index_path: str = "./cross_document_index.json",
                 model: str = None):
        from .utils import ConfigLoader
        config_loader = ConfigLoader()
        config_data = config_loader.load()
        
        # Use provided model, or get from config, or default to Qwen
        if model is None:
            model = getattr(config_data, 'model', 'Qwen/Qwen3-235B-A22B-Instruct-2507')
        
        self.index_path = index_path
        self.model = model
        self.logger = logging.getLogger(__name__)
        self.descriptor = DocumentDescriptor(model=model)
        self.selector = DocumentSelector(model=model)

        # Load existing index or create new one
        self.documents: Dict[str, DocumentMetadata] = {}
        self.index_created_at = datetime.now().isoformat()
        self.index_updated_at = datetime.now().isoformat()

        self._load_index()

    def _load_index(self):
        """Load existing index from file if it exists"""
        if os.path.exists(self.index_path):
            try:
                with open(self.index_path, 'r', encoding='utf-8') as f:
                    index_data = json.load(f)

                self.index_created_at = index_data.get('index_created_at', datetime.now().isoformat())
                self.index_updated_at = index_data.get('index_updated_at', datetime.now().isoformat())

                # Recreate DocumentMetadata objects
                for doc_data in index_data.get('documents', []):
                    doc = DocumentMetadata(**doc_data)
                    self.documents[doc.doc_id] = doc

                self.logger.info(f"Loaded cross-document index with {len(self.documents)} documents")

            except Exception as e:
                self.logger.error(f"Error loading index: {e}")
                self.documents = {}

    def _save_index(self):
        """Save index to file"""
        try:
            index_data = {
                'index_created_at': self.index_created_at,
                'index_updated_at': datetime.now().isoformat(),
                'documents': [asdict(doc) for doc in self.documents.values()]
            }

            os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
            with open(self.index_path, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Saved cross-document index with {len(self.documents)} documents")

        except Exception as e:
            self.logger.error(f"Error saving index: {e}")

    def _generate_doc_id(self, filepath: str) -> str:
        """Generate unique document ID based on file path and content hash"""
        # Use filename + modification time for basic uniqueness
        stat = os.stat(filepath)
        content = f"{filepath}_{stat.st_mtime}_{stat.st_size}"
        return hashlib.md5(content.encode()).hexdigest()[:12]

    async def add_document(self, filepath: str, custom_description_requirements: Optional[str] = None,
                          force_reprocess: bool = False) -> str:
        """Add a document to the cross-document index"""

        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Document not found: {filepath}")

        # Check if document already exists
        doc_id = self._generate_doc_id(filepath)
        if doc_id in self.documents and not force_reprocess:
            self.logger.info(f"Document {doc_id} already exists in index")
            return doc_id

        try:
            # Process document based on file type
            filename = os.path.basename(filepath)
            file_ext = filename.lower().split('.')[-1]

            if file_ext == 'pdf':
                # Process PDF using existing page_index functionality
                from .utils import ConfigLoader
                config_loader = ConfigLoader()
                default_opt = config_loader.load()
                # Update with specific settings for cross-document indexing
                opt_dict = vars(default_opt)
                opt_dict.update({
                    'model': self.model,
                    'if_add_doc_description': 'yes',  # Enable document description
                    'if_add_node_summary': 'yes',
                    'if_add_node_id': 'yes'
                })
                from types import SimpleNamespace as config
                opt = config(**opt_dict)
                tree_structure = page_index_main(filepath, opt)
                file_type = 'pdf'

            elif file_ext in ['md', 'markdown']:
                # Process Markdown using existing functionality
                from .utils import ConfigLoader
                config_loader = ConfigLoader()
                opt = config_loader.load()
                # Convert SimpleNamespace to dict and update with required settings
                opt_dict = vars(opt)
                # Use the model from the config, but ensure it's compatible with tiktoken
                model = opt_dict.get('model', 'gpt-4o')
                # Only pass parameters that md_to_tree supports
                md_supported_params = {
                    'model': model,
                    'if_add_doc_description': 'yes',
                    'if_add_node_summary': opt_dict.get('if_add_node_summary', 'yes'),
                    'if_add_node_text': opt_dict.get('if_add_node_text', 'no'),
                    'if_add_node_id': opt_dict.get('if_add_node_id', 'yes'),
                    'if_thinning': opt_dict.get('if_thinning', 'no'),
                    'min_token_threshold': opt_dict.get('min_token_threshold', 5000),
                    'summary_token_threshold': opt_dict.get('summary_token_threshold', 200)
                }
                tree_structure = await md_to_tree(filepath, **md_supported_params)
                file_type = 'markdown'

            else:
                raise ValueError(f"Unsupported file type: {file_ext}")

            # Use the existing doc_description from tree structure if available, otherwise generate a new one
            existing_description = tree_structure.get('doc_description', '').strip()
            if existing_description and len(existing_description) > 10:  # If there's a meaningful existing description
                description = existing_description
            else:
                description = await self.descriptor.generate_description(
                    tree_structure, custom_description_requirements
                )

            # Save tree structure to separate file
            trees_dir = os.path.join(os.path.dirname(self.index_path), 'trees')
            os.makedirs(trees_dir, exist_ok=True)
            tree_path = os.path.join(trees_dir, f"{doc_id}_tree.json")

            with open(tree_path, 'w', encoding='utf-8') as f:
                json.dump(tree_structure, f, indent=2, ensure_ascii=False)

            # Create metadata
            stat = os.stat(filepath)
            metadata = DocumentMetadata(
                doc_id=doc_id,
                filename=filename,
                filepath=filepath,
                description=description,
                tree_structure=tree_structure,
                created_at=datetime.now().isoformat(),
                file_type=file_type,
                file_size=stat.st_size,
                tree_path=tree_path
            )

            # Add to index
            self.documents[doc_id] = metadata
            self._save_index()

            self.logger.info(f"Added document {doc_id} ({filename}) to index")
            return doc_id

        except Exception as e:
            self.logger.error(f"Error adding document {filepath}: {e}")
            raise

    async def add_documents_batch(self, filepaths: List[str],
                                custom_description_requirements: Optional[str] = None) -> List[str]:
        """Add multiple documents to the index in batch"""
        doc_ids = []

        for filepath in filepaths:
            try:
                doc_id = await self.add_document(filepath, custom_description_requirements)
                doc_ids.append(doc_id)
            except Exception as e:
                self.logger.error(f"Failed to add document {filepath}: {e}")
                continue

        return doc_ids

    def remove_document(self, doc_id: str) -> bool:
        """Remove a document from the index"""
        if doc_id not in self.documents:
            return False

        try:
            doc = self.documents[doc_id]

            # Remove tree structure file
            if os.path.exists(doc.tree_path):
                os.remove(doc.tree_path)

            # Remove from index
            del self.documents[doc_id]
            self._save_index()

            self.logger.info(f"Removed document {doc_id} from index")
            return True

        except Exception as e:
            self.logger.error(f"Error removing document {doc_id}: {e}")
            return False

    def list_documents(self) -> List[DocumentMetadata]:
        """List all documents in the index"""
        return list(self.documents.values())

    def get_document(self, doc_id: str) -> Optional[DocumentMetadata]:
        """Get a specific document by ID"""
        return self.documents.get(doc_id)

    async def search_documents(self, query: str, max_results: int = 5) -> List[DocumentMetadata]:
        """Search for relevant documents using LLM-based selection"""
        documents = list(self.documents.values())

        if not documents:
            return []

        selected_ids = await self.selector.select_documents(query, documents, max_results)

        # Return full metadata for selected documents
        return [doc for doc in documents if doc.doc_id in selected_ids]

class CrossDocumentSearch:
    """Combines document selection with PageIndex retrieval for cross-document search"""

    def __init__(self, cross_index: CrossDocumentIndex, model: str = None):
        from .utils import ConfigLoader
        config_loader = ConfigLoader()
        config_data = config_loader.load()
        
        # Use provided model, or get from config, or default to Qwen
        if model is None:
            model = getattr(config_data, 'model', 'Qwen/Qwen3-235B-A22B-Instruct-2507')
        
        self.cross_index = cross_index
        self.model = model
        self.logger = logging.getLogger(__name__)
        self.tree_search = TreeSearch(model=model)

    async def search(self, query: str, max_documents: int = 3,
                    max_results_per_doc: int = 5, include_nodes: bool = False,
                    max_nodes_per_doc: Optional[int] = None) -> Dict[str, Any]:
        """
        Perform cross-document search combining document selection and content retrieval

        Args:
            query: Search query
            max_documents: Maximum number of documents to analyze
            max_results_per_doc: Maximum results per document (for backward compatibility)
            include_nodes: Whether to include node-level analysis
            max_nodes_per_doc: Maximum nodes per document for tree search

        Returns:
            Search results with optional node information
        """

        # Step 1: Select relevant documents
        relevant_docs = await self.cross_index.search_documents(query, max_documents)

        if not relevant_docs:
            return {
                'query': query,
                'selected_documents': [],
                'results': [],
                'message': 'No relevant documents found for the query'
            }

        # Step 2: Process documents based on whether node analysis is requested
        if include_nodes:
            return await self._search_with_nodes(query, relevant_docs, max_nodes_per_doc)
        else:
            return await self._search_documents_only(query, relevant_docs, max_results_per_doc)

    async def _search_with_nodes(self, query: str, relevant_docs: List[DocumentMetadata],
                               max_nodes_per_doc: Optional[int]) -> Dict[str, Any]:
        """Search with node-level analysis using TreeSearch"""
        try:
            # Prepare document IDs and metadata for TreeSearch
            doc_ids = [doc.doc_id for doc in relevant_docs]
            doc_metadata = {doc.doc_id: doc for doc in relevant_docs}

            # Perform tree search
            tree_results = await self.tree_search.search_nodes(
                query=query,
                document_ids=doc_ids,
                document_metadata=doc_metadata,
                max_nodes_per_doc=max_nodes_per_doc
            )

            # Convert results to expected format
            results = []
            for tree_result in tree_results:
                doc_result = {
                    'doc_id': tree_result.document_id,
                    'filename': tree_result.document_name,
                    'description': next((doc.description for doc in relevant_docs if doc.doc_id == tree_result.document_id), ''),
                    'search_confidence': tree_result.search_confidence,
                    'total_nodes_analyzed': tree_result.total_nodes_analyzed,
                    'processing_time': tree_result.processing_time,
                    'nodes': []
                }

                # Add node information
                for node in tree_result.relevant_nodes:
                    doc_result['nodes'].append({
                        'node_id': node.node_id,
                        'title': node.node_title,
                        'path': node.node_path,
                        'relevance_score': node.relevance_score,
                        'reasoning': node.reasoning,
                        'content_preview': node.content_preview,
                        'text': node.text  # 添加text字段
                    })

                results.append(doc_result)

            # Sort results by confidence
            results.sort(key=lambda x: x['search_confidence'], reverse=True)

            return {
                'query': query,
                'selected_documents': [{'doc_id': doc.doc_id, 'filename': doc.filename} for doc in relevant_docs],
                'results': results,
                'tree_search_enabled': True,
                'message': f'Found relevant nodes in {len(tree_results)} document(s) using tree search'
            }

        except Exception as e:
            self.logger.error(f"Error in tree search: {e}")
            # Fallback to document-only search
            return await self._search_documents_only(query, relevant_docs, 5)

    async def _search_documents_only(self, query: str, relevant_docs: List[DocumentMetadata],
                                   max_results_per_doc: int) -> Dict[str, Any]:
        """Original document-only search for backward compatibility"""
        results = []

        for doc in relevant_docs:
            # Return top-level sections as results
            doc_results = []
            if 'nodes' in doc.tree_structure:
                for node in doc.tree_structure['nodes'][:max_results_per_doc]:
                    doc_results.append({
                        'node_id': node.get('node_id', ''),
                        'title': node.get('title', ''),
                        'summary': node.get('summary', ''),
                        'start_index': node.get('start_index', 0),
                        'end_index': node.get('end_index', 0)
                    })

            results.append({
                'doc_id': doc.doc_id,
                'filename': doc.filename,
                'description': doc.description,
                'sections': doc_results
            })

        return {
            'query': query,
            'selected_documents': [{'doc_id': doc.doc_id, 'filename': doc.filename} for doc in relevant_docs],
            'results': results,
            'tree_search_enabled': False,
            'message': f'Found relevant information in {len(relevant_docs)} document(s)'
        }
