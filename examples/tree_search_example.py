#!/usr/bin/env python3
"""
Tree Search Example
Demonstrates how to use the Tree Search functionality to find specific nodes in documents.
"""

import asyncio
import os
import sys
import json

# Add the parent directory to the path so we can import pageindex modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pageindex.cross_document_index import CrossDocumentIndex, CrossDocumentSearch
from pageindex.tree_search import TreeSearch


async def basic_tree_search_example():
    """Basic example of tree search functionality"""
    print("=== Basic Tree Search Example ===\n")

    # Initialize the cross-document index
    index_path = "./cross_document_index.json"
    cross_index = CrossDocumentIndex(index_path=index_path)
    search = CrossDocumentSearch(cross_index)

    # Example queries for tree search
    queries = [
        "What are the company's revenue figures?",
        "Information about EBITDA adjustments",
        "Risk factors and mitigation strategies",
        "Executive compensation details"
    ]

    for query in queries:
        print(f"🔍 Searching for: {query}")
        print("-" * 50)

        try:
            # Search with tree nodes enabled
            results = await search.search(
                query=query,
                max_documents=2,
                max_results_per_doc=3,
                include_nodes=True,  # Enable tree search
                max_nodes_per_doc=3
            )

            if not results['results']:
                print("❌ No relevant information found.\n")
                continue

            print(f"✅ Found relevant information in {len(results['results'])} document(s):\n")

            for i, result in enumerate(results['results'], 1):
                print(f"{i}. Document: {result['filename']}")
                print(f"   Description: {result['description']}")

                if results.get('tree_search_enabled'):
                    print(f"   🌲 Tree Search Results:")
                    print(f"   Search Confidence: {result.get('search_confidence', 0):.2f}")
                    print(f"   Nodes Analyzed: {result.get('total_nodes_analyzed', 0)}")

                    if 'nodes' in result and result['nodes']:
                        for j, node in enumerate(result['nodes'], 1):
                            print(f"     {j}. {node['title']}")
                            print(f"        Path: {' → '.join(node['path'])}")
                            print(f"        Relevance: {node['relevance_score']:.2f}")
                            if node.get('content_preview'):
                                print(f"        Preview: {node['content_preview'][:100]}...")
                            print()

                print("-" * 30)

        except Exception as e:
            print(f"❌ Error during search: {e}\n")

        print("\n")


async def compare_search_methods():
    """Compare traditional search vs tree search"""
    print("=== Search Method Comparison ===\n")

    cross_index = CrossDocumentIndex(index_path="./cross_document_index.json")
    search = CrossDocumentSearch(cross_index)

    query = "Financial performance metrics"
    print(f"Query: {query}\n")

    # Traditional search (document-level only)
    print("1. Traditional Search (Document-level only):")
    print("-" * 40)

    try:
        traditional_results = await search.search(
            query=query,
            max_documents=2,
            max_results_per_doc=3,
            include_nodes=False  # Disable tree search
        )

        for result in traditional_results['results']:
            print(f"📄 Document: {result['filename']}")
            if 'sections' in result:
                for section in result['sections'][:2]:  # Show first 2 sections
                    print(f"   - {section['title']}")
            print()

    except Exception as e:
        print(f"Error in traditional search: {e}")

    # Tree search (node-level analysis)
    print("\n2. Tree Search (Node-level analysis):")
    print("-" * 40)

    try:
        tree_results = await search.search(
            query=query,
            max_documents=2,
            max_results_per_doc=3,
            include_nodes=True,  # Enable tree search
            max_nodes_per_doc=3
        )

        for result in tree_results['results']:
            print(f"📄 Document: {result['filename']}")
            print(f"   Search Confidence: {result.get('search_confidence', 0):.2f}")

            if 'nodes' in result and result['nodes']:
                for node in result['nodes']:
                    print(f"   🌳 {node['title']}")
                    print(f"      Path: {' → '.join(node['path'])}")
                    print(f"      Relevance: {node['relevance_score']:.2f}")
                    if node.get('reasoning'):
                        print(f"      Reasoning: {node['reasoning']}")
            print()

    except Exception as e:
        print(f"Error in tree search: {e}")


