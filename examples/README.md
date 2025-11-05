# PageIndex Examples

This directory contains example scripts and tutorials for using PageIndex features.

## Cross-Document Search

### `cross_document_search_example.py`

A comprehensive example demonstrating how to use PageIndex's cross-document search functionality.

**Features demonstrated:**
- Creating a cross-document index from multiple files
- Adding documents to the index (both PDF and Markdown)
- Listing documents in the index
- Performing searches across multiple documents
- Index management operations

**Usage:**

1. Set your OpenAI API key:
```bash
export CHATGPT_API_KEY='your-api-key-here'
```

2. Create a directory for sample documents:
```bash
mkdir -p examples/sample_docs
```

3. Add some PDF or Markdown files to `examples/sample_docs/`

4. Run the example:
```bash
cd examples
python3 cross_document_search_example.py
```

**Expected output:**
```
🔍 PageIndex Cross-Document Search Example
==================================================

1. Initializing cross-document index...

2. Adding 3 documents to the index...
✅ Successfully added 3 documents
   📄 financial_report.pdf: Annual financial report with revenue analysis and risk assessment
   📄 compliance_guide.pdf: Comprehensive guide to regulatory compliance requirements
   📄 technical_manual.md: Technical documentation with API specifications

3. Current documents in index:
   📋 abc123def456: financial_report.pdf
   📋 def456ghi789: compliance_guide.pdf
   📋 ghi789jkl012: technical_manual.md

4. Performing example searches:

   🔎 Searching for: 'financial regulations'
   ✅ Found 2 relevant document(s)
      📄 compliance_guide.pdf
         • Regulatory Framework
           Overview of key financial regulations and compliance standards
         • Implementation Guidelines
           Step-by-step procedures for regulatory compliance
      📄 financial_report.pdf
         • Risk Management
           Detailed analysis of financial risk factors and mitigation strategies

🎉 Cross-document search example completed!
```

## CLI Examples

### Basic Cross-Document Commands

```bash
# Create an index from multiple files
python3 run_pageindex.py create-index --files doc1.pdf doc2.pdf doc3.md

# List all documents in the index
python3 run_pageindex.py list-docs

# Search across documents
python3 run_pageindex.py search --query "financial regulations"

# Search with custom limits
python3 run_pageindex.py search --query "risk management" --max-documents 2 --max-results 5

# Remove a document
python3 run_pageindex.py remove-doc --doc-id abc123def456
```

### Advanced Usage

```bash
# Create index with custom description requirements
python3 run_pageindex.py create-index \
  --files *.pdf \
  --description-requirements "Focus on financial compliance and regulatory aspects"

# Search with specific document and result limits
python3 run_pageindex.py search \
  --query "What are the key compliance requirements?" \
  --max-documents 3 \
  --max-results 10
```

## Single Document Processing (Legacy)

For backward compatibility, you can still process individual documents:

```bash
# Process a single PDF
python3 run_pageindex.py --pdf_path document.pdf

# Process a single Markdown file
python3 run_pageindex.py --md_path document.md

# Or use the new subcommand syntax
python3 run_pageindex.py process --pdf_path document.pdf
python3 run_pageindex.py process --md_path document.md
```

## Configuration

You can customize cross-document behavior in `pageindex/config.yaml`:

```yaml
cross_document:
  # Cross-document index settings
  index_path: "./my_document_index.json"
  trees_directory: "./document_trees"

  # Document selection settings
  max_documents_per_query: 5
  max_results_per_document: 3

  # Model settings
  description_model: "gpt-4o-2024-11-20"
  selection_model: "gpt-4o-2024-11-20"

  # Performance settings
  batch_processing: true
  cache_descriptions: true
  enable_async: true
```

## Troubleshooting

### Common Issues

1. **"API key not found" error**
   - Make sure to set the `CHATGPT_API_KEY` environment variable
   - Verify your OpenAI API key is valid and has sufficient credits

2. **"File not found" error**
   - Check that file paths are correct
   - Use absolute paths if relative paths don't work

3. **Slow processing**
   - Cross-document indexing requires API calls for each document
   - Processing time depends on document size and complexity
   - Consider reducing `max_documents_per_query` for faster searches

4. **Memory issues with large document collections**
   - The current implementation is designed for small-to-medium collections (up to ~100 documents)
   - For larger collections, consider processing in batches

### Getting Help

- 📖 Check the main [README.md](../README.md) for detailed documentation
- 🤝 Join our [Discord community](https://discord.gg/VuXuf29EUj) for support
- 📨 Leave us a [message](https://ii2abc2jejf.typeform.com/to/tK3AXl8T) for specific issues