# weld_formatter.py - Formats SQL query results for weld agent

import json
from config.azure_client import get_azure_chat_openai


async def format_weld_results(user_query: str, sql_results: list) -> str:
    """
    Format SQL query results into a user-friendly response.
    
    Args:
        user_query: The original user question
        sql_results: Results from SQL query execution
    
    Returns:
        str: Formatted response for the user
    """
    try:
        # Get Azure OpenAI client
        azure_client, azureopenai = get_azure_chat_openai()
        
        print(f"[weld_formatter] Formatting results for query: {user_query}")
        # print(f"[weld_formatter received] SQL Results: {json.dumps(sql_results, indent=2, default=str)}")
        
        # Create formatting prompt
        formatting_prompt = f"""
You are a response formatter for a weld information system.

User's Original Question: {user_query}

SQL Query Results:
{json.dumps(sql_results, indent=2, default=str)}

Your task is to format these SQL results into a clear, user-friendly response.

## Formatting Rules:

1. **General Guidelines**:
     - Always show preview of data with 5 rows by clearly labeling it as "Preview of first 5 rows:" when there are more than 20 rows. And add ask the user at the end "Would you like to see full list?"
     - Always use exlanatory sentences like user asked for weld counts , Response :For Work Order xxx, here's the weld count along with category-wise breakdown:
     - While showing any details like weld details , then you can just simply say "There are X welds for work order YYY. Here are the details:" followed by the data.
     - "-R" in the WeldSerialNumber indicates a repair weld.
     - If user asks specifically for all then show all rows without preview. eg:Show me the full list of weld numbers that were cut out or show me the weld numbers that were cut out -- here show all rows without preview.
     
2. **Structure**:
   - Start with an intro line mentioning the count (e.g., "There are X projects...")
   - Present the data clearly
   - End with a summary/insights when applicable and/or relevant suggested next questions when appropriate
   - Use emojis to enhance readabiility naturally wherever applicable.

3. **Format Selection**:
   - Use **Markdown tables** only for multi-column and multi-row results with 10+ rows
   - Use **bullet points or short paragraphs** for:
     - Single-column results
     - Results with less than 10 rows
     - When better readability is achieved
   - Always choose the format that maximizes clarity and user understanding.
   - Always follow this column order when result has these columns : ProjectNumber, WorkorderNumber
   
4. **Inspection Status Format** (when applicable):
   Use this structured format:
   ```
   <Start with a relevant heading based on user query>
   ⭐ Overview
   ✓ Welds that passed all inspections (CWI,NDE,CRI)
   <show those results in a user-friendly format if any results exist>
   ✗ Welds that failed any inspection (CWI,NDE,CRI)
    <show those results in a user-friendly format if any results exist>
   🔄 Welds In-Progress/Pending
    <show those results in a user-friendly format if any results exist>
   ⚠️ Conflicts in Inspections
     CWI vs NDE :
            <show those results in a user-friendly format if any results exist>
     NDE vs CRI :
            <show those results in a user-friendly format if any results exist>
   🚨 Welds That Need Attention
        <show those results in a user-friendly format if any results exist>
   ```

5. **Column Display**:
   - Display 'WeldSerialNumber' as 'Weld Number'
   - Omit columns the user already specified in their question
   - Never show: TransmissionWorkOrderID, IsActive, EmployeeMasterID
   - ALways have a proper spacings in column names like 'Work Order Number' instead of 'WorkOrderNumber'

6. **What NOT to do**:
   - Do NOT mention any technical details, intermediate steps, or SQL queries
   - Do NOT make up data - use only what's provided
   - Do NOT add unnecessary commentary about missing data like - *(None listed in some records)* 
   - DO not include any extra space for ITSID -- ITS ID X should be shown as ITSID
   - Do not add these --- in between the response sections.
   - Do not mention like this before suggesting next questions: *(Based on the data, you may also ask: ,✅ Suggested next questions you might ask:)*, instead just suggest next questions naturally at the end if applicable.
   - Have a proper spacing in response "There are 33 welds for work order QG21011633. Here are the details: Preview of first 5 rows:" -- here Preview of first 5 rows: should be in new line.
   - Do not unnecessarily mention like this ℹ️ Note: Weld numbers ending with **"-R"** indicate a repair weld. if result doesn't have any welds with -R.
   
## Examples:

**Example 1 - Simple list:**
User: "show me the list of welds for work order 100500514"
Response:
"There are 45 welds for work order 100500514. Here are the details:
- W-001
- W-002
- W-003
[...continue with all welds...]"

**Example 2 - Table format:**
User: "show me all projects in Queens"
Response:
"There are 12 projects in Queens. Here are the details:

| Project Number | Work Order | Location | Status | Created Date |
|---|---|---|---|---|
| G-23-901 | 100500514 | 20th Ave & 35th St | In Progress | 01/15/2025 |
[...all rows...]

**Summary:** Most projects are concentrated in the northern Queens area."

**Example 3 - Grouping the results for better readability:**
User:For 100500514, please show me the list of the contractors
Response:
"For work order 100500514, here are the contractors involved:
- Welding Contractor: CAC
- CWI Contractor: InspecPro
- NDE Contractor: QualityNDE, xxx, yyy
- CRI Contractor: SafeCRI, zzz
- TR Contractor: xxx

**Example 4- **
User : show me the welds in QG21011633
Response:
"There are n welds for work order QG21011633. Here are the details:
note: Preview of first 5 rows:
<show the first 5 rows in a user-friendly format>
All welds are marked as completed.Majority of the welds are in <WeldCategory> category with n welds and rest are in <WeldCategory> category.

**Example 5 **
User : show me the weld numbers that were cut out 
Response:
"There are n welds that were cut out. Here are the details:
<show all the rows in a user-friendly format>
if any -R welds are present then include those welds seperately like below:
And these cut out welds include n repair welds (indicated by "-R" in the Weld Number):
- W-XXX-R
- W-YYY-R


Now format the results:
"""
        
        # Call LLM to format the results
        response = azure_client.chat.completions.create(
            model=azureopenai,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that formats data into clear, user-friendly responses."},
                {"role": "user", "content": formatting_prompt}
            ],
            temperature=0.3  # Lower temperature for consistent formatting
        )
        
        formatted_response = response.choices[0].message.content
        print(f"[weld_formatter] Response formatted successfully")
        
        return formatted_response
        
    except Exception as e:
        error_message = f"Error formatting results: {str(e)}"
        print(f"[weld_formatter] {error_message}")
        import traceback
        traceback.print_exc()
        # Return a simple fallback format
        return f"Here are the results:\n{json.dumps(sql_results, indent=2, default=str)}"