from config.azure_client import get_azure_chat_openai
from tools.sql_executor import execute_sql_query
import json
import re


async def name_clarifier_llm(query: str, auth_token=None):
    """
    Identifies the category of an ambiguous name in the user query using a 3-step process:
    1. LLM extracts the name from user query
    2. Static SQL query searches for matches (fast, no LLM)
    3. LLM rewrites query with clarified name OR generates clarification message
    
    Args:
        query: User's original query containing an ambiguous name
    
    Returns:
        dict: Contains either rewritten query OR clarification request
    """
    
    azure_client, azureopenai = get_azure_chat_openai()
    
    print(f"[Name Clarifier] Received query: {query}")
    
    # ============================================================
    # STEP 1: LLM extracts the ambiguous name from user query
    # ============================================================
    extraction_prompt = f"""
    Extract the person's name from this query. Return ONLY the name, nothing else.
    
    User Query: {query}
    
    Examples:
    - "show me projects handled by Joseph" → Joseph
    - "how many welds did james clark complete" → james clark
    - "give me work orders for supervisor manju" → manju
    - "what projects did joseph work on" → joseph
    - "show me inspections by CWI Smith" → Smith
    
    Return only the extracted name without any additional text or formatting.
    """
    
    try:
        response = azure_client.chat.completions.create(
            model=azureopenai,
            messages=[
                {"role": "system", "content": "You extract person names from queries. Return only the name, no explanation."},
                {"role": "user", "content": extraction_prompt}
            ],
            temperature=0,
            max_tokens=50
        )
        
        extracted_name = response.choices[0].message.content.strip()
        print(f"[Name Clarifier] Extracted name: '{extracted_name}'")
        
        if not extracted_name or len(extracted_name) < 2:
            return {
                "success": False,
                "error": "Sorry, I couldn't identify a person's name in your question. 🤔\n\n"
                       "Could you please rephrase with a clear name?"
            }
    
    except Exception as e:
        print(f"[Name Clarifier] Error extracting name: {str(e)}")
        return {
            "success": False,
            "error": "Oops! I had trouble understanding that question. 😅 Could you rephrase it?"
        }
    
    # ============================================================
    # STEP 2: Execute static SQL query (NO LLM - Fast & Efficient)
    # ============================================================
    sql_query = generate_static_name_search_query(extracted_name)
    print(f"[Name Clarifier] Executing SQL query for fuzzy matching...")
    
    try:
        results = execute_sql_query(sql_query)
        
        if not results or len(results) == 0:
            return {
                "success": False,
                "error": f"Sorry, I couldn't find anyone named '{extracted_name}' in our system. 😔\n\n"
                       f"I searched across all roles:\n"
                       f"  • Project Managers & Supervisors\n"
                       f"  • Engineers & Welders\n"
                       f"  • Inspectors (CWI, CRI, NDE)\n"
                       f"  • Contractors & Technical Reps\n\n"
                       f"Please check:\n"
                       f"  ✓ Spelling of the name\n"
                       f"  ✓ Try using the full name\n"
                       f"  ✓ Verify the person exists in our system"
            }
        
        # Process results - collect all matches
        all_matches = []
        seen_combinations = set()  # Avoid duplicates
        
        for row in results:
            count = row.get("count", 0)
            category = row.get("category")
            matched_value = row.get("matched_value")
            similarity = float(row.get("similarity", 0))
            
            if count > 0 and similarity > 0 and matched_value:
                # Create unique key to avoid duplicates
                unique_key = f"{matched_value}|{category}"
                if unique_key not in seen_combinations:
                    seen_combinations.add(unique_key)
                    all_matches.append({
                        "category": category,
                        "name": matched_value,
                        "similarity": similarity
                    })
        
        if not all_matches:
            return {
                "success": False,
                "error": f"Sorry, I couldn't find anyone named '{extracted_name}' in our system. 😔"
            }
        
        # Sort by similarity (best matches first)
        all_matches.sort(key=lambda x: x["similarity"], reverse=True)
        
        print(f"[Name Clarifier] Found {len(all_matches)} match(es)")
        
        # ============================================================
        # STEP 3: LLM rewrites query OR generates clarification
        # ============================================================
        
        if len(all_matches) == 1:
            # Single match - LLM rewrites the query with clarified name
            matched = all_matches[0]
            return await handle_single_match_with_llm_rewrite(
                query, extracted_name, matched["name"], matched["category"]
            )
        else:
            # Multiple matches - LLM generates user-friendly clarification
            return await handle_multiple_matches_with_llm_clarification(
                query, extracted_name, all_matches
            )
            
    except Exception as sql_error:
        print(f"[Name Clarifier] SQL execution error: {sql_error}")
        return {
            "success": False,
            "error": "Oops! 😅 I ran into a technical issue while searching.\n\n"
                   "Please try again. If this persists, contact support."
        }


