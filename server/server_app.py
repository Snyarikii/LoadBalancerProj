import os
from flask import Flask, jsonify

app = Flask(__name__)

# Fetch the unique container name/ID from environment variables
SERVER_ID = os.environ.get("SERVER_ID", "Unknown_Server")

# 1) Endpoint (/home, method=GET)
@app.route('/home', methods=['GET'])
def home():
    response = {
        "message": f"Hello from Server: {SERVER_ID}",
        "status": "successful"
    }
    return jsonify(response), 200

# 2) Endpoint (/heartbeat, method=GET)
@app.route('/heartbeat', methods=['GET'])
def heartbeat():
    # Empty response with a 200 status code for the health checker
    return "", 200

if __name__ == '__main__':
    # Listen inside the container network on port 5000 
    app.run(host='0.0.0.0', port=5000)
