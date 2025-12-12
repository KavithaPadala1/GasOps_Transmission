"""
Specification Document Vectorization and Indexing Module

This module chunks extracted specification texts, generates embeddings using Azure OpenAI,
and uploads them to Azure AI Search for semantic search capabilities.
"""

import os
import uuid
import logging
from typing import List, Dict
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchFieldDataType,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    SemanticConfiguration,
    SemanticSearch,
    SemanticPrioritizedFields,
    SemanticField,
    VectorSearchAlgorithmMetric,
    SearchableField,
    SearchField
)
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

# Azure OpenAI configuration for embeddings
azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
azure_openai_key = os.getenv("AZURE_OPENAI_API_KEY")
azure_openai_version = os.getenv("AZURE_OPENAI_API_VERSION")
embedding_deployment = os.getenv("AZURE_SEARCH_DEPLOYMENT")

# Initialize Azure OpenAI client
client = AzureOpenAI(
    azure_endpoint=azure_openai_endpoint,
    api_key=azure_openai_key,
    api_version=azure_openai_version
)


def delete_search_index():
    """
    Delete the existing Azure AI Search index

    Returns:
        bool: True if deletion succeeded, False otherwise
    """
    index_client = SearchIndexClient(
        endpoint=search_endpoint,
        credential=AzureKeyCredential(search_key)
    )

    try:
        index_client.delete_index(index_name)
        logger.info(f"Deleted existing index '{index_name}'")
        return True
    except Exception as e:
        logger.warning(f"Could not delete index '{index_name}': {e}")
        return False


def create_search_index():
    """
    Create the Azure AI Search index with vector search capabilities

    The index schema includes:
    - id: Unique document chunk identifier
    - content: Text content (searchable)
    - embeddingVector: 1536-dim vector for semantic search
    - pageNumber: Page reference from source document
    - documentName: Source PDF filename
    - chunkNumber: Sequential chunk number
    - totalChunks: Total chunks in the document

    Returns:
        SearchIndex: Created index object
    """
    index_client = SearchIndexClient(
        endpoint=search_endpoint,
        credential=AzureKeyCredential(search_key)
    )

    # Define the fields for the index
    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SearchableField(name="content", type=SearchFieldDataType.String),
        SearchField(
            name="embeddingVector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=1536,  # text-embedding-ada-002 dimension
            vector_search_profile_name="my-vector-config"
        ),
        SimpleField(name="pageNumber", type=SearchFieldDataType.Int32),
        SearchableField(name="documentName", type=SearchFieldDataType.String),
        SimpleField(name="chunkNumber", type=SearchFieldDataType.Int32),
        SimpleField(name="totalChunks", type=SearchFieldDataType.Int32)
    ]

    # Configure vector search with HNSW algorithm
    vector_search = VectorSearch(
        algorithms=[
            HnswAlgorithmConfiguration(
                name="my-hnsw-config",
                parameters={
                    "m": 4,
                    "efConstruction": 400,
                    "efSearch": 500,
                    "metric": VectorSearchAlgorithmMetric.COSINE
                }
            )
        ],
        profiles=[
            VectorSearchProfile(
                name="my-vector-config",
                algorithm_configuration_name="my-hnsw-config"
            )
        ]
    )

    # Configure semantic search for better ranking
    semantic_config = SemanticConfiguration(
        name="my-semantic-config",
        prioritized_fields=SemanticPrioritizedFields(
            content_fields=[SemanticField(field_name="content")]
        )
    )

    semantic_search = SemanticSearch(configurations=[semantic_config])

    # Create the search index
    index = SearchIndex(
        name=index_name,
        fields=fields,
        vector_search=vector_search,
        semantic_search=semantic_search
    )

    logger.info(f"Creating index '{index_name}'...")
    result = index_client.create_or_update_index(index)
    logger.info(f"Index '{result.name}' created successfully!")

    return result


