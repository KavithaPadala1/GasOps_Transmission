"""
Test script to verify if auth_token from frontend works with Fabric connection.
Run this to test before making changes to sql_executor.py
"""

import pyodbc
import struct
from datetime import datetime

def test_fabric_connection_with_token(auth_token: str):
    """
    Test if the provided auth_token can connect to Fabric warehouse.
    
    Args:
        auth_token: The token from your frontend/main.py
    """
    try:
        server = "w3qy24yijqqencf2hpyf3pxrf4-6trn5wecf2euff2i4t5hv6xiy4.datawarehouse.fabric.microsoft.com"
        database = "Gold_WH"
        
        print(f"Testing connection to {server}/{database}")
        print(f"Token length: {len(auth_token)} characters")
        
        # Remove 'Bearer ' prefix if present
        token_str = auth_token.replace("Bearer ", "") if auth_token.startswith("Bearer ") else auth_token
        
        # Convert token to ODBC format
        token_bytes = token_str.encode("utf-16-le")
        token_struct = struct.pack(f'<I{len(token_bytes)}s', len(token_bytes), token_bytes)
        
        # Connection string
        connection_string = (
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"PORT=1433;"
            f"Encrypt=yes;"
            f"TrustServerCertificate=no;"
        )
        
        print("Attempting connection with provided token...")
        conn = pyodbc.connect(connection_string, attrs_before={1256: token_struct})
        
        print("✅ Connection SUCCESSFUL with provided token!")
        
        # Test a simple query
        cursor = conn.cursor()
        cursor.execute("SELECT TOP 3 ProjectNumber, WorkOrderNumber FROM project_workorderdetails")
        rows = cursor.fetchall()
        
        print(f"✅ Query SUCCESSFUL! Retrieved {len(rows)} rows:")
        for row in rows:
            print(f"   - ProjectNumber: {row[0]}, WorkOrderNumber: {row[1]}")
        
        cursor.close()
        conn.close()
        
        print("\n✅ TEST PASSED: Your auth_token works with Fabric!")
        print("You can now use this token in sql_executor.py")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        print("\nThis means:")
        print("1. The token from frontend is NOT valid for Fabric access")
        print("2. You need to use Azure CLI token instead (az login)")
        print("3. Or get a different token from frontend scoped for Fabric")
        return False


def test_azure_cli_token():
    """
    Test if Azure CLI token works (fallback method).
    """
    try:
        from azure.identity import AzureCliCredential
        
        print("\nTesting Azure CLI token...")
        credential = AzureCliCredential()
        token_response = credential.get_token("https://analysis.windows.net/powerbi/api/.default")
        
        print(f"✅ Azure CLI token acquired successfully!")
        print(f"   Token expires in: {(token_response.expires_on - datetime.now().timestamp()) / 60:.1f} minutes")
        
        # Test connection with Azure CLI token
        return test_fabric_connection_with_token(token_response.token)
        
    except Exception as e:
        print(f"❌ Azure CLI token failed: {str(e)}")
        print("Run 'az login' to authenticate")
        return False


if __name__ == "__main__":
    print("=" * 70)
    print("FABRIC TOKEN TEST")
    print("=" * 70)
    
    # Option 1: Test with your frontend token (paste it here)
    frontend_token = input("\nPaste your frontend auth_token here (or press Enter to skip): ").strip()
    
    if frontend_token:
        print("\n--- Testing Frontend Token ---")
        frontend_works = test_fabric_connection_with_token(frontend_token)
    else:
        print("\nSkipping frontend token test...")
        frontend_works = False
    
    # Option 2: Test with Azure CLI token
    print("\n--- Testing Azure CLI Token ---")
    cli_works = test_azure_cli_token()
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Frontend Token: {'✅ WORKS' if frontend_works else '❌ DOES NOT WORK'}")
    print(f"Azure CLI Token: {'✅ WORKS' if cli_works else '❌ DOES NOT WORK'}")
    
    if frontend_works:
        print("\n✅ RECOMMENDATION: Use frontend token in sql_executor.py")
    elif cli_works:
        print("\n⚠️  RECOMMENDATION: Use Azure CLI token (implement token caching)")
    else:
        print("\n❌ ERROR: No working authentication method found!")
        print("   1. Run 'az login' to authenticate")
        print("   2. Or get a valid Fabric token from frontend")