import os
from typing import List, Optional
from dotenv import load_dotenv
from config.azure_client import get_azure_chat_openai

# Load environment variables from .env file if present
load_dotenv()


def rewrite_question(prev_msgs: Optional[List[dict]], current_question: str, auth_token: Optional[str] = None) -> str:
    """
    Given previous messages and the current user question, rewrite the question to be clear and self-contained.
    Handles both follow-up/clarification and fresh questions. Includes current date and time in the context.
    """
    context = ""
    if prev_msgs:
        for i, msg in enumerate(prev_msgs[-5:]):
            # Support both dict and object (e.g., Pydantic/BaseModel) types
            role = msg['role'] if isinstance(msg, dict) else getattr(msg, 'role', '')
            content = msg['content'] if isinstance(msg, dict) else getattr(msg, 'content', '')
            context += f"Previous message {i+1} ({role}): {content}\n"
    context += f"Current user question: {current_question}\n"
    token = auth_token if auth_token else "No auth token provided."
    print(f"[contextllm] Using auth token: {token}")
    # Print the context being sent to the LLM
    print("=== Context sent to contextllm ===")
    print(context)
    print("==================================")

    system_prompt = (
        """
        You are an expert AI assistant specialized in rewriting user questions to be clear and self-contained.
        Your task is to analyze the previous conversation context and the current user question, and rewrite the question accordingly.
        
    
        **General Rewrite Rules:**
        - Only treat the current question as a clarification/selection if:
          a) The user is selecting from a numbered list shown by the assistant, OR
          b) The user is confirming a specific suggestion from the assistant (e.g., "yes" after "do you mean X?"), OR
          c) The current question is a SHORT fragment (1-3 words) that clearly references the previous question
        - If the question is a greeting, new topic, or completely new question, return it as is WITHOUT modification.
        - Never change, expand, infer, or reinterpret the user's terms, names, or entities unless the user is explicitly confirming a selection.
        - If the current question is a COMPLETE, STANDALONE question (not a fragment), return it EXACTLY as provided.
        - Do NOT combine the current question with previous context unless the current question is clearly incomplete or a reference.
       
       
        **Examples:**
        - Previous: "Show me welders", Current: "show me work orders" → Return: "show me work orders" (NEW question)
        - Previous: "Hello", Current: "show me work orders" → Return: "show me work orders" (NEW question)
        -Previous: "How many projects are in queens which are still in progress?", Current: "Give me the projects ending with 16" → Return: "Give me the projects ending with 16" (NEW complete question, do NOT add Queens or in progress)
        
        Return only the rewritten question.
        """
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": context}
    ]

    # Use Azure OpenAI client
    azure_client, azureopenai = get_azure_chat_openai()
    response = azure_client.chat.completions.create(
        model=azureopenai,
        messages=messages,
        max_tokens=256,
        temperature=0.2
    )
    
    rewritten = response.choices[0].message.content.strip()
    print(f"[contextllm] Rewritten question: {rewritten}")
    return rewritten