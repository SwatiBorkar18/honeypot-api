import re
import requests
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

API_KEY = "test123"

# -------------------------
# In-memory session memory
# -------------------------
sessions = {}

# -------------------------
# Models
# -------------------------
class Message(BaseModel):
    sender: str
    text: str
    timestamp: int

class Metadata(BaseModel):
    channel: Optional[str] = None
    language: Optional[str] = None
    locale: Optional[str] = None

class HoneyPotRequest(BaseModel):
    sessionId: str
    message: Message
    conversationHistory: List[Message] = []
    metadata: Optional[Metadata] = None

# -------------------------
# Scam detection
# -------------------------
SCAM_KEYWORDS = [
    "account blocked",
    "verify",
    "urgent",
    "upi",
    "bank",
    "otp",
    "click link",
    "suspended"
]

def detect_scam(text: str) -> bool:
    text = text.lower()
    return any(k in text for k in SCAM_KEYWORDS)

# -------------------------
# Intelligence extraction
# -------------------------
def extract_intelligence(text: str):
    return {
        "upiIds": re.findall(r"[a-zA-Z0-9.\-_]{2,}@[a-zA-Z]{2,}", text),
        "phoneNumbers": re.findall(r"\b\d{10}\b", text),
        "phishingLinks": re.findall(r"https?://\S+", text),
        "suspiciousKeywords": [k for k in SCAM_KEYWORDS if k in text.lower()]
    }

# -------------------------
# Agent reply logic
# -------------------------
def agent_reply(stage: int) -> str:
    replies = {
        1: "Why will my account be blocked?",
        2: "I already verified earlier, why again?",
        3: "Can you share any official link or message?",
        4: "I am not comfortable sharing details like this."
    }
    return replies.get(stage, "Please explain properly.")

# -------------------------
# Root
# -------------------------
@app.get("/")
def home():
    return {"message": "Honeypot API is running"}

# -------------------------
# Main Honeypot Endpoint
# -------------------------
@app.post("/api/honeypot")
def honeypot(
    data: Optional[HoneyPotRequest] = None,
    x_api_key: str = Header(None)
):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    # GUVI tester (empty body)
    if data is None:
        return {
            "status": "success",
            "reply": "Honeypot endpoint is active and secured"
        }

    session_id = data.sessionId

    if session_id not in sessions:
        sessions[session_id] = {
            "messages": [],
            "scamDetected": False,
            "intelligence": {
                "upiIds": [],
                "phoneNumbers": [],
                "phishingLinks": [],
                "suspiciousKeywords": []
            },
            "callbackSent": False
        }

    session = sessions[session_id]
    session["messages"].append(data.message.text)

    # Detect scam
    if not session["scamDetected"]:
        session["scamDetected"] = detect_scam(data.message.text)

    # Extract intelligence
    intel = extract_intelligence(data.message.text)
    for key in intel:
        session["intelligence"][key].extend(intel[key])

    stage = len(session["messages"])
    reply = agent_reply(stage)

    # -------------------------
    # FINAL CALLBACK (after enough engagement)
    # -------------------------
    if session["scamDetected"] and stage >= 3 and not session["callbackSent"]:
        payload = {
            "sessionId": session_id,
            "scamDetected": True,
            "totalMessagesExchanged": stage,
            "extractedIntelligence": session["intelligence"],
            "agentNotes": "Scammer used urgency and account threat tactics"
        }

        try:
            requests.post(
                "https://hackathon.guvi.in/api/updateHoneyPotFinalResult",
                json=payload,
                timeout=5
            )
            session["callbackSent"] = True
        except:
            pass

    return {
        "status": "success",
        "reply": reply,
        "scamDetected": session["scamDetected"],
        "extractedIntelligence": session["intelligence"]
    }
