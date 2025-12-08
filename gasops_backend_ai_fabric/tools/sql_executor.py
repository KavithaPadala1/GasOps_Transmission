# # sql_executor.py - SQL query execution tool using pyodbc with FreeTDS driver

# import pyodbc
# from azure.identity import DefaultAzureCredential
# from datetime import datetime
# from typing import List, Dict, Any
# import struct
# import logging

# # Suppress Azure Identity verbose logging
# logging.getLogger('azure.identity').setLevel(logging.ERROR)
# logging.getLogger('azure.core.pipeline.policies.http_logging_policy').setLevel(logging.ERROR)


# def get_fabric_connection_freetds():
#     """
#     Create and return a connection to Microsoft Fabric SQL Endpoint using pyodbc with FreeTDS driver.
#     Uses Azure AD token authentication with DefaultAzureCredential.
    
#     Returns:
#         pyodbc.Connection: Active database connection
    
#     Raises:
#         Exception: If connection fails
#     """
#     try:
#         # Fabric SQL endpoint configuration
#         server = "w3qy24yijqqencf2hpyf3pxrf4-6trn5wecf2euff2i4t5hv6xiy4.datawarehouse.fabric.microsoft.com"
#         database = "Gold_WH"
        
#         # Get Azure AD token
#         credential = DefaultAzureCredential()
#         token = credential.get_token("https://database.windows.net/.default")
        
#         # Convert token to the format expected by ODBC
#         token_bytes = token.token.encode("utf-16-le")
#         token_struct = struct.pack(f'<I{len(token_bytes)}s', len(token_bytes), token_bytes)
        
#         print(f"[get_fabric_connection_freetds] Connecting to {server}/{database}")
        
#         # Connection string using FreeTDS driver
#         connection_string = (
#             f"DRIVER={{ODBC Driver 18 for SQL Server}};"
#             f"SERVER={server};"
#             f"DATABASE={database};"
#             f"PORT=1433;"
#             f"Encrypt=yes;"
#             f"TrustServerCertificate=no;"
#         )
        
#         # Establish connection with Azure AD token
#         conn = pyodbc.connect(connection_string, attrs_before={1256: token_struct})
        
#         return conn
        
#     except pyodbc.Error as e:
#         error_msg = f"pyodbc connection error: {str(e)}"
#         print(f"[get_fabric_connection_freetds] {error_msg}")
#         raise Exception(error_msg)
#     except Exception as e:
#         error_msg = f"Unexpected connection error: {str(e)}"
#         print(f"[get_fabric_connection_freetds] {error_msg}")
#         raise Exception(error_msg)


# def execute_sql_query(sql_query: str) -> List[Dict[str, Any]]:
#     """
#     Execute a SQL SELECT query against Microsoft Fabric warehouse using pyodbc with FreeTDS.
    
#     Args:
#         sql_query: The SQL SELECT query to execute
    
#     Returns:
#         List[Dict[str, Any]]: List of dictionaries containing the query results
    
#     Raises:
#         Exception: If query execution fails
#     """
#     try:
#         print(f"[execute_sql_query] Executing query")
#         print(f"[execute_sql_query] SQL: {sql_query}")  
        
#         # Get database connection
#         conn = get_fabric_connection_freetds()
#         cursor = conn.cursor()
        
#         # Execute the query
#         cursor.execute(sql_query)
        
#         # Fetch column names
#         columns = [column[0] for column in cursor.description]
        
#         # Fetch all rows
#         rows = cursor.fetchall()
        
#         # Convert to list of dictionaries
#         results = []
#         for row in rows:
#             row_dict = {}
#             for i, column in enumerate(columns):
#                 value = row[i]
#                 # Handle datetime objects
#                 if isinstance(value, datetime):
#                     value = value.strftime('%Y-%m-%d %H:%M:%S')
#                 row_dict[column] = value
#             results.append(row_dict)
        
#         cursor.close()
#         conn.close()
        
#         print(f"[execute_sql_query] Successfully fetched {len(results)} rows")
#         print(f"SQL Query Results: {results}")
#         return results
        
#     except pyodbc.Error as e:
#         error_msg = f"Database error: {str(e)}"
#         print(f"[execute_sql_query] {error_msg}")
#         raise Exception(error_msg)
#     except Exception as e:
#         error_msg = f"Unexpected error: {str(e)}"
#         print(f"[execute_sql_query] {error_msg}")
#         raise Exception(error_msg)


