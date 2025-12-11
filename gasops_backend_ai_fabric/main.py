from fastapi import FastAPI, Header, Body
from fastapi.middleware.cors import CORSMiddleware
import logging
from pydantic import BaseModel
from typing import List, Optional
from config.decryption import decode
from agents.supervisor import supervisor
from agents.contextllm import rewrite_question
from datetime import datetime, timezone, timedelta
import json

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Message(BaseModel):
    role: str
    content: str

class AskRequest(BaseModel):
    query: str
    prev_msgs: Optional[List[Message]] = None
    token: Optional[str] = None

print("Main module loaded successfully.")

@app.post("/ask")
async def ask(
    body: AskRequest = Body(...),
    encoded_string: str = Header(...)
):
    print(f"Received request body: {body}")

    query = body.query
    prev_msgs = body.prev_msgs or []

    # Initialize variables early
    database_name = None
    decrypted_fields = {}
    auth_token = None

    # Process encoded_string and generate auth_token first
    if encoded_string:
        try:
            decrypted = decode(encoded_string)
            print(f"Decrypted token: {decrypted}")
            database_name = decrypted.get("Database_Name")
            decrypted_fields = {
                "LoginMasterID": decrypted.get("LoginMasterID"),
                "Database_Name": decrypted.get("Database_Name"),
                "OrgID": decrypted.get("OrgID")
            }
            
            # Generate auth_token for barcode api (moved here)
            if decrypted_fields:
                import base64
                now_utc = datetime.now(timezone.utc)
                date_plus_one = (now_utc + timedelta(days=1)).isoformat()
                date_now = now_utc.isoformat()
                token_str = f"{date_plus_one}&{decrypted_fields.get('LoginMasterID')}&{decrypted_fields.get('Database_Name')}&{date_now}&{decrypted_fields.get('OrgID')}"
                def encode_base64(text: str) -> str:
                    if text is None:
                        return None
                    text_bytes = text.encode('utf-8')
                    return base64.b64encode(text_bytes).decode('utf-8')
                auth_token = encode_base64(token_str)
                print(f"Base64 encoded auth_token to call api: {auth_token}")
                
        except Exception as e:
            logger.error(f"Failed to decode token: {e}")

    # Now rewrite the question using contextllm with auth_token available
    try:
        # Convert prev_msgs to list of dicts if needed
        prev_msgs_dict = [m.dict() if hasattr(m, 'dict') else dict(m) if not isinstance(m, dict) else m for m in prev_msgs]
        full_question = rewrite_question(prev_msgs_dict, query, auth_token)
        print(f"[contextllm] Rewritten full question: {full_question}")
        logger.info(f"[contextllm] Rewritten full question: {full_question}")
    except Exception as e:
        print(f"[contextllm] Failed to rewrite question, using fallback. Error: {e}")
        logger.error(f"[contextllm] Failed to rewrite question, using fallback. Error: {e}")
        # fallback to old logic
        last_msgs = prev_msgs[-5:]
        context = "\n".join([f"Previous message {i+1} ({msg['role'] if isinstance(msg, dict) else msg.role}): {msg['content'] if isinstance(msg, dict) else msg.content}" for i, msg in enumerate(last_msgs)])
        full_question = f"{context}\nCurrent question: {query}" if context else query
        print(f"Full question: {full_question}")
        logger.info(f"Full question: {full_question}")

    # Pass all relevant info to the orchestration handler, including auth_token
    result = await supervisor(full_question, database_name, auth_token)
    print(f"Printing final result: {result}")


    # Extract the main response text, always as a string
    response_text = None
    if isinstance(result, dict):
        if "answer" in result:
            response_text = result["answer"]
            while isinstance(response_text, dict) and "answer" in response_text:
                response_text = response_text["answer"]
        elif "error" in result:
            response_text = "Server is down, please try again in some time."
        else:
            response_text = str(result)
    else:
        response_text = str(result)

    if not isinstance(response_text, str):
        response_text = json.dumps(response_text, ensure_ascii=False)

    timestamp_bot = datetime.utcnow().isoformat()
    context_list = [
        {"role": "user", "content": query, "timestamp": timestamp_bot},
        {"role": "assistant", "content": response_text, "timestamp": timestamp_bot}
    ]
    user_details = {
        "session_id": getattr(body, "session_id", None) if hasattr(body, "session_id") else None,
        "token": getattr(body, "token", None) if hasattr(body, "token") else None
    }

    return {
        "answer": response_text,
        "timestamp": timestamp_bot,
        "context": context_list,
        "user_details": user_details,
        "decrypted_fields": decrypted_fields
    }