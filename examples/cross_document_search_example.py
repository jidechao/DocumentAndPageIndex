#!/usr/bin/env python3
"""
Cross-Document Search Example

This example demonstrates how to use PageIndex's cross-document search functionality
to create, manage, and search across multiple documents.

Requirements:
- OpenAI API key set in environment variable CHATGPT_API_KEY
- Some PDF or Markdown files to index
"""

import asyncio
import os
from pageindex.cross_document_index import CrossDocumentIndex, CrossDocumentSearch

async def main():
    """Main example function demonstrating cross-document search"""

    print("🔍 PageIndex Cross-Document Search Example")
    print("=" * 50)

    # Initialize the cross-document index
    print("\n1. Initializing cross-document index...")
    cross_index = CrossDocumentIndex(index_path="./example_index.json")
    search = CrossDocumentSearch(cross_index)

    # Example file paths (modify these to point to your actual files)
    example_files = [
        "./examples/sample_docs/financial_report.pdf",
        "./examples/sample_docs/compliance_guide.pdf",
        "./examples/sample_docs/technical_manual.md"
    ]

    # Filter to only existing files
    existing_files = [f for f in example_files if os.path.exists(f)]

    if not existing_files:
        print("❌ No example files found. Please add some PDF or Markdown files to the examples/sample_docs/ directory.")
        print("   Looking for files at:", example_files)
        return

    # Add documents to the index
    print(f"\n2. Adding {len(existing_files)} documents to the index...")
    try:
        doc_ids = await cross_index.add_documents_batch(existing_files)
        print(f"✅ Successfully added {len(doc_ids)} documents")

        # Show added documents
        for doc_id in doc_ids:
            doc = cross_index.get_document(doc_id)
            if doc:
                print(f"   📄 {doc.filename}: {doc.description}")

    except Exception as e:
        print(f"❌ Error adding documents: {e}")
        return

    # List all documents in the index
    print("\n3. Current documents in index:")
    documents = cross_index.list_documents()
    for doc in documents:
        print(f"   📋 {doc.doc_id}: {doc.filename}")

    # Perform some example searches
    example_queries = [
        "financial regulations",
        "compliance requirements",
        "risk management",
        "technical specifications"
    ]

    print("\n4. Performing example searches:")
    for query in example_queries:
        print(f"\n   🔎 Searching for: '{query}'")
        try:
            results = await search.search(query, max_documents=2, max_results=3)

            if results['results']:
                print(f"   ✅ Found {len(results['selected_documents'])} relevant document(s)")
                for result in results['results']:
                    print(f"      📄 {result['filename']}")
                    if result['sections']:
                        for section in result['sections'][:2]:  # Show top 2 sections
                            print(f"         • {section['title']}")
                            if section.get('summary'):
                                summary = section['summary'][:100] + "..." if len(section['summary']) > 100 else section['summary']
                                print(f"           {summary}")
            else:
                print(f"   ❌ No relevant documents found")

        except Exception as e:
            print(f"   ❌ Error during search: {e}")

    # Demonstrate index management
    print("\n5. Index Management:")
    print(f"   📊 Total documents: {len(documents)}")
    print(f"   💾 Index file: {cross_index.index_path}")
    print(f"   📁 Trees directory: {os.path.dirname(cross_index.index_path)}/trees")

    # Example of removing a document (commented out to avoid accidental removal)
    # if documents:
    #     first_doc = documents[0]
    #     print(f"\n6. Removing document: {first_doc.filename}")
    #     if cross_index.remove_document(first_doc.doc_id):
    #         print(f"   ✅ Successfully removed {first_doc.filename}")
    #     else:
    #         print(f"   ❌ Failed to remove {first_doc.filename}")

    print("\n🎉 Cross-document search example completed!")
    print("\n💡 Next steps:")
    print("   - Try your own queries with different search terms")
    print("   - Add more documents to the index")
    print("   - Experiment with configuration settings in pageindex/config.yaml")
    print("   - Use the CLI commands: python3 run_pageindex.py --help")

if __name__ == "__main__":
    # Check for OpenAI API key
    if not os.getenv("CHATGPT_API_KEY"):
        print("❌ Error: CHATGPT_API_KEY environment variable not set.")
        print("   Please set your OpenAI API key:")
        print("   export CHATGPT_API_KEY='your-api-key-here'")
        exit(1)

    # Run the example
    asyncio.run(main())