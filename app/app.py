from flask import Flask, jsonify
import os
import socket

app = Flask(__name__)

APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")


@app.route("/")
def home():
    return jsonify({
        "status": "ok",
        "message": "Hello from GitOps Demo App!",
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
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
