from flask import Flask, request, jsonify

app = Flask(__name__)
latest_data = {}

@app.route('/update', methods=['POST'])
def update_data():
    global latest_data
    latest_data = request.json
    return jsonify({"status": "ok"})

@app.route('/get', methods=['GET'])
def get_data():
    temp = latest_data.get("temperature", "N/A")
    html = f"""
    <html>
        <head><title>ESP32 Temperature</title></head>
        <body>
            <h1>ESP32 Temperature</h1>
            <p>Current Temperature: <strong>{temp}</strong></p>
        </body>
    </html>
    """
    return html

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
