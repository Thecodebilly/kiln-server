from flask import Flask, request, jsonify

app = Flask(__name__)
latest_data = {}

@app.route('/update', methods=['POST'])
def update_data():
    global latest_data
    data = request.json
    latest_data = data
    print("Received:", data)
    return jsonify({"status": "ok"})

@app.route('/get', methods=['GET'])
def get_data():
    return jsonify(latest_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
