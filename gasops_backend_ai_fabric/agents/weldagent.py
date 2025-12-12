# # weldagent.py - Handles weld-related queries by generating and executing SQL

# import json
# from datetime import datetime
# from zoneinfo import ZoneInfo
# from config.azure_client import get_azure_chat_openai
# from prompts.weldprompt import get_weld_prompt
# from tools.sql_executor import execute_sql_query, get_sql_tool_definition


# async def handle_weld(query: str, auth_token: str = None):
#     """
#     Weld agent that generates SQL queries based on user questions and executes them.
    
#     Flow:
#     1. Get system prompt from weldprompt.py (includes SQL generation rules and response formatting)
#     2. LLM generates SQL query using tool calling
#     3. Execute SQL query via tool
#     4. LLM formats results based on prompt instructions (single call with tool results)
    
#     Args:
#         query: User's question about welds, work orders, inspections, etc.
#         auth_token: Authentication token for API calls (if needed)
    
#     Returns:
#         dict: Response containing the formatted answer
#     """
#     try:
#         # Get Azure OpenAI client
#         azure_client, azureopenai = get_azure_chat_openai()
        
#         # Get current date/time context
#         eastern = ZoneInfo("America/New_York")
#         now = datetime.now(ZoneInfo("UTC")).astimezone(eastern)
#         current_year = now.year
#         current_date = now.strftime('%B %d, %Y')
        
#         print(f"[weldagent] Processing query: {query}")
#         print(f"[weldagent] Current year: {current_year}, Current date: {current_date}")
        
#         # Get system prompt from weldprompt.py (includes SQL rules and response formatting)
#         system_prompt = get_weld_prompt(query, current_year)
        
#         # Get SQL tool definition
#         tools = [get_sql_tool_definition()]
        
#         # Single LLM call with tool: Generate SQL, execute, and format response
#         messages = [
#             {"role": "system", "content": system_prompt},
#             {"role": "user", "content": query}
#         ]
        
#         print("[weldagent] Calling LLM with tools...")
#         response = azure_client.chat.completions.create(
#             model=azureopenai,
#             messages=messages,
#             tools=tools,
#             tool_choice="required"
#         )
        
#         response_message = response.choices[0].message
#         tool_calls = response_message.tool_calls
        
#         # If no tool call, return direct response (e.g., greetings handled by prompt)
#         if not tool_calls:
#             direct_answer = response_message.content
#             print(f"[weldagent] No tool call. Direct response from LLM.")
#             return {"answer": direct_answer}
        
#         # Process tool calls - execute SQL query
#         messages.append(response_message)
        
#         for tool_call in tool_calls:
#             function_name = tool_call.function.name
#             function_args = json.loads(tool_call.function.arguments)
            
#             if function_name == "execute_sql_query":
#                 sql_query = function_args.get("sql_query")
#                 # print(f"[weldagent] Generated SQL Query:\n{sql_query}\n")
                
#                 # Execute the SQL query
#                 try:
#                     sql_results = execute_sql_query(sql_query)
#                     print(f"[weldagent] Query returned {len(sql_results) if sql_results else 0} rows")
#                     print(f"[weldagent] SQL Results: {sql_results}")
                    
#                     # Add tool response to messages
#                     tool_response = {
#                         "role": "tool",
#                         "tool_call_id": tool_call.id,
#                         "name": function_name,
#                         "content": json.dumps(sql_results, default=str)
#                     }
#                     messages.append(tool_response)
                    
#                 except Exception as e:
#                     error_msg = f"SQL execution error: {str(e)}"
#                     print(f"[weldagent] {error_msg}")
                    
#                     # Don't expose SQL errors to user - return friendly message instead
#                     print("[weldagent] Returning user-friendly error message")
#                     return {"answer": "I apologize, but I'm having trouble retrieving that information right now. Could you please rephrase your question or try again in a moment?"}
        
