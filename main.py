from flask import Flask, request, jsonify
import re
import requests
import os

app = Flask(__name__)

# ==============================
# CONFIG
# ==============================
API_KEY = "test123"
GUVI_CALLBACK_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"

# ==============================
# IN-MEMORY SESSION STORE
# ==============================
sessions = {}

# ==============================
# SCAM DETECTION
# ==============================
def detect_scam(text: str) -> bool:
    keywords = [
        "account blocked",
        "verify",
        "urgent",
        "upi",
        "bank",
        "suspended",
        "click",
        "link",
        "payment"
    ]
    text = text.lower()
    return any(k in text for k in keywords)

# ==============================
# INTELLIGENCE EXTRACTION
# ==============================
def extract_intelligence(text: str):
    return {
        "upiIds": re.findall(r"\b[a-zA-Z0-9.\-_]{2,}@[a-zA-Z]{2,}\b", text),
        "phoneNumbers": re.findall(r"\b\d{10}\b", text),
        "phishingLinks": re.findall(r"https?://[^\s]+", text),
        "suspiciousKeywords": [k for k in ["urgent", "verify", "blocked"] if k in text.lower()]
    }

# ==============================
# HUMAN-LIKE AGENT REPLY
# ==============================
def agent_reply(message_count: int):
    replies = [
        "Why will my account be blocked?",
        "I already have a bank account, why verification again?",
        "Can you share any official message or link?",
        "I am not comfortable sharing details. Please explain."
    ]
    if message_count <= len(replies):
        return replies[message_count - 1]
    return replies[-1]

# ==============================
# ROOT
# ==============================
@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Honeypot API is running"})

# ==============================
# MAIN HONEYPOT ENDPOINT
# ==============================
@app.route("/api/honeypot", methods=["GET", "POST"])
def honeypot():

    # --------------------------
    # AUTH CHECK
    # --------------------------
    api_key = request.headers.get("x-api-key")
    if api_key != API_KEY:
        return jsonify({"error": "Invalid API Key"}), 401

    # --------------------------
    # GUVI TESTER (NO BODY / GET)
    # --------------------------
    if request.method == "GET" or not request.data:
        return jsonify({
            "status": "success",
            "reply": "Honeypot endpoint is active and secured"
        })

    # --------------------------
    # PARSE REQUEST
    # --------------------------
    data = request.get_json(silent=True)
    if not data or "sessionId" not in data or "message" not in data:
        return jsonify({
            "status": "success",
            "reply": "Hello, what is this regarding?"
        })

    session_id = data["sessionId"]
    message_text = data["message"]["text"]

    # --------------------------
    # INIT SESSION
    # --------------------------
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

    # --------------------------
    # STORE MESSAGE
    # --------------------------
    sessions[session_id]["messages"].append(message_text)

    # --------------------------
    # DETECT SCAM
    # --------------------------
    if not sessions[session_id]["scamDetected"]:
        sessions[session_id]["scamDetected"] = detect_scam(message_text)

    # --------------------------
    # EXTRACT INTEL
    # --------------------------
    intel = extract_intelligence(message_text)
    for key in intel:
        sessions[session_id]["intelligence"][key].extend(intel[key])

    message_count = len(sessions[session_id]["messages"])

    # --------------------------
    # FINAL GUVI CALLBACK
    # --------------------------
    if (
        sessions[session_id]["scamDetected"]
        and message_count >= 3
        and not sessions[session_id]["callbackSent"]
    ):
        payload = {
            "sessionId": session_id,
            "scamDetected": True,
            "totalMessagesExchanged": message_count,
            "extractedIntelligence": sessions[session_id]["intelligence"],
            "agentNotes": "Scammer used urgency and payment redirection tactics"
        }

        try:
            requests.post(GUVI_CALLBACK_URL, json=payload, timeout=5)
            sessions[session_id]["callbackSent"] = True
        except Exception as e:
            print("GUVI callback failed:", e)

    # --------------------------
    # AGENT RESPONSE
    # --------------------------
    return jsonify({
        "status": "success",
        "reply": agent_reply(message_count)
    })

# ==============================
# START
# ==============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
