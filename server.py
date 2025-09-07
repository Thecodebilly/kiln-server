from flask import Flask, request, jsonify, render_template_string
from datetime import datetime
import sqlite3

app = Flask(__name__)
DB_FILE = "temperature.db"
HIGH_TEMP_THRESHOLD = 1000  # Change as needed
colors = ["red", "blue", "green", "orange", "purple", "brown", "cyan", "magenta"]

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

# Dashboard template
dashboard_html = """
<html>
<head>
    <title>ESP32 Temperature Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: Arial; text-align: center; background: #f2f2f2; }
        h1 { color: #333; }
        canvas { max-width: 900px; margin: auto; display: block; }
        table { margin: auto; border-collapse: collapse; width: 60%; margin-top: 20px; }
        th, td { padding: 10px; border: 1px solid #999; }
        th { background: #555; color: white; }
        td { background: white; text-align: center; }
        .high { background: #ff4c4c; color: white; font-weight: bold; }
    </style>
</head>
<body>
    <h1>ESP32 Temperature Dashboard</h1>
    <canvas id="tempChart"></canvas>

    <h2>Device Values</h2>
    <table>
        <tr><th>Device</th><th>Latest</th><th>Min</th><th>Max</th></tr>
        {% for device, data in devices.items() %}
        <tr class="{{ 'high' if data.latest > threshold else '' }}">
            <td>{{ device }}</td>
            <td>{{ data.latest }}</td>
            <td>{{ data.min }}</td>
            <td>{{ data.max }}</td>
        </tr>
        {% endfor %}
    </table>

    <script>
        const ctx = document.getElementById('tempChart').getContext('2d');
        const labels = {{ timestamps|safe }};
        const datasets = [];

        {% for device, data in devices.items() %}
        datasets.push({
            label: '{{ device }}',
            data: {{ data.history|safe }},
            borderColor: '{{ data.color }}',
            fill: false,
            tension: 0.1
        });
        {% endfor %}

        const tempChart = new Chart(ctx, {
            type: 'line',
            data: { labels: labels, datasets: datasets },
            options: {
                responsive: true,
                scales: { y: { beginAtZero: true } }
            }
        });
    </script>
</body>
</html>
"""

# Endpoint to receive ESP32 data
@app.route('/update', methods=['POST'])
def update_data():
    data = request.json
    device_id = data.get("device_id", "default")
    temp = data.get("temperature")
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
    for device_id, temp, ts in rows:
        if device_id not in data:
            data[device_id] = {"history": [], "latest": temp, "min": temp, "max": temp}
        data[device_id]["history"].append({"temperature": temp, "timestamp": ts})
        data[device_id]["latest"] = temp
        data[device_id]["min"] = min(data[device_id]["min"], temp)
        data[device_id]["max"] = max(data[device_id]["max"], temp)
    return jsonify(data)

# Dashboard endpoint
@app.route('/dashboard')
def dashboard():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT device_id, temperature, timestamp FROM readings ORDER BY id ASC")
    rows = c.fetchall()
    conn.close()

    devices = {}
    timestamps_set = set()
    for device_id, temp, ts in rows:
        timestamps_set.add(ts)
        if device_id not in devices:
            devices[device_id] = {"history": [], "latest": temp, "min": temp, "max": temp, "color": colors[len(devices) % len(colors)]}
        devices[device_id]["history"].append(temp)
        devices[device_id]["latest"] = temp
        devices[device_id]["min"] = min(devices[device_id]["min"], temp)
        devices[device_id]["max"] = max(devices[device_id]["max"], temp)

    timestamps = sorted(list(timestamps_set))
    return render_template_string(dashboard_html, devices=devices, timestamps=timestamps, threshold=HIGH_TEMP_THRESHOLD)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