def generate_static_name_search_query(name: str) -> str:
    """
    Generate a static SQL query with parameter substitution.
    Uses fuzzy matching (SOUNDEX, LIKE) to handle typos and partial names.
    
    Args:
        name: The name to search for
    
    Returns:
        str: Complete SQL query with the name substituted
    """
    
    # Sanitize input to prevent SQL injection
    sanitized_name = name.replace("'", "''").strip()
    
    # All name categories to search
    categories = [
        "ProjectManagerName",
        "ProjectSupervisorName", 
        "ProjectEngineerName",
        "WelderName",
        "CWIName",
        "TRName",
        "WeldingContractorName",
        "ContractorCWIName",
        "ContractorNDEName",
        "ContractorCRIName"
    ]
    
    # Build UNION query for all categories
    union_parts = []
    
    for category in categories:
        query_part = f"""
        SELECT 
            COUNT(*) as count, 
            '{category}' as category, 
            {category} as matched_value,
            CASE 
                WHEN {category} LIKE '{sanitized_name}%' THEN 1.0
                WHEN SOUNDEX({category}) = SOUNDEX('{sanitized_name}') THEN 0.8
                WHEN {category} LIKE '%{sanitized_name}%' THEN 0.6
                ELSE 0.0
            END as similarity
        FROM  nameuniquetable 
        WHERE {category} IS NOT NULL
          AND {category} != ''
          AND (
              {category} LIKE '%{sanitized_name}%' 
              OR SOUNDEX({category}) = SOUNDEX('{sanitized_name}')
          )
        GROUP BY {category}
        HAVING COUNT(*) > 0
        """
        union_parts.append(query_part.strip())
    
    # Combine with UNION ALL
    full_query = "\nUNION ALL\n".join(union_parts)
    full_query += "\nORDER BY similarity DESC, count DESC"
    
    return full_query


async def handle_single_match_with_llm_rewrite(original_query: str, user_name: str, matched_name: str, category: str):
    """
    Handle case where exactly one match is found.
    Uses LLM to intelligently rewrite the query with clarified name and category.
    
    Args:
        original_query: User's original question
        user_name: Ambiguous name user typed
        matched_name: Full name found in database
        category: Role category (e.g., ProjectSupervisorName, WelderName)
    
    Returns:
        dict: Rewritten query ready for routing to appropriate agent
    """
    print(f"[Name Clarifier] Single match: {matched_name} ({category})")
    
    azure_client, azureopenai = get_azure_chat_openai()
    
    display_category = format_category_name(category)
    
    # LLM rewrites the query naturally
    rewrite_prompt = f"""
    Rewrite this query by replacing the ambiguous name with the clarified full name and role category.
    
    Original Query: {original_query}
    Ambiguous Name: {user_name}
    Actual Full Name: {matched_name}
    Role Category: {category}
    
    Rewrite the query naturally, making it clear which person is meant.
    Include both the category and full name in this format: "{category} {matched_name}"
    
    Examples:
    - Original: "show me projects handled by Joseph"
      Rewritten: "show me projects handled by ProjectSupervisorName Joseph Clark"
    
    - Original: "how many welds did james complete"
      Rewritten: "how many welds did WelderName James Martinez complete"
      
    - Original: "what inspections did smith do"
      Rewritten: "what inspections did CWIName John Smith do"
    
    Return ONLY the rewritten query, nothing else. No explanations.
    """
    
    try:
        response = azure_client.chat.completions.create(
            model=azureopenai,
            messages=[
                {"role": "system", "content": "You rewrite queries by replacing ambiguous names with clarified names and categories. Return only the rewritten query."},
                {"role": "user", "content": rewrite_prompt}
            ],
            temperature=0,
            max_tokens=150
        )
        
        rewritten_query = response.choices[0].message.content.strip()
        print(f"[Name Clarifier] Rewritten query: {rewritten_query}")
        
        return {
            "success": True,
            "original_query": original_query,
            "rewritten_query": rewritten_query,
            "name": matched_name,
            "original_name": user_name,
            "category": category,
            "display_category": display_category,
            "message": f"✓ Found: {matched_name} ({display_category})"
        }
        
    except Exception as e:
        print(f"[Name Clarifier] Error rewriting query: {str(e)}")
        # Fallback to simple replacement
        rewritten = original_query.replace(user_name, f"{category} {matched_name}")
        return {
            "success": True,
            "original_query": original_query,
            "rewritten_query": rewritten,
            "name": matched_name,
            "original_name": user_name,
            "category": category,
            "display_category": display_category
        }


