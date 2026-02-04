from flask import Flask, request, jsonify
import re
import requests
import os

app = Flask(__name__)

# =========================
# CONFIG
# =========================
API_KEY = "test123"
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
    # -------- API KEY CHECK --------
    api_key = request.headers.get("x-api-key")
    if api_key != API_KEY:
        return jsonify({"error": "Invalid API Key"}), 401

    # -------- GUVI TESTER (NO BODY) --------
    if not request.data:
        return jsonify({
            "status": "success",
            "reply": "Honeypot endpoint is active and secured"
        })

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 422

    session_id = data.get("sessionId")
    message = data.get("message", {})
    text = message.get("text", "")

    if not session_id or not text:
        return jsonify({"error": "Invalid request body"}), 422

    # -------- SESSION INIT --------
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

    # -------- STORE MESSAGE --------
    session["messages"].append(text)
    turn = len(session["messages"])

    # -------- SCAM DETECTION --------
    if not session["scamDetected"]:
        session["scamDetected"] = detect_scam(text)

    # -------- INTELLIGENCE EXTRACTION --------
    intel = extract_intelligence(text)
    for k in session["intelligence"]:
        session["intelligence"][k].extend(intel[k])

    # -------- FINAL GUVI CALLBACK --------
    if (
        session["scamDetected"]
        and turn >= 3
        and not session["callbackSent"]
    ):
        payload = {
            "sessionId": session_id,
            "scamDetected": True,
            "totalMessagesExchanged": turn,
            "extractedIntelligence": session["intelligence"],
            "agentNotes": "Scammer used urgency and account threat tactics"
        }

        try:
            requests.post(GUVI_CALLBACK_URL, json=payload, timeout=5)
            session["callbackSent"] = True
        except Exception as e:
            print("GUVI callback failed:", e)

    # -------- AGENT REPLY --------
    reply = generate_reply(session["scamDetected"], turn)

    return jsonify({
        "status": "success",
        "reply": reply
    })

# =========================
# RAILWAY ENTRYPOINT
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