# def get_sql_tool_definition() -> Dict[str, Any]:
#     """
#     Returns the OpenAI function tool definition for SQL query execution.
    
#     Returns:
#         Dict: Tool definition for OpenAI function calling
#     """
#     return {
#         "type": "function",
#         "function": {
#             "name": "execute_sql_query",
#             "description": "Executes a SQL SELECT query against the Microsoft Fabric warehouse and returns the results",
#             "parameters": {
#                 "type": "object",
#                 "properties": {
#                     "sql_query": {
#                         "type": "string",
#                         "description": "The SQL SELECT query to execute. Must be a valid SELECT statement without markdown formatting."
#                     }
#                 },
#                 "required": ["sql_query"]
#             }
#         }
#     }






import pyodbc
from azure.identity import AzureCliCredential, DefaultAzureCredential
from datetime import datetime
from typing import List, Dict, Any
import struct
import logging
import time

# Suppress Azure Identity verbose logging
logging.getLogger('azure.identity').setLevel(logging.ERROR)
logging.getLogger('azure.core.pipeline.policies.http_logging_policy').setLevel(logging.ERROR)

# Global token cache
_token_cache = {
    "token": None,
    "expires_at": 0
}


def get_fabric_token(force_refresh=False):
    """
    Get or refresh Microsoft Fabric access token with caching.
    Tokens are cached and automatically refreshed before expiration.
    
    Args:
        force_refresh: Force token refresh even if cached token is valid
    
    Returns:
        str: Valid access token for Microsoft Fabric
    
    Raises:
        Exception: If token acquisition fails
    """
    global _token_cache
    
    current_time = time.time()
    
    # Check if we have a valid cached token (with 5 min buffer before expiration)
    if not force_refresh and _token_cache["token"] and current_time < (_token_cache["expires_at"] - 300):
        expires_in_minutes = (_token_cache["expires_at"] - current_time) / 60
        print(f"[get_fabric_token] Using cached token (valid for {expires_in_minutes:.1f} more minutes)")
        return _token_cache["token"]
    
    # Need to get a new token
    print("[get_fabric_token] Acquiring new token for Microsoft Fabric Warehouse")
    
    try:
        # Try Azure CLI first (most reliable for local development)
        try:
            credential = AzureCliCredential()
            # Use the correct resource scope for Microsoft Fabric
            token_response = credential.get_token("https://analysis.windows.net/powerbi/api/.default")
            print("[get_fabric_token] ✅ Using Azure CLI credential")
        except Exception as cli_error:
            print(f"[get_fabric_token] Azure CLI failed: {str(cli_error)}")
            # Fallback to DefaultAzureCredential (for Azure-hosted environments)
            credential = DefaultAzureCredential(
                exclude_visual_studio_code_credential=True,
                exclude_powershell_credential=True,
                exclude_shared_token_cache_credential=True,
                exclude_workload_identity_credential=True,
                exclude_developer_cli_credential=True
            )
            token_response = credential.get_token("https://analysis.windows.net/powerbi/api/.default")
            print("[get_fabric_token] Using DefaultAzureCredential (ManagedIdentity)")
        
        # Cache the token
        _token_cache["token"] = token_response.token
        _token_cache["expires_at"] = token_response.expires_on
        
        expires_in_minutes = (token_response.expires_on - current_time) / 60
        print(f"[get_fabric_token] ✅ New token acquired, expires in {expires_in_minutes:.1f} minutes")
        
        return token_response.token
        
    except Exception as e:
        print(f"[get_fabric_token] ❌ Failed to acquire token: {str(e)}")
        raise Exception(f"Token acquisition failed: {str(e)}")


