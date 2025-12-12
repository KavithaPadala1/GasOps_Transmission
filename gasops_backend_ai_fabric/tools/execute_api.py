import requests
import requests_pkcs12
import tempfile
import base64
import os
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

def execute_api(api_path, api_name, parameters, auth_token, method="POST", pfx_source="./certificate/oamsapicert2023.pfx"):
    """
    Generic function to call external APIs using PKCS#12 client certificate authentication.

    This function handles secure API calls to the GasOps system using certificate-based
    authentication. It supports both file-based and base64-encoded certificates.

    Args:
        api_path (str): The API path (e.g., 'AITransmissionWorkOrder', 'AIMTRMetaData')
        api_name (str): The specific API endpoint to call
        parameters (dict): Dictionary containing all required API parameters
        auth_token (str): Authentication token for the API (masked in logs)
        method (str): HTTP method - "GET" or "POST" (default: "POST")
        pfx_source (str): Path to .pfx file or base64 string of the certificate

    Returns:
        dict: Structured response with success status, data, and status code
              Format: {"success": bool, "data": any, "status_code": int}
              Or: {"error": str} on failure

    Raises:
        No exceptions raised - all errors are captured and returned in response
    """
    url = f"https://oamsapi.gasopsiq.com/api/{api_path}/{api_name}"
    payload = parameters

    # Log API call details with sensitive data masked
    auth_token_masked = f"***{auth_token[-4:]}" if auth_token and len(auth_token) > 4 else "***"
    logger.info(f"Sending {method} request to {api_path} API '{api_name}' with {len(payload)} parameters")
    logger.info(f"Full API URL: {url}")
    logger.info(f"Request payload: {payload}")
    logger.info(f"Using auth token: {auth_token_masked}")

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "auth-token": auth_token
    }

    # Log headers (with auth-token masked for security)
    headers_for_logging = headers.copy()
    if "auth-token" in headers_for_logging:
        headers_for_logging["auth-token"] = auth_token_masked
    logger.info(f"Request headers: {headers_for_logging}")

    temp_file = None
    try:
        # Handle certificate source (file path or base64 string)
        if not os.path.isfile(pfx_source):
            logger.info("Processing base64 encoded certificate")
            try:
                cert_bytes = base64.b64decode(pfx_source)
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pfx")
                temp_file.write(cert_bytes)
                temp_file.close()
                pfx_path = temp_file.name
                logger.info("Successfully created temporary certificate file")
            except Exception as decode_err:
                logger.error(f"Failed to decode base64 certificate: {str(decode_err)}")
                return {"error": f"Failed to decode base64 certificate: {decode_err}"}
        else:
            logger.info(f"Using certificate file: {pfx_source}")
            pfx_path = pfx_source

        # Load certificate data
        with open(pfx_path, "rb") as f:
            pfx_data = f.read()
        logger.info(f"Certificate loaded, size: {len(pfx_data)} bytes")

        # Execute request based on method
        if method.upper() == "GET":
            logger.info("Executing GET request with certificate authentication")
            response = requests_pkcs12.get(
                url,
                headers=headers,
                params=payload,
                pkcs12_data=pfx_data,
                pkcs12_password=os.getenv("PFX_PASSWORD")
            )
        else:  # POST
            logger.info("Executing POST request with certificate authentication")
            response = requests_pkcs12.post(
                url,
                headers=headers,
                json=payload,
                pkcs12_data=pfx_data,
                pkcs12_password=os.getenv("PFX_PASSWORD")
            )

        # Process response
        logger.info(f"API response received with status code: {response.status_code}")
        try:
            result = response.json()
            logger.info("Successfully parsed JSON response")
            logger.info(f"Response payload: {result}")
            return {"success": True, "data": result, "status_code": response.status_code}
        except Exception as json_err:
            logger.warning(f"Failed to parse JSON response: {str(json_err)}, returning raw text")
            logger.info(f"Raw response text: {response.text}")
            return {"success": True, "data": response.text, "status_code": response.status_code}

    except Exception as e:
        logger.error(f"API call failed: {str(e)}")
        return {"error": str(e)}
    finally:
        # Clean up temporary certificate file
        if temp_file:
            try:
                os.unlink(temp_file.name)
                logger.info("Temporary certificate file cleaned up")
            except Exception as cleanup_err:
                logger.warning(f"Failed to clean up temporary file: {str(cleanup_err)}")
                pass