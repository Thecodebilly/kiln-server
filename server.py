from flask import Flask, request, jsonify, render_template_string
from datetime import datetime
import sqlite3

app = Flask(__name__)
DB_FILE = "temperature.db"
HIGH_TEMP_THRESHOLD = 5000
colors = ["#e6194b", "#3cb44b", "#ffe119", "#4363d8", "#f58231", "#911eb4", "#46f0f0", "#f032e6"]

# Initialize SQLite DB
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

dashboard_html = """
<html>
<head>
    <title>ESP32 Temperature Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-zoom@2.1.1/dist/chartjs-plugin-zoom.min.js"></script>
    <style>
        body { font-family: 'Arial', sans-serif; text-align: center; background: #f9f9f9; color: #333; }
        h1 { font-size: 2.5em; color: #444; margin-bottom: 10px; }
        canvas { max-width: 900px; margin: 20px auto; display: block; background: #fff; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); padding: 10px; }
        table { margin: 20px auto; border-collapse: collapse; width: 70%; font-size: 1.2em; }
        th, td { padding: 12px 15px; border: 1px solid #ccc; text-align: center; }
        th { background: #4CAF50; color: white; font-size: 1.2em; }
        tr:nth-child(even) { background: #f2f2f2; }
        .high { background: #ff4c4c !important; color: white; font-weight: bold; }
        .device-name { font-weight: bold; color: #333; }
        .footer { margin-top: 40px; font-size: 0.9em; color: #666; }
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
            <td class="device-name">{{ device }}</td>
            <td>{{ data.latest }}</td>
            <td>{{ data.min }}</td>
            <td>{{ data.max }}</td>
        </tr>
        {% endfor %}
    </table>

    <div class="footer">Updated automatically from ESP32 devices.</div>

    <script>
        Chart.register(ChartZoom); // Register zoom plugin

        const ctx = document.getElementById('tempChart').getContext('2d');
        const labels = {{ timestamps|safe }};
        const datasets = [];

        {% for device, data in devices.items() %}
        datasets.push({
            label: '{{ device }}',
            data: {{ data.history|safe }},
            borderColor: '{{ data.color }}',
            backgroundColor: '{{ data.color }}55',
            fill: false,
            tension: 0.2,
            pointRadius: 4,
            pointHoverRadius: 6
        });
        {% endfor %}

        const tempChart = new Chart(ctx, {
            type: 'line',
            data: { labels: labels, datasets: datasets },
            options: {
                responsive: true,
                plugins: {
                    legend: { position: 'top', labels: { font: { size: 16 } } },
                    tooltip: { mode: 'index', intersect: false, titleFont: { size: 14 }, bodyFont: { size: 14 } },
                    zoom: {
                        pan: { enabled: true, mode: 'x', modifierKey: 'ctrl' }, // Pan along X-axis with Ctrl
                        zoom: { wheel: { enabled: true }, pinch: { enabled: true }, mode: 'x' } // Zoom along X-axis
                    }
                },
                scales: {
                    x: { title: { display: true, text: 'Time', font: { size: 16 } } },
                    y: { beginAtZero: true, title: { display: true, text: 'Temperature', font: { size: 16 } } }
                }
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

# Dashboard
@app.route('/dashboard')
def dashboard():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT device_id, temperature, timestamp FROM readings ORDER BY timestamp ASC")
    rows = c.fetchall()
    conn.close()

    devices = {}
    all_timestamps = []

    # Collect unique timestamps
    for device_id, temp, ts in rows:
        if ts not in all_timestamps:
            all_timestamps.append(ts)

    # Prepare device histories
    for device_id, temp, ts in rows:
        if device_id not in devices:
            devices[device_id] = {
                "history": [None] * len(all_timestamps),
                "latest": temp,
                "min": temp,
                "max": temp,
                "color": colors[len(devices) % len(colors)]
            }
        # Fill in temperature at correct index
        index = all_timestamps.index(ts)
        devices[device_id]["history"][index] = temp
        devices[device_id]["latest"] = temp
        devices[device_id]["min"] = min(devices[device_id]["min"], temp)
        devices[device_id]["max"] = max(devices[device_id]["max"], temp)

    return render_template_string(
        dashboard_html,
        devices=devices,
        timestamps=all_timestamps,
        threshold=HIGH_TEMP_THRESHOLD
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
