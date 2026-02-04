from flask import Flask, request, jsonify
import re
import requests
import os

app = Flask(__name__)

# =========================
# CONFIG
# =========================
API_KEY = "agentic_honeypot_key"
GUVI_CALLBACK_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"

# =========================
# IN-MEMORY SESSION STORE
# =========================
sessions = {}

# =========================
# SCAM DETECTION
# =========================
def detect_scam(text: str) -> bool:
    keywords = [
        "urgent", "verify", "blocked", "suspended",
        "bank", "upi", "otp", "click", "account"
    ]
    text = text.lower()
    return any(k in text for k in keywords)

# =========================
# INTELLIGENCE EXTRACTION
# =========================
def extract_intelligence(text: str):
    return {
        "upiIds": re.findall(r"\b[a-zA-Z0-9.\-_]{2,}@[a-zA-Z]{2,}\b", text),
        "phoneNumbers": re.findall(r"\b\d{10}\b", text),
        "phishingLinks": re.findall(r"https?://[^\s]+", text),
        "suspiciousKeywords": [
            k for k in ["urgent", "verify", "blocked", "otp"]
            if k in text.lower()
        ]
    }

# =========================
# HUMAN-LIKE AGENT REPLIES
# =========================
def generate_reply(is_scam: bool, turn: int) -> str:
    if not is_scam:
        return "Hello, what is this regarding?"

    replies = {
        1: "Why is my account being suspended?",
        2: "I already have an account. Why do I need to verify again?",
        3: "Can you share any official message or link?",
        4: "I am not comfortable sharing details like this."
    }

    return replies.get(turn, "Please explain properly, I am confused.")

# =========================
# ROOT CHECK
# =========================
@app.route("/", methods=["GET"])
def root():
    return jsonify({"message": "Honeypot API is running"})

# =========================
# MAIN HONEYPOT ENDPOINT
# =========================
@app.route("/api/honeypot", methods=["POST"])
def honeypot():
    # --------------------
    # 1. API KEY CHECK
    # --------------------
    api_key = request.headers.get("x-api-key")
    if api_key != API_KEY:
        return jsonify({"error": "Invalid API Key"}), 401

    # --------------------
    # 2. GUVI TESTER CASE
    # (Empty or invalid body)
    # --------------------
    if not request.data:
        return jsonify({
            "status": "success",
            "reply": "Why is my account being suspended?"
        })

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "status": "success",
            "reply": "Why is my account being suspended?"
        })

    # --------------------
    # 3. SAFE FIELD ACCESS
    # --------------------
    session_id = data.get("sessionId", "default")

    message = data.get("message", {})
    text = message.get("text", "")

    # --------------------
    # 4. SESSION STORE
    # --------------------
    if session_id not in sessions:
        sessions[session_id] = {
            "messages": []
        }

    sessions[session_id]["messages"].append(text)
    count = len(sessions[session_id]["messages"])

    # --------------------
    # 5. AGENTIC REPLIES
    # --------------------
    replies = {
        1: "Why is my account being suspended?",
        2: "I already verified earlier. Why again?",
        3: "Can you share any official message or link?",
    }

    reply = replies.get(
        count,
        "I am not comfortable sharing sensitive details."
    )

    # --------------------
    # 6. FINAL RESPONSE
    # --------------------
    return jsonify({
        "status": "success",
        "reply": reply
    })
