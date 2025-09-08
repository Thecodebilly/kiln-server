from flask import Flask, request, jsonify, render_template, send_file
from datetime import datetime
import sqlite3
import csv
import os

app = Flask(__name__)
DB_FILE = "temperature.db"
CSV_FILE = "temperature.csv"
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

# Initialize CSV file with header if it doesn't exist
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "device_id", "temperature"])

# Receive ESP32 data
@app.route('/update', methods=['POST'])
def update_data():
    data = request.json
    device_id = data.get("device_id", "default")
    temp = data.get("temperature")
    if temp is None:
        return jsonify({"status": "error", "message": "No temperature provided"}), 400
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Write to SQLite
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO readings (device_id, temperature, timestamp) VALUES (?, ?, ?)",
              (device_id, temp, timestamp))
    conn.commit()
    conn.close()

    # Append to CSV
    with open(CSV_FILE, mode='a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, device_id, temp])

    return jsonify({"status": "ok"})

# Dashboard
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
            devices[device_id] = {
                "history": [],
                "latest": temp,
                "min": temp,
                "max": temp,
                "color": colors[len(devices) % len(colors)]
            }
        devices[device_id]["history"].append(temp)
        devices[device_id]["latest"] = temp
        devices[device_id]["min"] = min(devices[device_id]["min"], temp)
        devices[device_id]["max"] = max(devices[device_id]["max"], temp)

    timestamps = sorted(list(timestamps_set))
    return render_template('dashboard.html', devices=devices, timestamps=timestamps, threshold=HIGH_TEMP_THRESHOLD)

# CSV download endpoint
@app.route('/download_csv')
def download_csv():
    return send_file(CSV_FILE, mimetype='text/csv', as_attachment=True, download_name='temperature.csv')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
