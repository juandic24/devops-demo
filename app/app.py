from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route("/")
def home():
    return jsonify({"message": "DevOps Demo App", "version": "1.0"})

@app.route("/health")
def health():
    return jsonify({"status": "healthy", "env": os.getenv("ENV", "local")})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