def get_fabric_connection_freetds():
    """
    Create and return a connection to Microsoft Fabric SQL Endpoint using pyodbc with FreeTDS driver.
    Uses Azure AD token authentication with automatic token refresh.
    
    Returns:
        pyodbc.Connection: Active database connection
    
    Raises:
        Exception: If connection fails
    """
    try:
        # Fabric SQL endpoint configuration
        server = "w3qy24yijqqencf2hpyf3pxrf4-6trn5wecf2euff2i4t5hv6xiy4.datawarehouse.fabric.microsoft.com"
        database = "Gold_WH"
        
        print(f"[get_fabric_connection_freetds] Connecting to {server}/{database}")
        
        # Get cached or fresh token
        token_str = get_fabric_token()
        
        # Convert token to the format expected by ODBC
        token_bytes = token_str.encode("utf-16-le")
        token_struct = struct.pack(f'<I{len(token_bytes)}s', len(token_bytes), token_bytes)
        
        # Connection string using FreeTDS driver
        connection_string = (
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"PORT=1433;"
            f"Encrypt=yes;"
            f"TrustServerCertificate=no;"
        )
        
        # Establish connection with Azure AD token
        conn = pyodbc.connect(connection_string, attrs_before={1256: token_struct})
        print("[get_fabric_connection_freetds] ✅ Connection established successfully")
        
        return conn
        
    except pyodbc.Error as e:
        error_msg = f"pyodbc connection error: {str(e)}"
        print(f"[get_fabric_connection_freetds] ❌ {error_msg}")
        
        # If connection fails due to token issue, retry with fresh token
        if "token" in str(e).lower() or "authentication" in str(e).lower():
            print("[get_fabric_connection_freetds] 🔄 Token might be expired, retrying with fresh token...")
            try:
                token_str = get_fabric_token(force_refresh=True)
                token_bytes = token_str.encode("utf-16-le")
                token_struct = struct.pack(f'<I{len(token_bytes)}s', len(token_bytes), token_bytes)
                conn = pyodbc.connect(connection_string, attrs_before={1256: token_struct})
                print("[get_fabric_connection_freetds] ✅ Connection established with refreshed token")
                return conn
            except Exception as retry_error:
                raise Exception(f"Connection failed even after token refresh: {str(retry_error)}")
        
        raise Exception(error_msg)
    except Exception as e:
        error_msg = f"Unexpected connection error: {str(e)}"
        print(f"[get_fabric_connection_freetds] ❌ {error_msg}")
        raise Exception(error_msg)


# def execute_sql_query(sql_query: str) -> List[Dict[str, Any]]:
#     """
#     Execute a SQL SELECT query against Microsoft Fabric warehouse using pyodbc with FreeTDS.
#     Automatically handles token expiration and retries with fresh tokens.
    
#     Args:
#         sql_query: The SQL SELECT query to execute
    
#     Returns:
#         List[Dict[str, Any]]: List of dictionaries containing the query results
    
#     Raises:
#         Exception: If query execution fails after retries
#     """
#     max_retries = 2
#     retry_count = 0
    
#     while retry_count < max_retries:
#         try:
#             print(f"[execute_sql_query] Executing query (attempt {retry_count + 1}/{max_retries})")
#             print(f"[execute_sql_query] SQL: {sql_query}")  
            
#             # Get database connection with token handling
#             conn = get_fabric_connection_freetds()
#             cursor = conn.cursor()
            
#             # Execute the query
#             cursor.execute(sql_query)
            
#             # Fetch column names
#             columns = [column[0] for column in cursor.description]
            
#             # Fetch all rows
#             rows = cursor.fetchall()
            
#             # Convert to list of dictionaries
#             results = []
#             for row in rows:
#                 row_dict = {}
#                 for i, column in enumerate(columns):
#                     value = row[i]
#                     # Handle datetime objects
#                     if isinstance(value, datetime):
#                         value = value.strftime('%Y-%m-%d %H:%M:%S')
#                     row_dict[column] = value
#                 results.append(row_dict)
            
#             cursor.close()
#             conn.close()
            
#             print(f"[execute_sql_query] ✅ Successfully fetched {len(results)} rows")
#             return results
            
#         except pyodbc.Error as e:
#             retry_count += 1
#             error_msg = f"Database error: {str(e)}"
#             print(f"[execute_sql_query] ❌ {error_msg}")
            
#             # If it's a token/auth error and we haven't exhausted retries, try again
#             if retry_count < max_retries and ("token" in str(e).lower() or "authentication" in str(e).lower()):
#                 print(f"[execute_sql_query] 🔄 Authentication error detected, retrying with fresh token...")
#                 # Clear token cache to force refresh
#                 global _token_cache
#                 _token_cache["token"] = None
#                 _token_cache["expires_at"] = 0
#                 continue
            
#             # Otherwise, raise the error
#             raise Exception(error_msg)
#         except Exception as e:
#             retry_count += 1
#             error_msg = f"Unexpected error: {str(e)}"
#             print(f"[execute_sql_query] ❌ {error_msg}")
            
