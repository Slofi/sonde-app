from flask import Flask, render_template, jsonify, request
import json, os, subprocess, glob, threading
from pathlib import Path

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

@app.route('/api/scan/start', methods=['POST'])
def scan_start():
    subprocess.run(['systemctl', '--user', 'start', 'autorx'], capture_output=True)
    return jsonify({'ok': True})

@app.route('/api/scan/stop', methods=['POST'])
def scan_stop():
    subprocess.run(['systemctl', '--user', 'stop', 'autorx'], capture_output=True)
    return jsonify({'ok': True})

@app.route('/api/rtl/release', methods=['POST'])
def rtl_release():
    for name in ['auto_rx', 'rtl_tcp', 'rtl_fm', 'rtl_power', 'rtl_test', 'rtl_adsb']:
        subprocess.run(['pkill', '-f', name], capture_output=True)
    subprocess.run(['sudo', 'systemctl', 'stop', 'dump1090-mutability'], capture_output=True)
    for dev in glob.glob('/dev/bus/usb/*/*'):
        try:
            r = subprocess.run(['sudo', 'fuser', dev], capture_output=True, text=True)
            for pid in r.stdout.strip().split():
                subprocess.run(['sudo', 'kill', pid], capture_output=True)
        except Exception:
            pass
    return jsonify({'ok': True})

@app.route('/api/upgrade', methods=['POST'])
def upgrade():
    app_dir = os.path.dirname(os.path.abspath(__file__))
    result = subprocess.run(['git', 'pull'], cwd=app_dir, capture_output=True, text=True)
    if result.returncode != 0:
        return jsonify({'ok': False, 'msg': result.stderr.strip() or 'git pull failed'})
    msg = result.stdout.strip()
    def restart():
        import time; time.sleep(1)
        subprocess.run(['systemctl', '--user', 'restart', 'sonde.service'], capture_output=True)
    threading.Thread(target=restart, daemon=True).start()
    return jsonify({'ok': True, 'msg': msg})

@app.route('/api/version')
def get_version():
    import subprocess as sp
    result = sp.run(['git', 'rev-parse', '--short', 'HEAD'],
                    cwd=os.path.dirname(os.path.abspath(__file__)),
                    capture_output=True, text=True)
    return jsonify({'version': result.stdout.strip() or 'unknown'})

@app.route('/api/restart', methods=['POST'])
def restart_app():
    def do_restart():
        import time; time.sleep(1)
        subprocess.run(['systemctl', '--user', 'restart', 'sonde.service'], capture_output=True)
    threading.Thread(target=do_restart, daemon=True).start()
    return jsonify({'ok': True})

@app.route('/api/kill', methods=['POST'])
def kill_app():
    def do_stop():
        import time; time.sleep(1)
        subprocess.run(['systemctl', '--user', 'stop', 'sonde.service'], capture_output=True)
    threading.Thread(target=do_stop, daemon=True).start()
    return jsonify({'ok': True})


# ── GPS ───────────────────────────────────────────────────────────────────────

import gps as _gps

_gps.init(Path(__file__).resolve().parent)


@app.route('/api/gps')
def api_gps_get():
    with _gps.gps_lock:
        pos = dict(_gps.gps_state)
        rt  = dict(_gps._gps_runtime)
    cfg = _gps.load_config()
    return jsonify({**cfg, **pos, **rt})


@app.route('/api/gps', methods=['POST'])
def api_gps_set():
    data     = request.get_json(silent=True) or {}
    enabled  = bool(data.get('enabled', False))
    port     = str(data.get('port', '')).strip()
    om_proxy = bool(data.get('om_proxy', False))
    om_url   = str(data.get('om_url', 'http://localhost:8082')).strip()
    cfg = _gps.load_config()
    cfg['enabled']  = enabled
    cfg['port']     = port
    cfg['om_proxy'] = om_proxy
    cfg['om_url']   = om_url
    _gps.save_config(cfg)
    if enabled:
        if om_proxy and om_url:
            _gps._start_proxy(om_url, fallback_port=port)
        elif port:
            _gps.gps_start(port)
        else:
            _gps.gps_stop()
    else:
        _gps.gps_stop()
    return jsonify({'ok': True})


@app.route('/api/gps/ports')
def api_gps_ports():
    return jsonify({'ports': _gps.list_ports()})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5100, debug=False)