def get_embedding(text: str) -> List[float]:
    """
    Generate embedding for text using Azure OpenAI

    Args:
        text (str): Text to embed

    Returns:
        List[float]: 1536-dimensional embedding vector or empty list on failure
    """
    try:
        response = client.embeddings.create(
            model=embedding_deployment,
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        return []


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
    """
    Split text into overlapping chunks for better context preservation

    Args:
        text (str): Text to chunk
        chunk_size (int): Maximum chunk size in characters
        overlap (int): Overlap between consecutive chunks

    Returns:
        List[str]: List of text chunks
    """
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        # Try to break at a sentence or paragraph boundary
        if end < len(text):
            # Look for sentence endings
            for i in range(end, max(start + chunk_size // 2, start), -1):
                if text[i] in '.!?\n':
                    end = i + 1
                    break

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        start = end - overlap
        if start >= len(text):
            break

    return chunks


def process_extracted_texts():
    """
    Process all extracted text files and prepare for indexing

    Reads all *_extracted.txt files from specs_extracted_texts folder,
    chunks them, generates embeddings, and creates index documents.

    Returns:
        List[Dict]: List of documents ready for upload to Azure AI Search
    """
    extracted_texts_folder = os.path.join(os.path.dirname(__file__), '..', 'specs_extracted_texts')

    if not os.path.exists(extracted_texts_folder):
        logger.error(f"Folder {extracted_texts_folder} does not exist!")
        return []

    documents = []

    # Process each extracted text file
    for filename in os.listdir(extracted_texts_folder):
        if filename.endswith('_extracted.txt'):
            file_path = os.path.join(extracted_texts_folder, filename)
            document_name = filename.replace('_extracted.txt', '.pdf')

            logger.info(f"Processing {document_name}...")

            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()

            # Split text into chunks
            chunks = chunk_text(text)
            total_chunks = len(chunks)

            logger.info(f"  Split into {total_chunks} chunks")

            for i, chunk in enumerate(chunks):
                # Generate embedding for the chunk
                logger.info(f"  Generating embedding for chunk {i+1}/{total_chunks}...")
                embedding = get_embedding(chunk)

                if embedding:  # Only add if embedding was successful
                    doc = {
                        "id": str(uuid.uuid4()),
                        "content": chunk,
                        "embeddingVector": embedding,
                        "pageNumber": 1,  # TODO: Track actual page numbers if needed
                        "documentName": document_name,
                        "chunkNumber": i + 1,
                        "totalChunks": total_chunks
                    }
                    documents.append(doc)
                else:
                    logger.warning(f"  Failed to generate embedding for chunk {i+1}")

    return documents


def upload_documents(documents: List[Dict]):
    """
    Upload documents to Azure AI Search

    Args:
        documents (List[Dict]): List of documents with embeddings to upload
    """
    search_client = SearchClient(
        endpoint=search_endpoint,
        index_name=index_name,
        credential=AzureKeyCredential(search_key)
    )

    logger.info(f"Uploading {len(documents)} documents to index '{index_name}'...")

    # Upload in batches to avoid timeout
    batch_size = 100
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        try:
            result = search_client.upload_documents(documents=batch)
            logger.info(f"Uploaded batch {i//batch_size + 1}, {len(batch)} documents")
        except Exception as e:
            logger.error(f"Error uploading batch {i//batch_size + 1}: {e}")


def main():
    """
    Main execution function for indexing workflow

    Steps:
    1. Delete existing index (optional)
    2. Create new index with schema
    3. Process extracted texts into chunks
    4. Generate embeddings
    5. Upload to Azure AI Search
    """
    if not all([search_endpoint, search_key, azure_openai_key, embedding_deployment]):
        logger.error("Missing required environment variables!")
        logger.error("Required: AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_KEY, AZURE_OPENAI_API_KEY, AZURE_SEARCH_DEPLOYMENT")
        return

    # Delete and recreate the index
    logger.info("Attempting to delete existing index...")
    if delete_search_index():
        logger.info("Index deleted successfully. Creating new index...")
    else:
        logger.info("Index deletion failed or index didn't exist. Proceeding with create/update...")

    # Create the index
    create_search_index()

    # Process extracted texts and prepare documents
    documents = process_extracted_texts()

    if documents:
        # Upload documents to the index
        upload_documents(documents)
        logger.info(f"Successfully indexed {len(documents)} document chunks!")
    else:
        logger.warning("No documents to index!")


if __name__ == "__main__":
    # Run indexing when script is executed directly
    logging.basicConfig(level=logging.INFO)
    main()