#             # If it's a token/auth error and we haven't exhausted retries, try again
#             if retry_count < max_retries and ("token" in str(e).lower() or "authentication" in str(e).lower()):
#                 print(f"[execute_sql_query] 🔄 Authentication error detected, retrying with fresh token...")
#                 # Clear token cache to force refresh
#                 _token_cache["token"] = None
#                 _token_cache["expires_at"] = 0
#                 continue
            
#             # Otherwise, raise the error
#             raise Exception(error_msg)
    
#     raise Exception("Query execution failed after maximum retries")


def execute_sql_query(sql_query: str) -> List[Dict[str, Any]]:
    """
    Execute SQL query(ies) against Microsoft Fabric warehouse using pyodbc with FreeTDS.
    Supports multiple SELECT statements separated by semicolons.
    Automatically handles token expiration and retries with fresh tokens.
    
    Args:
        sql_query: The SQL query or queries to execute (can contain multiple SELECTs)
    
    Returns:
        List[Dict[str, Any]]: List of dictionaries containing all query results
    
    Raises:
        Exception: If query execution fails after retries
    """
    max_retries = 2
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            print(f"[execute_sql_query] Executing query (attempt {retry_count + 1}/{max_retries})")
            print(f"[execute_sql_query] SQL: {sql_query}")  
            
            # Get database connection with token handling
            conn = get_fabric_connection_freetds()
            cursor = conn.cursor()
            
            # Split queries by semicolon and filter out empty ones
            queries = [q.strip() for q in sql_query.split(';') if q.strip()]
            
            all_results = []
            
            # Execute each query separately
            for idx, query in enumerate(queries):
                print(f"[execute_sql_query] Executing statement {idx + 1}/{len(queries)}")
                cursor.execute(query)
                
                # Fetch column names
                columns = [column[0] for column in cursor.description]
                
                # Fetch all rows for this query
                rows = cursor.fetchall()
                
                # Convert to list of dictionaries
                for row in rows:
                    row_dict = {}
                    for i, column in enumerate(columns):
                        value = row[i]
                        # Handle datetime objects
                        if isinstance(value, datetime):
                            value = value.strftime('%Y-%m-%d %H:%M:%S')
                        row_dict[column] = value
                    all_results.append(row_dict)
                
                # If there are more queries, move to next result set
                if idx < len(queries) - 1:
                    try:
                        cursor.nextset()
                    except:
                        pass  # Some drivers don't support nextset for single queries
            
            cursor.close()
            conn.close()
            
            print(f"[execute_sql_query] ✅ Successfully fetched {len(all_results)} total rows from {len(queries)} statement(s)")
            return all_results
            
        except pyodbc.Error as e:
            retry_count += 1
            error_msg = f"Database error: {str(e)}"
            print(f"[execute_sql_query] ❌ {error_msg}")
            
            # If it's a token/auth error and we haven't exhausted retries, try again
            if retry_count < max_retries and ("token" in str(e).lower() or "authentication" in str(e).lower()):
                print(f"[execute_sql_query] 🔄 Authentication error detected, retrying with fresh token...")
                # Clear token cache to force refresh
                global _token_cache
                _token_cache["token"] = None
                _token_cache["expires_at"] = 0
                continue
            
            # Otherwise, raise the error
            raise Exception(error_msg)
        except Exception as e:
            retry_count += 1
            error_msg = f"Unexpected error: {str(e)}"
            print(f"[execute_sql_query] ❌ {error_msg}")
            
            # If it's a token/auth error and we haven't exhausted retries, try again
            if retry_count < max_retries and ("token" in str(e).lower() or "authentication" in str(e).lower()):
                print(f"[execute_sql_query] 🔄 Authentication error detected, retrying with fresh token...")
                # Clear token cache to force refresh
                _token_cache["token"] = None
                _token_cache["expires_at"] = 0
                continue
            
            # Otherwise, raise the error
            raise Exception(error_msg)
    
    raise Exception("Query execution failed after maximum retries")


def get_sql_tool_definition() -> Dict[str, Any]:
    """
    Returns the OpenAI function tool definition for SQL query execution.
    
    Returns:
        Dict: Tool definition for OpenAI function calling
    """
    return {
        "type": "function",
        "function": {
            "name": "execute_sql_query",
            "description": "Executes a SQL SELECT query against the Microsoft Fabric warehouse and returns the results",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql_query": {
                        "type": "string",
                        "description": "The SQL SELECT query to execute. Must be a valid SELECT statement without markdown formatting."
                    }
                },
                "required": ["sql_query"]
            }
        }
    }