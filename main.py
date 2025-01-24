from flask import (
    Flask,
    jsonify,
    request,
)
import os
from datetime import datetime, timezone
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
import requests

load_dotenv(override=True)

WEBHOOK = os.environ["WEBHOOK_URI"]

app = Flask(__name__)
CORS(app)
limiter = Limiter(
    get_remote_address,
    app=app,
)

def send_webhook(url, email, subject, message):
    data = {
        "embeds": [
            {
                "title": subject,
                "description": message,
                "author": {
                    "name": email,
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ]
    }
    requests.post(url, json=data)

@app.route("/contact", methods=["POST"])
@limiter.limit("20/day")
@limiter.limit("10/hour")
@limiter.limit("3/minute")
def contact():
    email = request.values.get("email")
    subject = request.values.get("subject")
    message = request.values.get("message")

    if not email or not message or not subject:
        return jsonify({"error": "Email, Subject and message are required"}), 400

    try:
        send_webhook(
            WEBHOOK,
            email,
            subject,
            message,
        )

    except Exception as e:
        print(f"Error sending webhook: {e}")
        return jsonify({"error": "Error sending message"}), 500

    return jsonify({"message": "Message sent successfully"}), 200


@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({"error": f"{e}"}), 429

@app.route("/health", methods=["GET"])
@limiter.exempt
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
