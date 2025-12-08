# # supervisor agent to route to subagents based on user query intent


# from config.azure_client import get_azure_chat_openai 
# from datetime import datetime  
# import json
# from datetime import datetime, timezone
# # import pytz 
# from zoneinfo import ZoneInfo 
# import os

# # from config.azure_client import get_azure_chat_completion_with_fallback  # for round robin model fallback

# # Import agent handlers
# from agents.weldagent import handle_weld
# from agents.mtragent import handle_mtr
# from agents.specsagent import handle_specs
# from tools.numberclarifier import number_clarifier_llm



# async def supervisor(query, database_name=None, auth_token=None):

#     # Get Azure OpenAI client
#     azure_client, azureopenai = get_azure_chat_openai()
#     print("Supervisor received query:", query)
    
#      # Calculate current time INSIDE the function so it's fresh on each request
#     eastern = ZoneInfo("America/New_York")  
#     now = datetime.now(ZoneInfo("UTC")).astimezone(eastern)  
#     time = now.strftime("%Y-%m-%d %H:%M:%S")
#     current_date = now.strftime('%B %d, %Y')
#     current_year = now.year
#     current_date_mmddyyyy = now.strftime('%m/%d/%Y')
    
#     print(f"Current date: {current_date}, Current date mm/dd/yyyy: {current_date_mmddyyyy}, Current year: {current_year}, Current time: {time}")
    
    
#     # # Load supervisor examples from file
#     # examples_path = os.path.join(os.path.dirname(__file__), '..', 'aisearch', 'supervisor_examples.txt')
#     # try:
#     #     with open(examples_path, 'r', encoding='utf-8') as f:
#     #         examples = f.read()
#     # except Exception:
#     #     examples = ""

#     # Use LLM prompt for all intent detection and response
#     prompt = (
#         f"""
#         You are a supervisor managing a team of specialized agents. Your job is to understand the user's intent from their question and respond appropriately.

#         User question: {query}
        
#         Context:
#         - Today's date is {current_date}, current year is {current_year}, and the time is {time}.
#         - Always greet the user if they greet you and say I can help you with information about the welds, inspections, MTR and specs as appropriate. Do not give previous context in responses to greetings.
#         - If the user asks a general question (e.g., about today's date, weather,general engineering, design calculations, standards, formulas, or topics about pipe properties, MAOP, wall thickness, steel grade, ASME codes, etc.), answer it directly and concisely and do not invoke any agent.
#         - For weather questions, if you do not have real-time data, provide an approximate.
#         - If the user's question is a follow-up (short or ambiguous) to a previous domain-specific question, route it to the same agent as before unless the intent clearly changes.
#         - When answering direct questions, you can use emojis to make the response more engaging.
        
#         Tools:
#         You have these two tools when user questions has number or name ambiguity:
#         1. numberclarifier : Always use 'numberclarifier' tool to clarify any ambiguous numbers (e.g., WorkOrderNumber, ProjectNumber, WeldSerialNumber) before routing to an agent.
#             eg: "How many engineers are handling G23309?   -- here the number G23309 is ambiguous, it can be a WorkOrderNumber or ProjectNumber or WeldSerialNumber.
#         2. nameclarifier : Always use 'nameclarifier' tool to clarify any ambiguous names (e.g., WelderName, ContractorName, SupervisorName) before routing to an agent.
#             eg: "give me the work orders assigned to manju"  -- here the name manju is ambiguous, it can be a WelderName or ContractorName or SupervisorName.
#         - These tools will return the user query by clearly specifying the intended number or name type, which you can then use to route to the appropriate agent.
#         - If the user query clealry specifies the number or name type, direct route to the appropriate agent.
#           eg: "who is the engineer for ProjectNumber G-23-901?   -- directly route to weldagent without using numberclarifier tool.
        
        
#         Available agents and their domains:
#         1.weldagent : Handles queries related to work orders, welds, weld details, heat number traceability, NDE reports, inspection results, welders, contractors, projects, regions, and material information in the context of work orders and welds. Use this when user asks about work orders, finding work orders by heat number, weld serial numbers, or getting heat numbers for a work order.
#         2.mtragent : Handles queries related to material test report (MTR) documents, detailed material properties from MTR files, chemical composition, mechanical properties, standards compliance (API 5L, ASME), and MTR-specific heat number data. Use this when user asks for MTR data, material properties, chemical composition, or test report details for a heat number.
#         3.specsagent : Handles queries about specifications, compliance requirements, regulatory standards, technical specifications, welding requirements, pipeline standards, material specifications, inspection procedures, and any questions requiring reference to specification documents. Use this when user asks about specs, requirements, standards, procedures, or "what is required for..."

        
#         Rules :
#         - You do NOT answer domain-specific queries yourself. Instead, you:
#         - Interpret the user’s query.
#         - Decide which subagent(s) should handle it.
#         - Route the query to the correct subagent(s) based on scope, domain, and context.
#         - Maintain strict boundaries: only return general answers if the query is outside agent scope (e.g., greetings, date, time, weather,general engineering, design calculations, standards, formulas, or topics about pipe properties, MAOP, wall thickness, steel grade, ASME codes, etc.).
#         - If the query is ambiguous, ask for clarification before routing.
#         - If the question is a follow-up to a previous agent interaction, and the intent is unclear, prefer routing to the previous agent.
                                     

