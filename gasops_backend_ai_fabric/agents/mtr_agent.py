# MTR Agent - Material Test Report Specialist
# Advanced AI agent for processing Material Test Reports using Azure Document Intelligence OCR
# Handles heat number queries, material properties analysis, and standards compliance validation

import json
import os
import tempfile
import base64
import logging
from config.azure_client import get_azure_chat_openai
from tools.execute_api import execute_api
from tools.mtr_tools import get_mtr_tools
from prompts.mtr_prompt import get_property_analysis_prompt, get_mtr_prompt
from tools.mtr_tools import GetMTRFileDatabyHeatNumber


# Azure Document Intelligence imports
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Initialize Azure OpenAI client for AI-powered analysis
try:
    azure_client, azureopenai = get_azure_chat_openai()
    logger.info("Azure OpenAI client initialized for MTR agent")
except Exception as e:
    logger.error(f"Failed to initialize Azure OpenAI client in MTR agent: {str(e)}")
    azure_client, azureopenai = None, None

def execute_tool_call(tool_call, auth_token=None):
    """
    Execute tool function calls from OpenAI function calling.
    
    Handles the mapping between OpenAI tool calls and actual API functions,
    ensuring proper parameter transformation and error handling.
    
    Args:
        tool_call: OpenAI tool call object containing function name and arguments
        auth_token (str): Authentication token for API calls
        
    Returns:
        dict: API response with success status and data
    """
    function_name = tool_call.function.name
    arguments = json.loads(tool_call.function.arguments)
    
    # Route function calls to appropriate tool implementations
    # Each function handles specific MTR-related operations
    if function_name == "GetMTRFileDatabyHeatNumber":
        # from tools.mtr_tools import GetMTRFileDatabyHeatNumber
        return GetMTRFileDatabyHeatNumber(
            heat_number=arguments.get("heat_number"),
            company_mtr_file_id=arguments.get("company_mtr_file_id"),
            auth_token=auth_token
        )
    else:
        # Fallback for additional functions - direct API call
        parameters = {k: v for k, v in arguments.items() if v is not None}
        return execute_api("AIMTRMetaData", function_name, parameters, auth_token, method="GET")

