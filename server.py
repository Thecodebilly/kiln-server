from flask import Flask, request, jsonify, render_template_string
from datetime import datetime
import sqlite3

app = Flask(__name__)
DB_FILE = "temperature.db"

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT,
            temperature INTEGER,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# HTML template for dashboard
dashboard_html = """
<html>
<head>
    <title>ESP32 Temperature Dashboard</title>
    <meta http-equiv="refresh" content="10">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: Arial; background: #f2f2f2; text-align: center; }
        h1 { color: #333; }
        canvas { max-width: 900px; margin: auto; display: block; }
    </style>
</head>
<body>
    <h1>ESP32 Temperature Dashboard</h1>
    <canvas id="tempChart"></canvas>
    <script>
        const ctx = document.getElementById('tempChart').getContext('2d');
        const labels = {{ timestamps|safe }};
        const datasets = [];

        {% for device, data in devices.items() %}
            datasets.push({
                label: '{{ device }}',
                data: {{ data.temps|safe }},
                borderColor: '{{ data.color }}',
                fill: false,
                tension: 0.1
            });
        {% endfor %}

        new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: datasets
            },
            options: {
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    </script>
</body>
</html>
"""

colors = ["red", "blue", "green", "orange", "purple", "brown", "cyan", "magenta"]

# Endpoint to receive ESP32 data
@app.route('/update', methods=['POST'])
def update_data():
    content = request.json
    device_id = content.get("device_id", "default")
    temp = content.get("temperature")
    if temp is None:
        return jsonify({"status": "error", "message": "No temperature provided"}), 400

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO readings (device_id, temperature, timestamp) VALUES (?, ?, ?)",
              (device_id, temp, timestamp))
    conn.commit()
    conn.close()

    return jsonify({"status": "ok"})

# JSON API endpoint
@app.route('/get', methods=['GET'])
def get_data():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT device_id, temperature, timestamp FROM readings ORDER BY id ASC")
    rows = c.fetchall()
    conn.close()

    data = {}
    for device_id, temp, timestamp in rows:
        if device_id not in data:
            data[device_id] = []
        data[device_id].append({"temperature": temp, "timestamp": timestamp})
    return jsonify(data)

# Dashboard endpoint
@app.route('/dashboard', methods=['GET'])
def dashboard():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT device_id, temperature, timestamp FROM readings ORDER BY id ASC")
    rows = c.fetchall()
    conn.close()

    devices = {}
    all_timestamps = sorted(list({ts for _, _, ts in rows}))
    for device_id, temp, ts in rows:
        if device_id not in devices:
            devices[device_id] = {"temps": [], "color": colors[len(devices) % len(colors)]}
        devices[device_id]["temps"].append(temp)

    return render_template_string(dashboard_html, devices=devices, timestamps=all_timestamps)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