#         Respond in the following format:
#         - If general question: {{"answer": "<direct answer>"}}
#         - If agent required: {{"agent": "<agent name>"}}
#         - If user question is ambiguous: {{"answer": "<ask for clarification clearly>"}}
#         - If number ambiguity : {{"tool": "numberclarifier"}}
#         - If name ambiguity : {{"tool": "nameclarifier"}}
#         """
#     )
   

#     # Send query to Azure OpenAI 
#     response = azure_client.chat.completions.create(
#     # response = get_azure_chat_completion_with_fallback(  ## for gpt load balancing
#     model=azureopenai,
#     messages=[
#         {"role": "system", "content": prompt},
#         {"role": "user", "content": query}
#     ]
#     )
#     result = response.choices[0].message.content.strip()
#     print("Supervisor LLM response:", result)
#     # Try to parse the LLM response
#     try:
#         parsed = json.loads(result)
#         print("Parsed response:", parsed)
#     except Exception:
#         parsed = {"answer": result}
#         print("Failed to parse response as JSON. Treating as direct answer.", parsed)
    
    
#     # Handle numberclarifier tool
#     if parsed.get("tool") == "numberclarifier":
#         print("Routing to numberclarifier tool")
#         clarifier_result = await number_clarifier_llm(query, auth_token)
        
#         if clarifier_result.get("success"):
#             # Recursively call supervisor with rewritten query and flag set
#             rewritten_query = clarifier_result.get("rewritten_query")
#             print(f"Number clarified. Reprocessing with: {rewritten_query}")
#             return await supervisor(rewritten_query, database_name, auth_token, clarification_done=True)
#         else:
#             # Return error message to user when number not found
#             error_message = clarifier_result.get("error", "Unable to clarify the number in your query.")
#             print(f"Number clarification failed: {error_message}")
#             return {
#                 "answer": error_message
#             }
    
#     if parsed.get("tool") == "nameclarifier":
#         print("Routing to nameclarifier tool")
#         return {"tool": "nameclarifier", "query": query}
    
    
#     # Route to appropriate agent based on parsed response
#     if parsed.get("agent") == "weldagent":
#         print("Routing to weldagent")
#         return await handle_weld(query, auth_token)
#     elif parsed.get("agent") == "mtragent":
#         print("Routing to mtragent")
#         return await handle_mtr(query, auth_token)
#     elif parsed.get("agent") == "specsagent":
#         print("Routing to specsagent")
#         return await handle_specs(query, auth_token)
    
#     return parsed






# supervisor agent to route to subagents based on user query intent

from config.azure_client import get_azure_chat_openai 
from datetime import datetime  
import json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo 
import os

# Import agent handlers
from agents.weldagent import handle_weld
from agents.mtragent import handle_mtr
from agents.specsagent import handle_specs
from tools.numberclarifier import number_clarifier_llm
from tools.nameclarifier import name_clarifier_llm


