import requests
import re
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

API_KEY = "test123"
if data is None:
    return {
        "status": "success",
        "reply": "Honeypot endpoint is active and secured"
    }


@app.get("/")
def root():
    return {"message": "Honeypot API is running"}

# --------------------
# In-memory session store
# --------------------
sessions = {}

# --------------------
# Scam detection
# --------------------
def detect_scam(text: str) -> bool:
    keywords = [
        "account blocked",
        "verify immediately",
        "urgent",
        "upi",
        "bank",
        "suspended",
        "click link",
        "verify now"
    ]
    text = text.lower()
    return any(k in text for k in keywords)

# --------------------
# Intelligence extraction
# --------------------
def extract_intelligence(text: str) -> dict:
    return {
        "upi_ids": re.findall(r"\b[a-zA-Z0-9.\-_]{2,}@[a-zA-Z]{2,}\b", text),
        "phone_numbers": re.findall(r"\b\d{10}\b", text),
        "urls": re.findall(r"https?://[^\s]+", text)
    }

# --------------------
# Human-like replies
# --------------------
def generate_human_reply(is_scam: bool, count: int) -> str:
    if not is_scam:
        return "Hello, what is this regarding?"

    if count == 1:
        return "Why will my account be blocked?"
    if count == 2:
        return "I already have an account, why verification again?"
    if count == 3:
        return "Can you share any official message or link?"

    return "I am not comfortable, please explain properly."

# --------------------
# Request Models
# --------------------
class Message(BaseModel):
    sender: str
    text: str
    timestamp: str

class Metadata(BaseModel):
    channel: Optional[str]
    language: Optional[str]
    locale: Optional[str]

class HoneyPotRequest(BaseModel):
    sessionId: str
    message: Message
    conversationHistory: List[Message] = []
    metadata: Optional[Metadata]

# --------------------
# MAIN API ENDPOINT
# --------------------
@app.post("/api/honeypot")
def honeypot(
    data: HoneyPotRequest | None = None,
    x_api_key: str = Header(None)
):


    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    session_id = data.sessionId

    # Create session
    if session_id not in sessions:
        sessions[session_id] = {
            "messages": [],
            "scamDetected": False,
            "intelligence": {
                "upi_ids": [],
                "phone_numbers": [],
                "urls": []
            },
            "callback_sent": False
        }

    # Store message
    sessions[session_id]["messages"].append(data.message.text)

    # Scam detection
    if not sessions[session_id]["scamDetected"]:
        sessions[session_id]["scamDetected"] = detect_scam(data.message.text)

    # Extract intelligence
    intel = extract_intelligence(data.message.text)
    sessions[session_id]["intelligence"]["upi_ids"].extend(intel["upi_ids"])
    sessions[session_id]["intelligence"]["phone_numbers"].extend(intel["phone_numbers"])
    sessions[session_id]["intelligence"]["urls"].extend(intel["urls"])

    message_count = len(sessions[session_id]["messages"])

    # --------------------
    # GUVI FINAL CALLBACK (MANDATORY)
    # --------------------
    if (
        sessions[session_id]["scamDetected"]
        and message_count >= 3
        and not sessions[session_id]["callback_sent"]
    ):
        payload = {
            "sessionId": session_id,
            "scamDetected": True,
            "totalMessagesExchanged": message_count,
            "extractedIntelligence": {
                "bankAccounts": [],
                "upiIds": sessions[session_id]["intelligence"]["upi_ids"],
                "phishingLinks": sessions[session_id]["intelligence"]["urls"],
                "phoneNumbers": sessions[session_id]["intelligence"]["phone_numbers"],
                "suspiciousKeywords": ["urgent", "verify", "blocked"]
            },
            "agentNotes": "Scammer used urgency and payment redirection"
        }

        try:
            requests.post(
                "https://hackathon.guvi.in/api/updateHoneyPotFinalResult",
                json=payload,
                timeout=5
            )
            sessions[session_id]["callback_sent"] = True
        except Exception as e:
            print("Callback failed:", e)

    # Generate reply
    reply_text = generate_human_reply(
        sessions[session_id]["scamDetected"],
        message_count
    )

    return {
        "status": "success",
        "reply": reply_text
    }
