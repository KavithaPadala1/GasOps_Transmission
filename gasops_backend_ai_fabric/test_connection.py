"""Test connection to Microsoft Fabric Gold_WH warehouse and execute sample queries."""


import pyodbc
from azure.identity import DefaultAzureCredential
import struct

def test_fabric_sql_connection():
    """Test connection to Microsoft Fabric SQL Endpoint"""
    
    # Your Fabric SQL endpoint
    server = "w3qy24yijqqencf2hpyf3pxrf4-6trn5wecf2euff2i4t5hv6xiy4.datawarehouse.fabric.microsoft.com"
    database = "Gold_WH"  
    
    try:
        # Get Azure AD token
        credential = DefaultAzureCredential()
        token = credential.get_token("https://database.windows.net/.default")
        
        # Convert token to the format expected by ODBC
        token_bytes = token.token.encode("utf-16-le")
        token_struct = struct.pack(f'<I{len(token_bytes)}s', len(token_bytes), token_bytes)
        
        # Connection string for Azure SQL with token authentication
        connection_string = (
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            # f"DRIVER={{FreeTDS}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"Encrypt=yes;"
            f"TrustServerCertificate=no;"
            f"Connection Timeout=30"
        )
        
        # Establish connection
        print("Attempting to connect to Fabric SQL endpoint...")
        conn = pyodbc.connect(connection_string, attrs_before={1256: token_struct})
        
        print("✓ Connection successful!\n")
        
        cursor = conn.cursor()
        
        # Execute query to get current database
        print("EXECUTING QUERY: SELECT DB_NAME() AS CurrentDatabase\n")
        cursor.execute("SELECT DB_NAME() AS CurrentDatabase")
        result = cursor.fetchone()
        print(f"Current Database: {result.CurrentDatabase}\n")
        
        # Execute query to list all tables
        print("LISTING ALL TABLES IN DATABASE\n")
        
        tables_query = """
        SELECT 
            s.name AS SchemaName,
            t.name AS TableName,
            t.create_date AS CreatedDate,
            t.modify_date AS ModifiedDate
        FROM sys.tables t
        INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
        ORDER BY s.name, t.name
        """
        
        cursor.execute(tables_query)
        tables = cursor.fetchall()
        
        if tables:
            print(f"Found {len(tables)} table(s):\n")
            print(f"{'Schema':<20} {'Table Name':<40} {'Created':<20} {'Modified':<20}")
            print("-" * 100)
            
            for table in tables:
                schema = table.SchemaName
                table_name = table.TableName
                created = table.CreatedDate.strftime('%Y-%m-%d %H:%M:%S') if table.CreatedDate else 'N/A'
                modified = table.ModifiedDate.strftime('%Y-%m-%d %H:%M:%S') if table.ModifiedDate else 'N/A'
                print(f"{schema:<20} {table_name:<40} {created:<20} {modified:<20}")
        else:
            print("No tables found in the database.")
        
        # For each requested table, print columns, datatypes, and 5 sample rows
        tables_to_check = ["welddetails", "project_workorderdetails", "EmployeeMasterNew"]
        for table in tables_to_check:
            print("\n" + "="*100)
            print(f"TABLE: {table}")
            print("-" * 100)
            # Get columns and datatypes
            columns_query = f"""
                SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, NUMERIC_PRECISION, NUMERIC_SCALE, IS_NULLABLE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = '{table}'
                ORDER BY ORDINAL_POSITION
            """
            cursor.execute(columns_query)
            columns_info = cursor.fetchall()
            if columns_info:
                print(f"{'#':<5} {'Column Name':<35} {'Data Type':<20} {'Max Length':<15} {'Nullable':<10}")
                print("-" * 100)
                for idx, col in enumerate(columns_info, 1):
                    col_name = col.COLUMN_NAME
                    data_type = col.DATA_TYPE
                    if col.CHARACTER_MAXIMUM_LENGTH:
                        max_length = str(col.CHARACTER_MAXIMUM_LENGTH)
                    elif col.NUMERIC_PRECISION:
                        max_length = f"({col.NUMERIC_PRECISION},{col.NUMERIC_SCALE})"
                    else:
                        max_length = 'N/A'
                    nullable = col.IS_NULLABLE
                    print(f"{idx:<5} {col_name:<35} {data_type:<20} {max_length:<15} {nullable:<10}")
            else:
                print("No columns found for this table.")
        # Close connection
        cursor.close()
        conn.close()
        print("\n✓ Query completed successfully!")
        return True
        
    except Exception as e:
        print(f"✗ Query failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_fabric_sql_connection()

