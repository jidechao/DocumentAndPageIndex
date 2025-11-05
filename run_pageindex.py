import argparse
import os
import json
import asyncio
from pageindex import *
from pageindex.page_index_md import md_to_tree
from pageindex.cross_document_index import CrossDocumentIndex, CrossDocumentSearch

def create_cross_document_index():
    """Create and return a cross-document index instance"""
    from pageindex.utils import ConfigLoader
    config_loader = ConfigLoader()
    config_data = config_loader.load()

    # Convert SimpleNamespace to dict for attribute access
    config_dict = vars(config_data)
    cross_doc_config = config_dict.get('cross_document', {})
    index_path = cross_doc_config.get('index_path', './cross_document_index.json')
    model = cross_doc_config.get('description_model', 'gpt-4o-2024-11-20')

    return CrossDocumentIndex(index_path=index_path, model=model)

async def cmd_create_index(args):
    """Create cross-document index from multiple files"""
    if not args.files:
        raise ValueError("At least one file must be specified with --files")

    # Validate all files exist
    for filepath in args.files:
        if not os.path.isfile(filepath):
            raise ValueError(f"File not found: {filepath}")

    print(f"Creating cross-document index from {len(args.files)} files...")

    cross_index = create_cross_document_index()
    custom_requirements = getattr(args, 'description_requirements', None)

    doc_ids = await cross_index.add_documents_batch(args.files, custom_requirements)

    print(f"Successfully added {len(doc_ids)} documents to the index:")
    for doc_id in doc_ids:
        doc = cross_index.get_document(doc_id)
        if doc:
            print(f"  - {doc.filename}: {doc.description}")

def cmd_list_documents(args):
    """List all documents in the cross-document index"""
    cross_index = create_cross_document_index()
    documents = cross_index.list_documents()

    if not documents:
        print("No documents found in the cross-document index.")
        return

    print(f"Found {len(documents)} documents in the index:")
    for doc in documents:
        print(f"  ID: {doc.doc_id}")
        print(f"  File: {doc.filename}")
        print(f"  Type: {doc.file_type}")
        print(f"  Description: {doc.description}")
        print(f"  Added: {doc.created_at}")
        print("-" * 50)

async def cmd_search(args):
    """Search across documents in the index"""
    if not args.query:
        raise ValueError("Query must be specified with --query")

    cross_index = create_cross_document_index()
    search = CrossDocumentSearch(cross_index)

    print(f"Searching for: {args.query}")

    max_docs = getattr(args, 'max_documents', 3)
    max_results = getattr(args, 'max_results', 5)
    include_nodes = getattr(args, 'include_nodes', False)
    max_nodes_per_doc = getattr(args, 'max_nodes_per_doc', None)

    if include_nodes:
        print("🔍 Tree search enabled - analyzing document nodes...")
        if max_nodes_per_doc:
            print(f"   Max nodes per document: {max_nodes_per_doc}")

    results = await search.search(
        args.query,
        max_docs,
        max_results,
        include_nodes=include_nodes,
        max_nodes_per_doc=max_nodes_per_doc
    )

    if not results['results']:
        print("No relevant information found.")
        return

    print(f"\nFound relevant information in {len(results['selected_documents'])} document(s):")
    if results.get('tree_search_enabled'):
        print("   Using tree search analysis")
    print("=" * 60)

    for result in results['results']:
        print(f"\nDocument ID: {result['doc_id']}")
        print(f"Document Name: {result['filename']}")
        print(f"Description: {result['description']}")

        # Show tree search specific information
        if results.get('tree_search_enabled') and 'search_confidence' in result:
            print(f"Search Confidence: {result['search_confidence']:.2f}")
            print(f"Nodes Analyzed: {result['total_nodes_analyzed']}")
            print(f"Processing Time: {result['processing_time']:.2f}s")

        # Show sections (backward compatibility)
        if 'sections' in result and result['sections']:
            print("Relevant sections:")
            for section in result['sections']:
                print(f"  - {section['title']}")
                if section.get('summary'):
                    print(f"    {section['summary']}")

        # Show nodes (tree search)
        if 'nodes' in result and result['nodes']:
            print("🌲 Relevant nodes found:")
            for i, node in enumerate(result['nodes'], 1):
                print(f" {i}. {node['title']}")
                print(f"     Path: {' → '.join(node['path'])}")
                print(f"     Node ID: {node['node_id']}")
                print(f"     Relevance: {node['relevance_score']:.2f}")
                if args.verbose and node.get('reasoning'):
                    print(f"     Reasoning: {node['reasoning']}")
                if node.get('content_preview'):
                    print(f"     Preview: {node['content_preview'][:100]}...")
                if node.get('text'):
                    print(f"     Text: {node['text'][:500]}...")  # 增加文本显示长度
                print()

        print("-" * 40)

    # Show summary statistics for tree search
    if results.get('tree_search_enabled'):
        total_nodes = sum(len(r.get('nodes', [])) for r in results['results'])
        avg_confidence = sum(r.get('search_confidence', 0) for r in results['results']) / len(results['results'])
        print(f"\n📊 Tree Search Summary:")
        print(f"   Total nodes found: {total_nodes}")
        print(f"   Average confidence: {avg_confidence:.2f}")

