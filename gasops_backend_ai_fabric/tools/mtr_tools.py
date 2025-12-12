# MTR Tools - Material Test Report API Functions
# Individual tool functions for OpenAI function calling integration
# Handles parameter mapping and API communication for MTR-related operations

from tools.execute_api import execute_api

def GetMTRFileDatabyHeatNumber(heat_number=None, company_mtr_file_id=None, auth_token=None):
    """
    Retrieve Material Test Report file data by heat number.
    
    Fetches MTR documents and associated metadata for material analysis.
    Supports both heat number and company MTR file ID for flexible querying.
    
    Args:
        heat_number (str, optional): Material heat number identifier
        company_mtr_file_id (str, optional): Company-specific MTR file identifier
        auth_token (str, optional): Authentication token for API access
        
    Returns:
        dict: API response containing MTR data, binary documents, and metadata
        
    Note:
        - API expects 'heatNumber' and 'companyMTRFileID' parameter names
        - Binary document data is included for OCR processing
        - At least heat_number should be provided for meaningful results
    """
    parameters = {
        "heatNumber": heat_number,  # API expects heatNumber format
        "companyMTRFileID": company_mtr_file_id  # API expects companyMTRFileID format
    }
    # Clean parameters by removing None values for efficient API calls
    parameters = {k: v for k, v in parameters.items() if v is not None}
    return execute_api("AIMTRMetaData", "GetMTRFileDatabyHeatNumber", parameters, auth_token, method="GET")

def get_mtr_tools():
    """
    Define OpenAI function calling tools for MTR operations.
    
    Returns tool definitions in OpenAI function calling format for AI agent integration.
    These tools enable intelligent parameter extraction and API interaction.
    
    Returns:
        list: OpenAI tool definitions for MTR-related functions
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "GetMTRFileDatabyHeatNumber",
                "description": "Get MTR (Material Test Report) file data and properties by heat number.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "heat_number": {
                            "type": "string",
                            "description": "Material heat number identifier (required)"
                        },
                        "company_mtr_file_id": {
                            "type": "string", 
                            "description": "Company MTR file identifier (optional)"
                        }
                    },
                    "required": ["heat_number"]
                }
            }
        }
    ]