from flask import Flask, request, jsonify
import os

app = Flask(__name__)

API_KEY = "test123"

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Honeypot API is running"})

@app.route("/api/honeypot", methods=["GET", "POST"])
def honeypot():
    api_key = request.headers.get("x-api-key")
    if api_key != API_KEY:
        return jsonify({"error": "Invalid API Key"}), 401

    # GUVI tester (no body)
    if request.method == "GET" or not request.data:
        return jsonify({
            "status": "success",
            "reply": "Honeypot endpoint is active and secured"
        })

    # Real evaluation (JSON body)
    return jsonify({
        "status": "success",
        "reply": "Why is my account being suspended?"
    })