def cmd_remove_document(args):
    """Remove a document from the index"""
    if not args.doc_id:
        raise ValueError("Document ID must be specified with --doc_id")

    cross_index = create_cross_document_index()

    # Show document info before removal
    doc = cross_index.get_document(args.doc_id)
    if not doc:
        print(f"Document with ID '{args.doc_id}' not found in index.")
        return

    print(f"Removing document:")
    print(f"  ID: {doc.doc_id}")
    print(f"  File: {doc.filename}")
    print(f"  Description: {doc.description}")

    if args.force or input("Are you sure? (y/N): ").lower() == 'y':
        if cross_index.remove_document(args.doc_id):
            print("Document removed successfully.")
        else:
            print("Failed to remove document.")
    else:
        print("Operation cancelled.")

if __name__ == "__main__":
    # Set up argument parser with subcommands
    parser = argparse.ArgumentParser(description='Process PDF/Markdown documents and generate structures with cross-document indexing support')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Legacy single document processing (default behavior)
    single_parser = subparsers.add_parser('process', help='Process a single document (legacy mode)')
    single_parser.add_argument('--pdf_path', type=str, default="D:/project/ReadAgent（无需分块和向量化的RAG）/DocumentAndPageIndex/tests/pdfs/demo.pdf",help='Path to the PDF file')
    single_parser.add_argument('--md_path', type=str, help='Path to the Markdown file')
    single_parser.add_argument('--model', type=str, default='Qwen/Qwen3-235B-A22B-Instruct-2507', help='Model to use')
    single_parser.add_argument('--toc-check-pages', type=int, default=20,
                      help='Number of pages to check for table of contents (PDF only)')
    single_parser.add_argument('--max-pages-per-node', type=int, default=10,
                      help='Maximum number of pages per node (PDF only)')
    single_parser.add_argument('--max-tokens-per-node', type=int, default=20000,
                      help='Maximum number of tokens per node (PDF only)')
    single_parser.add_argument('--if-add-node-id', type=str, default='yes',
                      help='Whether to add node id to the node')
    single_parser.add_argument('--if-add-node-summary', type=str, default='yes',
                      help='Whether to add summary to the node')
    single_parser.add_argument('--if-add-doc-description', type=str, default='no',
                      help='Whether to add doc description to the doc')
    single_parser.add_argument('--if-add-node-text', type=str, default='no',
                      help='Whether to add text to the node')
    single_parser.add_argument('--if-thinning', type=str, default='no',
                      help='Whether to apply tree thinning for markdown (markdown only)')
    single_parser.add_argument('--thinning-threshold', type=int, default=5000,
                      help='Minimum token threshold for thinning (markdown only)')
    single_parser.add_argument('--summary-token-threshold', type=int, default=200,
                      help='Token threshold for generating summaries (markdown only)')

    # Cross-document index commands
    create_parser = subparsers.add_parser('create-index', help='Create cross-document index from multiple files')
    create_parser.add_argument('--files', nargs='+', required=True,
                             help='List of PDF or Markdown files to index')
    create_parser.add_argument('--description-requirements', type=str,
                             help='Custom requirements for document description generation')

    list_parser = subparsers.add_parser('list-docs', help='List all documents in the cross-document index')

    search_parser = subparsers.add_parser('search', help='Search across documents in the index')
    search_parser.add_argument('--query', type=str, required=True, help='Search query')
    search_parser.add_argument('--max-documents', type=int, default=3,
                             help='Maximum number of documents to search')
    search_parser.add_argument('--max-results', type=int, default=5,
                             help='Maximum results per document')
    search_parser.add_argument('--include-nodes', action='store_true',
                             help='Enable tree search to find specific relevant nodes')
    search_parser.add_argument('--max-nodes-per-doc', type=int, default=5,
                             help='Maximum number of nodes to analyze per document (tree search)')
    search_parser.add_argument('--verbose', '-v', action='store_true',
                             help='Show detailed reasoning and paths for tree search results')

    remove_parser = subparsers.add_parser('remove-doc', help='Remove a document from the index')
    remove_parser.add_argument('--doc-id', type=str, required=True, help='Document ID to remove')
    remove_parser.add_argument('--force', action='store_true', help='Skip confirmation prompt')

    args = parser.parse_args()

    # Handle default behavior (no subcommand) - maintain backward compatibility
    if args.command is None:
        # If no command, assume single document processing for backward compatibility
        if not any(arg.startswith('--') for arg in ['--pdf_path', '--md_path']):
            parser.print_help()
            exit(1)
        args.command = 'process'

    # Route to appropriate command handler
    try:
        if args.command == 'process':
            # Original single document processing logic
            # Validate that exactly one file type is specified
            if not args.pdf_path and not args.md_path:
                raise ValueError("Either --pdf_path or --md_path must be specified")
            if args.pdf_path and args.md_path:
                raise ValueError("Only one of --pdf_path or --md_path can be specified")

            if args.pdf_path:
                # Validate PDF file
                if not args.pdf_path.lower().endswith('.pdf'):
                    raise ValueError("PDF file must have .pdf extension")
                if not os.path.isfile(args.pdf_path):
                    raise ValueError(f"PDF file not found: {args.pdf_path}")

                # Process PDF file
                # Configure options
                opt = config(
                    model=args.model,
                    toc_check_page_num=args.toc_check_pages,
                    max_page_num_each_node=args.max_pages_per_node,
                    max_token_num_each_node=args.max_tokens_per_node,
                    if_add_node_id=args.if_add_node_id,
                    if_add_node_summary=args.if_add_node_summary,
                    if_add_doc_description=args.if_add_doc_description,
                    if_add_node_text=args.if_add_node_text
                )

                # Process the PDF
                toc_with_page_number = page_index_main(args.pdf_path, opt)
                print('Parsing done, saving to file...')

                # Save results
                pdf_name = os.path.splitext(os.path.basename(args.pdf_path))[0]
                output_dir = './results'
                output_file = f'{output_dir}/{pdf_name}_structure.json'
                os.makedirs(output_dir, exist_ok=True)

                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(toc_with_page_number, f, indent=2, ensure_ascii=False)

                print(f'Tree structure saved to: {output_file}')

            elif args.md_path:
                # Validate Markdown file
                if not args.md_path.lower().endswith(('.md', '.markdown')):
                    raise ValueError("Markdown file must have .md or .markdown extension")
                if not os.path.isfile(args.md_path):
                    raise ValueError(f"Markdown file not found: {args.md_path}")

                # Process markdown file
                print('Processing markdown file...')

                # Use ConfigLoader to get consistent defaults (matching PDF behavior)
                from pageindex.utils import ConfigLoader
                config_loader = ConfigLoader()

                # Create options dict with user args
                user_opt = {
                    'model': args.model,
                    'if_add_node_summary': args.if_add_node_summary,
                    'if_add_doc_description': args.if_add_doc_description,
                    'if_add_node_text': args.if_add_node_text,
                    'if_add_node_id': args.if_add_node_id
                }

                # Load config with defaults from config.yaml
                opt = config_loader.load(user_opt)

                toc_with_page_number = asyncio.run(md_to_tree(
                    md_path=args.md_path,
                    if_thinning=args.if_thinning.lower() == 'yes',
                    min_token_threshold=args.thinning_threshold,
                    if_add_node_summary=opt.if_add_node_summary,
                    summary_token_threshold=args.summary_token_threshold,
                    model=opt.model,
                    if_add_doc_description=opt.if_add_doc_description,
                    if_add_node_text=opt.if_add_node_text,
                    if_add_node_id=opt.if_add_node_id
                ))

                print('Parsing done, saving to file...')

                # Save results
                md_name = os.path.splitext(os.path.basename(args.md_path))[0]
                output_dir = './results'
                output_file = f'{output_dir}/{md_name}_structure.json'
                os.makedirs(output_dir, exist_ok=True)

                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(toc_with_page_number, f, indent=2, ensure_ascii=False)

                print(f'Tree structure saved to: {output_file}')

        elif args.command == 'create-index':
            asyncio.run(cmd_create_index(args))

        elif args.command == 'list-docs':
            cmd_list_documents(args)

        elif args.command == 'search':
            asyncio.run(cmd_search(args))

        elif args.command == 'remove-doc':
            cmd_remove_document(args)

        else:
            parser.print_help()

    except Exception as e:
        print(f"Error: {e}")
        exit(1)
