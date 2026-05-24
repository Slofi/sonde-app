from flask import Flask, render_template, jsonify, request
import json, os

app = Flask(__name__)
PRESETS_FILE = os.path.join(os.path.dirname(__file__), 'presets.json')

DEFAULT_PRESETS = [
    {"id": "lju",  "name": "Ljubljana", "country": "SI", "freq": 403.00, "type": "M20",  "verified": True},
    {"id": "zag",  "name": "Zagreb",    "country": "HR", "freq": 402.00, "type": "RS41", "verified": True},
    {"id": "wie1", "name": "Wien",      "country": "AT", "freq": 403.50, "type": "RS41", "verified": True},
    {"id": "wie2", "name": "Wien Alt",  "country": "AT", "freq": 405.00, "type": "RS41", "verified": False},
    {"id": "udi",  "name": "Udine",     "country": "IT", "freq": 403.00, "type": "M20",  "verified": False},
    {"id": "bud",  "name": "Budapest",  "country": "HU", "freq": 402.00, "type": "RS41", "verified": False},
    {"id": "pra",  "name": "Praha",     "country": "CZ", "freq": 402.50, "type": "RS41", "verified": False},
    {"id": "beg",  "name": "Beograd",   "country": "RS", "freq": 402.00, "type": "RS41", "verified": False},
    {"id": "muc",  "name": "München",   "country": "DE", "freq": 403.00, "type": "RS41", "verified": False},
    {"id": "pay",  "name": "Payerne",   "country": "CH", "freq": 402.00, "type": "RS41", "verified": False},
    {"id": "mil",  "name": "Milano",    "country": "IT", "freq": 403.00, "type": "RS41", "verified": False},
]

if not os.path.exists(PRESETS_FILE):
    with open(PRESETS_FILE, 'w') as f:
        json.dump(DEFAULT_PRESETS, f, indent=2)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/presets', methods=['GET'])
def get_presets():
    try:
        with open(PRESETS_FILE) as f:
            return jsonify(json.load(f))
    except Exception:
        return jsonify(DEFAULT_PRESETS)

@app.route('/api/presets', methods=['POST'])
def save_presets():
    data = request.get_json()
    with open(PRESETS_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    return jsonify({'ok': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5100, debug=False)