async def handle_multiple_matches_with_llm_clarification(original_query: str, user_name: str, matches: list):
    """
    Handle case where multiple matches are found.
    Uses LLM to generate a friendly, conversational clarification message.
    
    Args:
        original_query: User's original question
        user_name: Ambiguous name user typed
        matches: List of matching names with categories and similarity scores
    
    Returns:
        dict: Clarification request asking user to specify which person they meant
    """
    print(f"[Name Clarifier] Multiple matches for '{user_name}': {len(matches)} found")
    
    azure_client, azureopenai = get_azure_chat_openai()
    
    # Format matches for the clarification message
    matches_list = []
    for i, match in enumerate(matches[:5]):  # Limit to top 5 matches
        display_category = format_category_name(match['category'])
        matches_list.append(f"{i+1}. **{match['name']}** - {display_category}")
    
    matches_text = "\n".join(matches_list)
    
    # LLM generates friendly clarification message
    clarification_prompt = f"""
    The user searched for "{user_name}" but we found multiple people with similar names.
    
    Matches found:
    {matches_text}
    
    Generate a friendly, conversational clarification message that:
    - Acknowledges we found multiple people
    - Lists the options clearly (already formatted above)
    - Asks the user to specify which person they meant
    - Is warm and helpful with 1-2 emojis maximum
    - Keeps it concise (2-3 sentences max)
    
    Example tone:
    "I found a few people named {user_name}! 😊 Could you please specify which one you meant?"
    
    Return ONLY the clarification message text. Include the formatted list of matches in your response.
    """
    
    try:
        response = azure_client.chat.completions.create(
            model=azureopenai,
            messages=[
                {"role": "system", "content": "You create friendly clarification messages when there are multiple matching names. Be warm, concise, and helpful."},
                {"role": "user", "content": clarification_prompt}
            ],
            temperature=0.7,
            max_tokens=250
        )
        
        clarification_message = response.choices[0].message.content.strip()
        print(f"[Name Clarifier] Generated clarification message")
        
        return {
            "success": False,
            "needs_clarification": True,
            "clarification_message": clarification_message,
            "matches": matches[:5],  # Return top 5 matches
            "original_query": original_query,
            "original_name": user_name
        }
        
    except Exception as e:
        print(f"[Name Clarifier] Error generating clarification: {str(e)}")
        # Fallback to simple clarification
        return {
            "success": False,
            "needs_clarification": True,
            "clarification_message": f"I found {len(matches)} people named '{user_name}'. 🤔\n\n{matches_text}\n\nWhich one did you mean?",
            "matches": matches[:5],
            "original_query": original_query,
            "original_name": user_name
        }


def format_category_name(category: str) -> str:
    """
    Format category name for display.
    E.g., ProjectManagerName -> Project Manager
    """
    display = category.replace("Name", "")
    display = re.sub(r'([A-Z])', r' \1', display).strip()
    return display