class MTRProcessor:
    """
    Advanced MTR document processor using Azure Document Intelligence.
    
    Handles the complete pipeline for Material Test Report processing:
    1. Binary string to PDF conversion
    2. OCR text extraction using Azure Document Intelligence
    3. AI-powered property analysis and standards compliance checking
    
    Features:
    - Supports both base64 and raw binary input formats
    - Automatic temporary file management with cleanup
    - Comprehensive text extraction with fallback methods
    - Intelligent property analysis using Azure OpenAI
    """
    
    def __init__(self):
        self.azure_client = azure_client
    
    def convert_binary_to_pdf(self, binary_string: str, heat_number: str) -> str:
        """Convert binary string to PDF file"""
        try:
            # Try to decode as base64 first
            try:
                pdf_data = base64.b64decode(binary_string)
                logger.info(f"Successfully decoded binary string as base64 for heat number {heat_number}")
            except Exception:
                # If base64 decoding fails, assume it's raw binary
                pdf_data = binary_string.encode('latin-1') if isinstance(binary_string, str) else binary_string
                logger.info(f"Using binary string as raw data for heat number {heat_number}")
            
            # Create temporary file with heat number as name
            temp_dir = tempfile.gettempdir()
            pdf_path = os.path.join(temp_dir, f"MTR_{heat_number}.pdf")
            
            with open(pdf_path, 'wb') as pdf_file:
                pdf_file.write(pdf_data)
            
            logger.info(f"PDF file created successfully: {pdf_path}")
            return pdf_path
            
        except Exception as e:
            logger.error(f"Failed to convert binary to PDF for heat number {heat_number}: {str(e)}")
            raise Exception(f"PDF conversion failed: {str(e)}")
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF using Azure Document Intelligence"""
        try:
            # Get credentials from environment
            endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
            key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")
            
            if not endpoint or not key:
                raise ValueError("Azure Document Intelligence credentials not found in .env file")
            
            client = DocumentIntelligenceClient(endpoint=endpoint, credential=AzureKeyCredential(key))
            
            # Read the PDF file as binary data and pass directly to API
            with open(pdf_path, "rb") as f:
                poller = client.begin_analyze_document(
                    "prebuilt-read",  # Use prebuilt-read for text extraction
                    body=f  # Pass the file object directly as body
                )
            
            result: AnalyzeResult = poller.result()
            
            # Extract text content directly from the result
            text_content = result.content if result.content else ""
            
            # Alternative: If you want to extract text line by line
            if not text_content and result.pages:
                all_text = []
                for page in result.pages:
                    if page.lines:
                        for line in page.lines:
                            all_text.append(line.content)
                text_content = "\n".join(all_text)
            
            logger.info(f"Successfully extracted {len(text_content)} characters of text from PDF")
            return text_content
            
        except Exception as e:
            logger.error(f"Text extraction failed for {pdf_path}: {str(e)}")
            raise Exception(f"OCR extraction failed: {str(e)}")
    
    def analyze_mtr_properties(self, query: str, extracted_text: str, document_info: dict) -> str:
        """Use comprehensive OCR+LLM approach to answer questions about MTR document"""
        try:
            analysis_prompt = get_property_analysis_prompt(query, extracted_text, document_info)
            
            # Use Azure OpenAI client correctly
            response = self.azure_client.chat.completions.create(
                model=azureopenai,
                messages=[{"role": "user", "content": analysis_prompt}]
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Comprehensive MTR analysis failed: {str(e)}")
            return f"I was able to extract the complete text from the MTR document, but encountered an issue during analysis: {str(e)}. Please try rephrasing your question or ask for specific properties."

def handle_mtr_agent(user_input, auth_token=None):
    """
    Main MTR agent handler for processing Material Test Report queries.
    
    This function orchestrates the complete MTR processing workflow:
    1. Uses Azure OpenAI to understand user intent and extract parameters
    2. Calls appropriate API tools to retrieve MTR data
    3. Processes binary documents with sophisticated OCR when available
    4. Provides intelligent analysis using AI-powered property evaluation
    
    Args:
        user_input (str): User's query about MTR documents or material properties
        auth_token (str, optional): Authentication token for API calls
        
    Returns:
        str: Comprehensive response including material properties, analysis, or error messages
        
    Features:
    - Automatic parameter extraction from natural language queries
    - Azure Document Intelligence OCR for PDF processing
    - Standards compliance analysis (API 5L, ASME, etc.)
    - Chemical composition and mechanical properties analysis
    - Intelligent conversation context handling
    """
    
    logger.info("MTR agent handling user query")

    # Get MTR prompt
    try:
        mtr_prompt = get_mtr_prompt(user_input)
        logger.info("MTR prompt generated successfully")
    except Exception as e:
        logger.error(f"Failed to generate MTR prompt: {str(e)}")
        return f"Error in MTR prompt generation: {str(e)}"
    
    # Create messages list for conversation
    messages = [
        {
            "role": "system",
            "content": mtr_prompt
        },
        {
            "role": "user", 
            "content": user_input
        }
    ]

    try:
        # Initial AI call with function calling enabled for parameter extraction
        response = azure_client.chat.completions.create(
            model=azureopenai,
            messages=messages,
            tools=get_mtr_tools(),
            tool_choice="required"  # Forces the LLM to call at least one tool
        )

        # Check if the model wants to call a tool
        if response.choices[0].message.tool_calls:
            # Add the assistant's response to messages
            messages.append(response.choices[0].message)
            
            # Execute each tool call
            for tool_call in response.choices[0].message.tool_calls:
                logger.info(f"Executing tool: {tool_call.function.name}")
                
                # Execute the tool function
                tool_result = execute_tool_call(tool_call, auth_token)
                logger.info(f"Tool result success: {tool_result.get('success', False)}")
                
                # Process MTR document if binary data is present (original sophisticated functionality)
                if tool_result.get("success") and isinstance(tool_result.get("data"), dict):
                    data = tool_result["data"]
                    if "Obj" in data and data["Obj"]:
                        try:
                            # Get the first document
                            first_obj = data["Obj"][0]
                            binary_string = first_obj.get("BinaryString")
                            
                            if binary_string:
                                # Initialize processor for sophisticated OCR
                                processor = MTRProcessor()
                                
                                # Extract heat number from tool arguments for file naming
                                arguments = json.loads(tool_call.function.arguments)
                                heat_number = arguments.get("heat_number", "unknown")
                                
                                # Process MTR document with original sophisticated OCR
                                pdf_path = None
                                try:
                                    pdf_path = processor.convert_binary_to_pdf(binary_string, heat_number)
                                    extracted_text = processor.extract_text_from_pdf(pdf_path)
                                    
                                    if extracted_text:
                                        # Use original sophisticated property analysis
                                        analyzed_response = processor.analyze_mtr_properties(user_input, extracted_text, first_obj)
                                        
                                        # Replace the tool result data with analyzed response
                                        tool_result["data"] = analyzed_response
                                        logger.info("MTR document processed successfully with OCR")
                                    
                                except Exception as e:
                                    logger.error(f"MTR document processing failed: {str(e)}")
                                    tool_result["processing_error"] = str(e)
                                finally:
                                    # Clean up temporary PDF file
                                    if pdf_path and os.path.exists(pdf_path):
                                        try:
                                            os.remove(pdf_path)
                                            logger.info(f"Cleaned up temporary file: {pdf_path}")
                                        except:
                                            pass
                            
                        except Exception as e:
                            logger.error(f"MTR document processing failed: {str(e)}")
                            tool_result["processing_error"] = str(e)
                
                # Add tool result to messages
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(tool_result) if isinstance(tool_result, (dict, list)) else str(tool_result)
                })
            
            # Get final response from the model - it will format the results naturally
            final_response = azure_client.chat.completions.create(
                model=azureopenai,
                messages=messages
            )
            
            return final_response.choices[0].message.content
        else:
            # No tool calls needed, return direct response
            return response.choices[0].message.content

    except Exception as e:
        logger.error(f"Error in MTR agent processing: {str(e)}")
        return f"Error in MTR processing: {str(e)}"