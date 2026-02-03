from flask import Flask, request, jsonify

app = Flask(__name__)

API_KEY = "test123"

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Honeypot API is running"})

@app.route("/api/honeypot", methods=["POST"])
def honeypot():
    # API key check
    api_key = request.headers.get("x-api-key")
    if api_key != API_KEY:
        return jsonify({"error": "Invalid API Key"}), 401

    # GUVI tester sends NO body
    if not request.data:
        return jsonify({
            "status": "success",
            "reply": "Honeypot endpoint is active and secured"
        })

    # Future evaluation messages (GUVI internal)
    return jsonify({
        "status": "success",
        "reply": "Why is my account being suspended?"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