async def supervisor(query, database_name=None, auth_token=None, clarification_done=False):
    """
    Supervisor agent that routes queries to specialized agents.
    
    Args:
        query: User's question
        database_name: Database name (optional)
        auth_token: Authentication token
        clarification_done: Flag to prevent infinite recursion after clarification
    """

    # Get Azure OpenAI client
    azure_client, azureopenai = get_azure_chat_openai()
    print("Supervisor received query:", query)
    
    # Calculate current time INSIDE the function so it's fresh on each request
    eastern = ZoneInfo("America/New_York")  
    now = datetime.now(ZoneInfo("UTC")).astimezone(eastern)  
    time = now.strftime("%Y-%m-%d %H:%M:%S")
    current_date = now.strftime('%B %d, %Y')
    current_year = now.year
    current_date_mmddyyyy = now.strftime('%m/%d/%Y')
    
    print(f"Current date: {current_date}, Current date mm/dd/yyyy: {current_date_mmddyyyy}, Current year: {current_year}, Current time: {time}")
    
    # Build clarification context
    clarification_note = ""
    if clarification_done:
        clarification_note = """
        IMPORTANT: The query has already been clarified with specific number/name categories (e.g., ProjectNumber, WorkOrderNumber, etc.). 
        DO NOT route to numberclarifier or nameclarifier again. 
        Route directly to the appropriate agent based on the clarified query.
        """
    
    # Use LLM prompt for all intent detection and response
    prompt = (
        f"""
        You are a supervisor managing a team of specialized agents. Your job is to understand the user's intent from their question and respond appropriately.

        User question: {query}
        
        {clarification_note}
        
        Context:
        - Today's date is {current_date}, current year is {current_year}, and the time is {time}.
        - Always greet the user if they greet you and say I can help you with information about the welds, inspections, MTR and specs as appropriate. Do not give previous context in responses to greetings.
        - If the user asks a general question (e.g., about today's date, weather, general engineering, design calculations, standards, formulas, or topics about pipe properties, MAOP, wall thickness, steel grade, ASME codes, etc.), answer it directly and concisely and do not invoke any agent.
        - For weather questions, if you do not have real-time data, provide an approximate.
        - If the user's question is a follow-up (short or ambiguous) to a previous domain-specific question, route it to the same agent as before unless the intent clearly changes.
        - When answering direct questions, you can use emojis to make the response more engaging.
        
        Tools:
        You have these two tools when user questions has number or name ambiguity:
        1. numberclarifier : Use 'numberclarifier' tool ONLY if the query contains an ambiguous number WITHOUT a category prefix (e.g., "G23309" is ambiguous, but "ProjectNumber G23309" is NOT ambiguous).
            Example ambiguous: "How many engineers are handling G23309?" -- number G23309 needs clarification
            Example clear: "who is the engineer for ProjectNumber G23309?" -- already clarified, route to agent
            Note: Even if user is asking a verification question (e.g., "Is X a work order number?"), still use numberclarifier to identify what X actually is.
        2. nameclarifier : Use 'nameclarifier' tool ONLY if the query contains an ambiguous name WITHOUT a role prefix.
            Example ambiguous: "give me the work orders assigned to manju" -- name manju needs clarification
            Example clear: "give me the work orders assigned to WelderName manju" -- already clarified, route to agent
            Example clear: "give me the list of work orders supervised by Waqar" -- already clarified as supervised means SupervisorName, route to agent.
        - These tools will return either the actual category of the number/name OR a direct answer for verification questions.
        
        Available agents and their domains:
        1. weldagent : Handles queries related to work orders, welds, weld details, heat number traceability, NDE reports, inspection results, welders, contractors, projects, regions, and material information in the context of work orders and welds.
        2. mtragent : Handles queries related to material test report (MTR) documents, detailed material properties from MTR files, chemical composition, mechanical properties, standards compliance (API 5L, ASME), and MTR-specific heat number data.
        3. specsagent : Handles queries about specifications, compliance requirements, regulatory standards, technical specifications, welding requirements, pipeline standards, material specifications, inspection procedures, and any questions requiring reference to specification documents.

        Rules :
        - You do NOT answer domain-specific queries yourself. Instead, you interpret, decide, and route.
        - Maintain strict boundaries: only return general answers if the query is outside agent scope.
        - If the query is ambiguous, ask for clarification before routing.

        Respond in the following format:
        - If general question: {{"answer": "<direct answer>"}}
        - If agent required: {{"agent": "<agent name>"}}
        - If user question is ambiguous: {{"answer": "<ask for clarification clearly>"}}
        - If number ambiguity (ONLY if no category prefix exists): {{"tool": "numberclarifier"}}
        - If name ambiguity (ONLY if no role prefix exists): {{"tool": "nameclarifier"}}
        """
    )

    # Send query to Azure OpenAI 
    response = azure_client.chat.completions.create(
        model=azureopenai,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": query}
        ]
    )
    result = response.choices[0].message.content.strip()
    print("Supervisor LLM response:", result)
    
    # Try to parse the LLM response
    try:
        parsed = json.loads(result)
        print("Parsed response:", parsed)
    except Exception:
        parsed = {"answer": result}
        print("Failed to parse response as JSON. Treating as direct answer.", parsed)
    
    # Handle numberclarifier tool
    if parsed.get("tool") == "numberclarifier" and not clarification_done:
        print("Routing to numberclarifier tool")
        clarifier_result = await number_clarifier_llm(query, auth_token)
        
        # Check if clarifier returned a direct answer (for verification questions)
        if clarifier_result.get("answer"):
            print(f"Number clarifier provided direct answer: {clarifier_result.get('answer')}")
            return {
                "answer": clarifier_result.get("answer")
            }
        
        if clarifier_result.get("success"):
            # For non-verification questions, rewrite and route to agent
            rewritten_query = clarifier_result.get("rewritten_query")
            print(f"Number clarified. Reprocessing with: {rewritten_query}")
            return await supervisor(rewritten_query, database_name, auth_token, clarification_done=True)
        else:
            # Return error message to user when number not found
            error_message = clarifier_result.get("error", "Unable to clarify the number in your query.")
            print(f"Number clarification failed: {error_message}")
            return {
                "answer": error_message
            }
            
            
    # Handle nameclarifier tool
    if parsed.get("tool") == "nameclarifier" and not clarification_done:
        print("Routing to nameclarifier tool")
        clarifier_result = await name_clarifier_llm(query, auth_token)
        
        # Check if name clarifier needs user input for multiple matches
        if clarifier_result.get("needs_clarification"):
            print(f"Name clarifier needs user clarification")
            return {
                "answer": clarifier_result.get("clarification_message"),
                "needs_clarification": True,
                "matches": clarifier_result.get("matches"),
                "original_query": clarifier_result.get("original_query")
            }
        
        if clarifier_result.get("success"):
            # Single match found - rewrite and route to agent
            rewritten_query = clarifier_result.get("rewritten_query")
            print(f"Name clarified. Reprocessing with: {rewritten_query}")
            return await supervisor(rewritten_query, database_name, auth_token, clarification_done=True)
        else:
            # Return error message when name not found
            error_message = clarifier_result.get("error", "Unable to clarify the name in your query.")
            print(f"Name clarification failed: {error_message}")
            return {
                "answer": error_message
            }
    
    # Handle nameclarifier tool
    if parsed.get("tool") == "nameclarifier" and not clarification_done:
        print("Routing to nameclarifier tool")
        return {"answer": "Name clarifier is not yet implemented. Please specify the name type in your query."}
    
    # Route to appropriate agent based on parsed response
    if parsed.get("agent") == "weldagent":
        print("Routing to weldagent")
        return await handle_weld(query, auth_token)
    elif parsed.get("agent") == "mtragent":
        print("Routing to mtragent")
        return await handle_mtr(query, auth_token)
    elif parsed.get("agent") == "specsagent":
        print("Routing to specsagent")
        return await handle_specs(query, auth_token)
    
    return parsed