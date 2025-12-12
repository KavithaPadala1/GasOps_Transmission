"""
Specifications Q&A Module using Retrieval Augmented Generation (RAG)

This module performs semantic search on specification documents and generates
accurate, cited answers using Azure AI Search and Azure OpenAI.
"""

import os
import logging
from typing import List, Dict, Optional
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Azure AI Search configuration
search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
search_key = os.getenv("AZURE_SEARCH_KEY")
index_name = "specs-vectorized-index"

# Azure OpenAI configuration
azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
azure_openai_key = os.getenv("AZURE_OPENAI_API_KEY")
azure_openai_version = os.getenv("AZURE_OPENAI_API_VERSION")
embedding_deployment = os.getenv("AZURE_SEARCH_DEPLOYMENT")
chat_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")

# Initialize clients
openai_client = AzureOpenAI(
    azure_endpoint=azure_openai_endpoint,
    api_key=azure_openai_key,
    api_version=azure_openai_version
)

search_client = SearchClient(
    endpoint=search_endpoint,
    index_name=index_name,
    credential=AzureKeyCredential(search_key)
)


def get_question_embedding(question: str) -> List[float]:
    """
    Generate embedding for the user question

    Args:
        question (str): User's question

    Returns:
        List[float]: 1536-dimensional embedding vector or empty list on failure
    """
    try:
        response = openai_client.embeddings.create(
            model=embedding_deployment,
            input=question
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Error generating embedding for question: {e}")
        return []


def search_specs(question: str, top_k: int = 5) -> List[Dict]:
    """
    Search the specs index for relevant chunks using hybrid search

    Combines keyword-based search with vector similarity search and semantic ranking
    for optimal retrieval accuracy.

    Args:
        question (str): User's question
        top_k (int): Number of relevant chunks to retrieve

    Returns:
        List[Dict]: List of relevant document chunks with metadata
    """
    # Get embedding for the question
    question_vector = get_question_embedding(question)

    if not question_vector:
        logger.error("Failed to generate embedding for question")
        return []

    try:
        # Perform hybrid search (text + vector + semantic ranking)
        results = search_client.search(
            search_text=question,  # Keyword search
            vector_queries=[{
                "kind": "vector",
                "vector": question_vector,
                "k_nearest_neighbors": top_k,
                "fields": "embeddingVector"
            }],
            select=["id", "content", "documentName", "chunkNumber", "totalChunks", "pageNumber"],
            top=top_k,
            query_type="semantic",
            semantic_configuration_name="my-semantic-config"
        )

        # Extract results
        search_results = []
        for result in results:
            search_results.append({
                "content": result["content"],
                "document_name": result["documentName"],
                "chunk_number": result["chunkNumber"],
                "total_chunks": result["totalChunks"],
                "page_number": result["pageNumber"],
                "score": result.get("@search.score", 0)
            })

        logger.info(f"Found {len(search_results)} relevant chunks for question")
        return search_results

    except Exception as e:
        logger.error(f"Error searching specs: {e}")
        return []


def generate_answer(question: str, search_results: List[Dict]) -> str:
    """
    Generate answer using GPT with the retrieved context

    Args:
        question (str): User's question
        search_results (List[Dict]): Relevant document chunks from search

    Returns:
        str: Generated answer with citations
    """
    if not search_results:
        return "I couldn't find any relevant information in the specifications to answer your question."

    # Prepare context from search results
    context_parts = []
    for i, result in enumerate(search_results, 1):
        context_parts.append(
            f"Context {i} (from {result['document_name']}, chunk {result['chunk_number']}/{result['total_chunks']}, page {result['page_number']}):\n"
            f"{result['content']}\n"
        )

    context = "\n".join(context_parts)

    # System prompt for compliance assistant
    system_prompt = """You are a compliance assistant for gas operations specifications. Use only the provided spec excerpts to answer questions. 

IMPORTANT INSTRUCTIONS:
1. Answer ONLY based on the provided context
2. Always include specific section references and page citations when available
3. If the information is not in the provided context, say "Not specified in the provided specifications"
4. Be precise and cite the exact document name and section when possible
5. If you're unsure or the context is ambiguous, clearly state your uncertainty
6. Format citations as: (Page X, [Document Name], Section Y.Z if available)

Now answer the user's question based only on the provided context."""

    # User prompt with question and context
    user_prompt = f"""Question: {question}

Context from specifications:
{context}

Please provide a detailed answer based only on the above context, including proper citations."""

    try:
        # Generate response using GPT
        response = openai_client.chat.completions.create(
            model=chat_deployment,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,  # Low temperature for factual accuracy
            max_tokens=1000
        )

        answer = response.choices[0].message.content
        logger.info("Successfully generated answer from context")
        return answer

    except Exception as e:
        logger.error(f"Error generating answer: {e}")
        return "I encountered an error while generating the answer. Please try again."


def ask_question(question: str, top_k: int = 5, show_context: bool = False) -> Dict:
    """
    Main function to answer questions about specifications

    Args:
        question (str): User's question
        top_k (int): Number of relevant chunks to retrieve
        show_context (bool): Whether to include retrieved context in response

    Returns:
        Dict: Response containing answer, sources, and optionally context
    """
    logger.info(f"Processing specs question: {question}")

    # Step 1: Search for relevant chunks
    search_results = search_specs(question, top_k)

    if not search_results:
        return {
            "question": question,
            "answer": "I couldn't find any relevant information in the specifications to answer your question.",
            "sources": [],
            "context_used": []
        }

    logger.info(f"Found {len(search_results)} relevant chunks")

    if show_context:
        logger.info("\nRetrieved context:")
        for i, result in enumerate(search_results, 1):
            logger.info(f"{i}. From {result['document_name']} (chunk {result['chunk_number']}/{result['total_chunks']}, score: {result['score']:.2f}):")
            logger.info(f"   {result['content'][:200]}...")

    # Step 2: Generate answer using GPT
    logger.info("Generating answer with GPT...")
    answer = generate_answer(question, search_results)

    # Prepare sources for citation
    sources = []
    for result in search_results:
        sources.append({
            "document": result['document_name'],
            "chunk": f"{result['chunk_number']}/{result['total_chunks']}",
            "page": result['page_number'],
            "score": result['score']
        })

    return {
        "question": question,
        "answer": answer,
        "sources": sources,
        "context_used": search_results if show_context else []
    }


def interactive_qa():
    """
    Interactive Q&A session for testing (command-line interface)
    """
    print("=== Gas Operations Specifications Q&A System ===")
    print("Ask questions about your specifications. Type 'quit' to exit.\n")

    while True:
        question = input("Question: ").strip()

        if question.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break

        if not question:
            continue

        try:
            result = ask_question(question, top_k=3, show_context=False)

            print(f"\nAnswer: {result['answer']}")

            if result['sources']:
                print(f"\nSources:")
                for i, source in enumerate(result['sources'], 1):
                    print(f"{i}. {source['document']} (chunk {source['chunk']}, page {source['page']}, relevance: {source['score']:.2f})")

            print("\n" + "="*80 + "\n")

        except Exception as e:
            logger.error(f"Error: {e}")
            print("Please try again.\n")


# Example usage and testing
def test_qa_system():
    """Test the Q&A system with sample questions"""

    sample_questions = [
       "What's required before a welder can weld on Company-owned piping?"
    ]

    print("=== Testing Q&A System ===\n")

    for question in sample_questions:
        print(f"Testing: {question}")
        result = ask_question(question, top_k=3)
        print(f"Answer: {result['answer']}")
        print(f"Sources: {len(result['sources'])} documents referenced")
        print("="*80 + "\n")


if __name__ == "__main__":
    # Check if required environment variables are set
    if not all([search_endpoint, search_key, azure_openai_key, embedding_deployment, chat_deployment]):
        print("Missing required environment variables!")
        print("Required: AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_KEY, AZURE_OPENAI_API_KEY, AZURE_SEARCH_DEPLOYMENT, AZURE_OPENAI_DEPLOYMENT")
    else:
        # Choose what to run
        import sys
        if len(sys.argv) > 1 and sys.argv[1] == "test":
            logging.basicConfig(level=logging.INFO)
            test_qa_system()
        else:
            logging.basicConfig(level=logging.INFO)
            interactive_qa()