async def performance_benchmark():
    """Benchmark tree search performance"""
    print("=== Performance Benchmark ===\n")

    cross_index = CrossDocumentIndex(index_path="./cross_document_index.json")
    search = CrossDocumentSearch(cross_index)

    test_queries = [
        "Revenue growth",
        "Operating expenses",
        "Cash flow analysis",
        "Market risk factors"
    ]

    print("Running performance tests...\n")

    total_time = 0
    total_nodes = 0

    for i, query in enumerate(test_queries, 1):
        print(f"Test {i}: {query}")

        try:
            import time
            start_time = time.time()

            results = await search.search(
                query=query,
                max_documents=3,
                include_nodes=True,
                max_nodes_per_doc=5
            )

            end_time = time.time()
            search_time = end_time - start_time
            total_time += search_time

            if results.get('tree_search_enabled'):
                nodes_found = sum(len(r.get('nodes', [])) for r in results['results'])
                total_nodes += nodes_found

                print(f"   Time: {search_time:.2f}s")
                print(f"   Documents analyzed: {len(results['results'])}")
                print(f"   Nodes found: {nodes_found}")

                avg_confidence = sum(r.get('search_confidence', 0) for r in results['results']) / len(results['results'])
                print(f"   Average confidence: {avg_confidence:.2f}")
            else:
                print(f"   Time: {search_time:.2f}s")
                print(f"   Tree search not available")

            print()

        except Exception as e:
            print(f"   Error: {e}\n")

    if total_time > 0 and total_nodes > 0:
        print(f"📊 Benchmark Summary:")
        print(f"   Total queries: {len(test_queries)}")
        print(f"   Total time: {total_time:.2f}s")
        print(f"   Average time per query: {total_time/len(test_queries):.2f}s")
        print(f"   Total nodes found: {total_nodes}")
        print(f"   Average nodes per query: {total_nodes/len(test_queries):.1f}")


async def custom_tree_search_example():
    """Example using TreeSearch class directly"""
    print("=== Custom Tree Search Example ===\n")

    # Initialize TreeSearch with custom configuration
    config = {
        'max_nodes_per_document': 3,
        'min_relevance_score': 0.5,
        'include_content_preview': True,
        'preview_max_length': 150,
        'cache_enabled': True,
        'max_retries': 2
    }

    tree_search = TreeSearch(model="gpt-4o", config_path=None)
    tree_search.config.update(config)

    # Load documents from cross-document index
    cross_index = CrossDocumentIndex(index_path="./cross_document_index.json")
    documents = cross_index.list_documents()

    if not documents:
        print("❌ No documents found in the index. Please create an index first.")
        return

    print(f"Found {len(documents)} documents in the index\n")

    # Select first few documents for demo
    demo_docs = documents[:2]
    doc_ids = [doc.doc_id for doc in demo_docs]
    doc_metadata = {doc.doc_id: doc for doc in demo_docs}

    query = "Key financial metrics and performance indicators"
    print(f"Analyzing query: {query}\n")

    try:
        results = await tree_search.search_nodes(
            query=query,
            document_ids=doc_ids,
            document_metadata=doc_metadata,
            max_nodes_per_doc=3
        )

        print(f"🌲 Tree Search Results:")
        print("=" * 50)

        for result in results:
            print(f"\n📄 Document: {result.document_name}")
            print(f"   Document ID: {result.document_id}")
            print(f"   Search Confidence: {result.search_confidence:.2f}")
            print(f"   Processing Time: {result.processing_time:.2f}s")
            print(f"   Total Nodes Analyzed: {result.total_nodes_analyzed}")

            if result.relevant_nodes:
                print(f"   Relevant Nodes Found ({len(result.relevant_nodes)}):")
                for i, node in enumerate(result.relevant_nodes, 1):
                    print(f"     {i}. {node.node_title}")
                    print(f"        Node ID: {node.node_id}")
                    print(f"        Path: {' → '.join(node.node_path)}")
                    print(f"        Relevance Score: {node.relevance_score:.2f}")
                    print(f"        Reasoning: {node.reasoning}")
                    if node.content_preview:
                        print(f"        Content: {node.content_preview}")
                    print()
            else:
                print("   ❌ No relevant nodes found")

    except Exception as e:
        print(f"❌ Error during tree search: {e}")


async def main():
    """Main function to run all examples"""
    print("🌲 Tree Search Examples")
    print("=" * 60)
    print()

    # Check if cross-document index exists
    if not os.path.exists("./cross_document_index.json"):
        print("❌ Cross-document index not found!")
        print("Please create an index first using:")
        print("python run_pageindex.py create-index --files file1.pdf file2.pdf")
        return

    # Run examples
    try:
        await basic_tree_search_example()
        await compare_search_methods()
        await performance_benchmark()
        await custom_tree_search_example()

        print("\n✅ All examples completed successfully!")

    except KeyboardInterrupt:
        print("\n\n⚠️  Examples interrupted by user")
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())