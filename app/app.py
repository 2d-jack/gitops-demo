from flask import Flask, jsonify
import os
import socket

app = Flask(__name__)
app.config["WTF_CSRF_ENABLED"] = False

APP_VERSION = os.getenv("APP_VERSION", "2.0.0")
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")


@app.route("/")
def home():
    return jsonify({
        "status": "ok",
        "message": "Hello from GitOps Demo App — v2 is LIVE!",
        "version": APP_VERSION,
        "environment": ENVIRONMENT,
        "hostname": socket.gethostname(),
    })


@app.route("/health")
def health():
    return jsonify({"status": "healthy"}), 200


@app.route("/version")
def version():
    return jsonify({"version": APP_VERSION}), 200


if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")  # safer default than 0.0.0.0
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"

    app.run(host=host, port=port, debug=debug)
