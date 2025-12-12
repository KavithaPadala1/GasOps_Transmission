"""
Specification Document Text Extraction Module

This module extracts text from PDF specification documents stored in Azure Blob Storage
using Azure Document Intelligence API. Extracted text is saved locally for vectorization.
"""

import os
import requests
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
import base64
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Load Azure Document Intelligence credentials from environment
ENDPOINT = os.getenv('AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT')
KEY = os.getenv('AZURE_DOCUMENT_INTELLIGENCE_KEY')

# Azure Blob Storage configuration (optional - can be configured per deployment)
ACCOUNT_NAME = "cespecs"
CONTAINER_NAME = "xhp"

# PDF blob details with SAS URLs (client provided)
# TODO: Move to configuration file or database for production
pdf_blobs = [
    {
        "name": "G-1065.pdf",
        "url": "https://cespecs.blob.core.windows.net/xhp/G-1065.pdf?sp=r&st=2025-08-13T16:31:21Z&se=2025-08-14T00:46:21Z&spr=https&sv=2024-11-04&sr=b&sig=6AUh40g1wRLvlqKLsJgzAGZC%2B%2BZ30Zh66Vqvxtz%2BeXs%3D"
    },
    {
        "name": "G-8107StlPipeSpec.pdf",
        "url": "https://cespecs.blob.core.windows.net/xhp/G-8107StlPipeSpec.pdf?sp=r&st=2025-08-13T16:46:57Z&se=2025-08-14T01:01:57Z&spr=https&sv=2024-11-04&sr=b&sig=se6a%2BfLYXCq4sRHjua3akl5fU%2F5FNws4GzeinCj6VZU%3D"
    }
]

# Output folder for extracted texts
output_folder = os.path.join(os.path.dirname(__file__), '..', 'specs_extracted_texts')
os.makedirs(output_folder, exist_ok=True)

# Initialize Azure Document Intelligence client
client = DocumentIntelligenceClient(endpoint=ENDPOINT, credential=AzureKeyCredential(KEY))


def download_pdf_from_blob(blob_url: str) -> bytes:
    """
    Download PDF from Azure Blob Storage using SAS URL

    Args:
        blob_url (str): SAS URL for the PDF blob

    Returns:
        bytes: PDF binary data or None if download fails
    """
    try:
        logger.info(f"Downloading PDF from blob URL")
        response = requests.get(blob_url)
        response.raise_for_status()
        logger.info(f"Successfully downloaded PDF ({len(response.content)} bytes)")
        return response.content
    except Exception as e:
        logger.error(f"Error downloading PDF from blob: {e}")
        return None


def extract_text_from_pdf_data(pdf_data: bytes) -> str:
    """
    Extract text from PDF data using Azure Document Intelligence

    Args:
        pdf_data (bytes): PDF binary data

    Returns:
        str: Extracted text content or empty string if extraction fails
    """
    try:
        logger.info("Starting text extraction from PDF")
        base64_data = base64.b64encode(pdf_data).decode('utf-8')
        analyze_request = AnalyzeDocumentRequest(bytes_source=base64_data)

        poller = client.begin_analyze_document(
            "prebuilt-read",  # Use prebuilt-read for text extraction
            analyze_request
        )
        result = poller.result()

        # Extract text content
        text_content = result.content if result.content else ""

        # Fallback: If no content, extract from lines
        if not text_content and result.pages:
            all_text = []
            for page in result.pages:
                if page.lines:
                    for line in page.lines:
                        all_text.append(line.content)
            text_content = "\n".join(all_text)

        logger.info(f"Successfully extracted {len(text_content)} characters")
        return text_content
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        return ""


def extract_all_specs():
    """
    Process all PDFs from Azure Blob Storage and save extracted text

    This function is typically run once during setup or when new specs are added.
    """
    logger.info("Starting specs extraction process")

    for pdf_blob in pdf_blobs:
        blob_name = pdf_blob["name"]
        blob_url = pdf_blob["url"]

        logger.info(f"Processing {blob_name}...")
        try:
            # Download PDF from Azure Blob Storage
            pdf_data = download_pdf_from_blob(blob_url)

            if pdf_data:
                # Extract text using Document Intelligence
                text = extract_text_from_pdf_data(pdf_data)

                # Save extracted text
                output_path = os.path.join(output_folder, blob_name.replace('.pdf', '_extracted.txt'))
                with open(output_path, 'w', encoding='utf-8') as out_f:
                    out_f.write(text)
                logger.info(f"Saved extracted text to {output_path}")
            else:
                logger.error(f"Failed to download {blob_name}")

        except Exception as e:
            logger.error(f"Failed to process {blob_name}: {e}")

    logger.info("Specs extraction process completed")


if __name__ == "__main__":
    # Run extraction when script is executed directly
    logging.basicConfig(level=logging.INFO)
    extract_all_specs()
