# DB Search and Scrape Tool - Usage Guide

This tool combines embedding-based search with web scraping to provide comprehensive research analysis.

## Overview

The `db_search_and_scrape` function:
1. ✅ Creates an embedding for your query
2. ✅ Searches for similar research papers in precomputed embedding databases
3. ✅ Retrieves top-k most relevant papers
4. ✅ Scrapes the content of each paper using Firecrawl
5. ✅ Uses GPT to analyze and synthesize findings from all papers

## Quick Start

### Basic Usage

```python
from agents.tools.db_search_and_scrape import db_search_and_scrape

# Search and analyze research papers
result = db_search_and_scrape(
    query="python code generation benchmarks",
    db_path="path/to/embeddings.pkl",
    top_k=3
)

print(result)
```

### Using Available Embedding Files

```python
# Example paths to existing embedding files
embedding_files = {
    "code_generation": "all_final_csvs_finall/01_Code_Generation/combined_01_code_generation_embeddings.pkl",
    "math_reasoning": "all_final_csvs_finall/02_Math_Reasoning/combined_02_math_reasoning_embeddings.pkl",
    "qa_vqa": "all_final_csvs_finall/03_QA_VQA/combined_03_qa_vqa_embeddings.pkl",
    "classification": "all_final_csvs_finall/04_Classification_NLI/combined_04_classification_nli_embeddings.pkl",
    "summarization": "all_final_csvs_finall/05_Text_Summarization/combined_05_text_summarization_embeddings.pkl",
    "translation": "all_final_csvs_finall/06_Machine_Translation/combined_06_machine_translation_embeddings.pkl"
}

# Search in code generation research
result = db_search_and_scrape(
    query="multilingual programming language evaluation",
    db_path=embedding_files["code_generation"],
    top_k=3
)
```

### Environment Setup

Create a `.env` file with required credentials:

```bash
# Azure OpenAI for embeddings
AZURE_OPENAI_ENDPOINT_EMBEDDING=your_endpoint
AZURE_OPENAI_API_KEY_EMBEDDING=your_key

# Azure OpenAI for chat completion
OPENAI_BASE_URL=your_base_url
OPENAI_API_VERSION=your_version
OPENAI_DEPLOYMENT_NAME=your_deployment
OPENAI_API_KEY=your_key

# Firecrawl for web scraping
FIRECRAWL_API_KEY=your_firecrawl_key

# Optional: Default database path
DB_PATH=path/to/default/embeddings.pkl
```

## Function Parameters

### `db_search_and_scrape(query, db_path, top_k=3)`

- **query** (str): Natural language search query
- **db_path** (str): Path to pickle file containing precomputed embeddings
- **top_k** (int): Number of top results to retrieve and analyze (default: 3)

### Returns
String containing comprehensive GPT analysis of the research findings.

## Example Queries

### Code Generation Research
```python
result = db_search_and_scrape(
    "How do multilingual models perform on code generation tasks?",
    "all_final_csvs_finall/01_Code_Generation/combined_01_code_generation_embeddings.pkl"
)
```

### Math Reasoning Research
```python
result = db_search_and_scrape(
    "What are the latest approaches to mathematical reasoning in LLMs?",
    "all_final_csvs_finall/02_Math_Reasoning/combined_02_math_reasoning_embeddings.pkl"
)
```

### Cross-Domain Search
```python
# Search across all available research areas
result = db_search_and_scrape(
    "Transformer model performance across different tasks",
    "all_final_csvs_finall/all_embeddings_combined.pkl",
    top_k=5
)
```

## Output Format

The function returns a comprehensive analysis including:

1. **Research Summary**: Key findings from each paper
2. **Methodology Overview**: Approaches used in the research
3. **Results and Metrics**: Specific performance numbers and comparisons
4. **Insights and Takeaways**: Practical implications
5. **Source Citations**: URLs and paper details
6. **Search Metadata**: Information about the search process

## Error Handling

The function handles various error scenarios:
- Invalid embedding database paths
- Failed web scraping attempts
- Network connectivity issues
- GPT API failures

## Performance Tips

1. **Use Specific Queries**: More specific queries yield better results
2. **Choose Appropriate top_k**: Start with 3, increase for comprehensive analysis
3. **Domain-Specific Searches**: Use domain-specific embedding files for focused research
4. **Rate Limiting**: The function includes delays between requests to respect API limits

## Integration with Agent Systems

The tool is designed for easy integration with multi-agent systems:

```python
from agents.tools.db_search_and_scrape import db_search_and_scrape_tool

# Tool configuration
tool_config = {
    "name": db_search_and_scrape_tool["name"],
    "description": db_search_and_scrape_tool["description"],
    "function": db_search_and_scrape_tool["run_function"]
}

# Use in agent workflow
result = tool_config["function"](
    query="latest developments in neural code generation",
    db_path="embeddings/code_generation.pkl",
    top_k=3
)
```

## Testing

Run the test script to verify functionality:

```bash
python agents/tools/test_db_search_and_scrape.py
```

This will test both the main function and the wrapper function with sample queries.

## Troubleshooting

### Common Issues

1. **"No embeddings found"**: Ensure the pickle file exists and was generated correctly
2. **"Error getting embedding"**: Check Azure OpenAI credentials and endpoint
3. **"Failed to scrape"**: Verify Firecrawl API key and network connectivity
4. **"GPT response error"**: Check chat completion API credentials

### Debug Mode

Enable verbose output by checking the console for detailed progress information during execution.

## Dependencies

Required packages (install via pip):
```bash
pip install openai firecrawl scikit-learn python-dotenv pandas numpy
```

The tool is now ready for use! It provides a powerful way to search through research literature and get comprehensive AI-generated analysis of the most relevant findings.
