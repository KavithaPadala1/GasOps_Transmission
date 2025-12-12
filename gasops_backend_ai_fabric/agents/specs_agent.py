"""
Specifications Agent Module

This agent handles queries related to gas operations specifications, compliance requirements,
regulatory standards, and technical specification documents using RAG architecture.
"""

import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from prompts.specs_prompt import ask_question

logger = logging.getLogger(__name__)


def handle_specs_agent(query: str, auth_token: str = None) -> dict:
    """
    Handle specifications-related questions using the specs_llm module

    This agent performs semantic search on specification documents and generates
    accurate, cited answers using Azure AI Search and Azure OpenAI.

    Args:
        query (str): User's question about specifications
        auth_token (str, optional): Not used by this agent but kept for consistency

    Returns:
        dict: Response containing answer and source citations
            {
                "answer": str,  # Generated answer with citations
                "sources": List[Dict],  # Source documents referenced
                "question": str  # Original question
            }

    Example:
        >>> result = handle_specs_agent("What's required before a welder can weld?")
        >>> print(result["answer"])
        According to G-1065, welders must complete qualification testing...
        >>> print(result["sources"])
        [{"document": "G-1065.pdf", "chunk": "3/15", "page": 12, "score": 0.89}]
    """
    logger.info(f"SpecsAgent processing query: {query[:100]}...")

    try:
        # Use the ask_question function from specs_llm.py
        result = ask_question(query, top_k=5, show_context=False)

        logger.info(f"SpecsAgent found {len(result.get('sources', []))} relevant sources")

        # Format the response for consistency with other agents
        return {
            "answer": result["answer"],
            "sources": result.get("sources", []),
            "question": result["question"]
        }

    except Exception as e:
        logger.error(f"Error in SpecsAgent: {e}")
        return {
            "answer": "I encountered an error while searching the specifications. Please try again.",
            "sources": [],
            "question": query
        }


# Example usage for testing
if __name__ == "__main__":
    # Test the specs agent
    logging.basicConfig(level=logging.INFO)

    test_questions = [
        "What's required before a welder can weld on Company-owned piping?",
        "What are the welding requirements for gas pipelines?",
        "What specifications are needed for pipeline materials?"
    ]

    for question in test_questions:
        print(f"\n{'='*80}")
        print(f"Question: {question}")
        print(f"{'='*80}")

        result = handle_specs_agent(question)

        print(f"\nAnswer: {result['answer']}")

        if result['sources']:
            print(f"\nSources:")
            for i, source in enumerate(result['sources'], 1):
                print(f"  {i}. {source['document']} (chunk {source['chunk']}, page {source['page']}, relevance: {source['score']:.2f})")
