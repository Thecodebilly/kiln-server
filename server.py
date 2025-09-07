from flask import Flask, request, jsonify, render_template_string
from datetime import datetime

app = Flask(__name__)

# Stores data per device
device_data = {}

# HTML template for dashboard
dashboard_html = """
<html>
<head>
    <title>ESP32 Temperature Dashboard</title>
    <meta http-equiv="refresh" content="5">
    <style>
        body { font-family: Arial; background: #f2f2f2; text-align: center; }
        h1 { color: #333; }
        table { margin: auto; border-collapse: collapse; width: 50%; }
        th, td { padding: 10px; border: 1px solid #999; }
        th { background: #555; color: white; }
        td { background: white; }
    </style>
</head>
<body>
    <h1>ESP32 Temperature Dashboard</h1>
    <table>
        <tr>
            <th>Device</th>
            <th>Latest Temp</th>
            <th>Min Temp</th>
            <th>Max Temp</th>
            <th>Last Update</th>
        </tr>
        {% for device, data in devices.items() %}
        <tr>
            <td>{{ device }}</td>
            <td>{{ data.latest }}</td>
            <td>{{ data.min }}</td>
            <td>{{ data.max }}</td>
            <td>{{ data.time }}</td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""

@app.route('/update', methods=['POST'])
def update_data():
    content = request.json
    device_id = content.get("device_id", "default")
    temp = content.get("temperature")

    if temp is None:
        return jsonify({"status": "error", "message": "No temperature provided"}), 400

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if device_id not in device_data:
        device_data[device_id] = {"latest": temp, "min": temp, "max": temp, "time": now}
    else:
        device_data[device_id]["latest"] = temp
        device_data[device_id]["min"] = min(temp, device_data[device_id]["min"])
        device_data[device_id]["max"] = max(temp, device_data[device_id]["max"])
        device_data[device_id]["time"] = now

    return jsonify({"status": "ok"})

@app.route('/get', methods=['GET'])
def get_data():
    # JSON for IoT apps
    return jsonify(device_data)

@app.route('/dashboard', methods=['GET'])
def dashboard():
    # Human-friendly HTML dashboard
    return render_template_string(dashboard_html, devices=device_data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