#         # Get formatted response from LLM (includes tool results in context)
#         print("[weldagent] Getting formatted response from LLM...")
#         final_response = azure_client.chat.completions.create(
#             model=azureopenai,
#             messages=messages
#         )
        
#         final_answer = final_response.choices[0].message.content
#         print(f"[weldagent] Response generated successfully")
        
#         return {"answer": final_answer}
        
#     except Exception as e:
#         error_message = f"Error in weldagent: {str(e)}"
#         print(f"[weldagent] {error_message}")
#         import traceback
#         traceback.print_exc()
#         return {"answer": "I encountered an error processing your query. Please try rephrasing your question or contact support if the issue persists."}






# weldagent.py - Handles weld-related queries by generating and executing SQL

import json
from datetime import datetime
from zoneinfo import ZoneInfo
from config.azure_client import get_azure_chat_openai
from prompts.weldprompt import get_weld_sql_prompt  # Fixed: import from tools, not prompts
from tools.sql_executor import execute_sql_query, get_sql_tool_definition
from tools.weld_formatter import format_weld_results


async def handle_weld(query: str, auth_token: str = None):
    """
    Weld agent that generates SQL queries and formats results.
    
    Flow:
    1. Get system prompt for SQL generation only (simplified prompt)
    2. LLM generates SQL query using tool calling
    3. Execute SQL query
    4. Pass results to formatter for user-friendly response
    
    Args:
        query: User's question about welds, work orders, inspections, etc.
        auth_token: Authentication token for API calls (if needed)
    
    Returns:
        dict: Response containing the formatted answer
    """
    try:
        # Get Azure OpenAI client
        azure_client, azureopenai = get_azure_chat_openai()
        
        # Get current date/time context
        eastern = ZoneInfo("America/New_York")
        now = datetime.now(ZoneInfo("UTC")).astimezone(eastern)
        current_year = now.year
        current_date = now.strftime('%B %d, %Y')
        
        print(f"[weldagent] Processing query: {query}")
        print(f"[weldagent] Current year: {current_year}, Current date: {current_date}")
        
        # Get SQL generation prompt (simplified - no formatting rules)
        system_prompt = get_weld_sql_prompt(query, current_year)
        
        # Get SQL tool definition
        tools = [get_sql_tool_definition()]
        
        # LLM call to generate SQL
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]
        
        print("[weldagent] Calling LLM to generate SQL...")
        response = azure_client.chat.completions.create(
            model=azureopenai,
            messages=messages,
            tools=tools,
            tool_choice="required"
        )
        
        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls
        
        # If no tool call, return direct response (e.g., greetings)
        if not tool_calls:
            direct_answer = response_message.content
            print(f"[weldagent] No tool call. Direct response from LLM.")
            return {"answer": direct_answer}
        
        # Execute SQL query
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            if function_name == "execute_sql_query":
                sql_query = function_args.get("sql_query")
                
                # Execute the SQL query
                try:
                    sql_results = execute_sql_query(sql_query)
                    print(f"[weldagent] Query returned {len(sql_results) if sql_results else 0} rows")
                    
                    # Format results using dedicated formatter
                    print("[weldagent] Calling formatter to create user response...")
                    formatted_answer = await format_weld_results(query, sql_results)
                    
                    return {"answer": formatted_answer}
                    
                except Exception as e:
                    error_msg = f"SQL execution error: {str(e)}"
                    print(f"[weldagent] {error_msg}")
                    
                    # Return friendly error message
                    return {"answer": "I apologize, but I'm having trouble retrieving that information right now. Could you please rephrase your question or try again in a moment?"}
        
        return {"answer": "I couldn't process your request. Please try again."}
        
    except Exception as e:
        error_message = f"Error in weldagent: {str(e)}"
        print(f"[weldagent] {error_message}")
        import traceback
        traceback.print_exc()
        return {"answer": "I encountered an error processing your query. Please try rephrasing your question or contact support if the issue persists."}