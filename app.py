from flask import Flask, render_template, jsonify, request
import json, os, subprocess, glob, threading, time, urllib.request
from pathlib import Path

app = Flask(__name__)
PRESETS_FILE    = os.path.join(os.path.dirname(__file__), 'presets.json')
GPS_CONFIG_FILE = Path(__file__).resolve().parent / 'gps_config.json'

# ── GPS ───────────────────────────────────────────────────────────────────────
import gps as _gps

def _gps_load_config() -> dict:
    if GPS_CONFIG_FILE.exists():
        try:
            return json.loads(GPS_CONFIG_FILE.read_text())
        except Exception:
            pass
    return {'source': 'opstoc', 'port': '/dev/ttyS3', 'om_url': 'http://localhost:8082'}

def _gps_save_config(cfg: dict):
    GPS_CONFIG_FILE.write_text(json.dumps(cfg, indent=2))

def _gps_apply(cfg: dict):
    src = cfg.get('source', 'opstoc')
    if src == 'direct':
        _gps.gps_start(cfg.get('port', '/dev/ttyS3'))
    elif src == 'om':
        _gps._start_proxy(cfg.get('om_url', 'http://localhost:8082'))
    else:
        _gps.gps_stop()

# init on startup
_cfg = _gps_load_config()
_gps_apply(_cfg)

@app.route('/api/gps')
def api_gps_get():
    cfg = _gps_load_config()
    src = cfg.get('source', 'opstoc')
    if src == 'opstoc':
        try:
            with urllib.request.urlopen('http://localhost:8090/api/gps', timeout=2) as r:
                d = json.loads(r.read())
            return jsonify({**d, 'source': 'opstoc'})
        except Exception:
            return jsonify({'fix': False, 'lat': None, 'lon': None, 'sats': 0,
                            'source': 'opstoc', 'error': 'OPS-TOC unavailable'})
    with _gps.gps_lock:
        pos = dict(_gps.gps_state)
        rt  = dict(_gps._gps_runtime)
    return jsonify({**pos, **rt, 'source': src})

@app.route('/api/gps/config', methods=['GET'])
def api_gps_config_get():
    return jsonify(_gps_load_config())

@app.route('/api/gps/config', methods=['POST'])
def api_gps_config_set():
    data = request.get_json(silent=True) or {}
    cfg  = _gps_load_config()
    cfg['source'] = data.get('source', cfg.get('source', 'opstoc'))
    if 'port'   in data: cfg['port']   = data['port']
    if 'om_url' in data: cfg['om_url'] = data['om_url']
    _gps_save_config(cfg)
    _gps_apply(cfg)
    return jsonify({'ok': True, 'source': cfg['source']})

@app.route('/api/gps/ports')
def api_gps_ports():
    return jsonify({'ports': _gps.list_ports()})

# ── Presets ───────────────────────────────────────────────────────────────────
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

STATION_CFG = os.path.expanduser('~/radiosonde_auto_rx/auto_rx/station.cfg')

def _update_frequency_list(freq):
    with open(STATION_CFG) as f:
        lines = f.readlines()
    lines = [l for l in lines if not (l.strip().startswith('frequency_list') and not l.strip().startswith('#'))]
    if freq is not None:
        for i, line in enumerate(lines):
            if line.strip().startswith('max_freq'):
                lines.insert(i + 1, f'frequency_list = [{float(freq):.3f}]\n')
                break
    with open(STATION_CFG, 'w') as f:
        f.writelines(lines)

@app.route('/api/preset/tune', methods=['POST'])
def preset_tune():
    data = request.get_json(silent=True) or {}
    freq = data.get('freq')
    try:
        _update_frequency_list(freq)
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500
    r = subprocess.run(['systemctl', '--user', 'is-active', 'autorx'], capture_output=True, text=True)
    restarted = r.stdout.strip() == 'active'
    if restarted:
        def do_restart():
            subprocess.run(['systemctl', '--user', 'restart', 'autorx'], capture_output=True)
        threading.Thread(target=do_restart, daemon=True).start()
    return jsonify({'ok': True, 'freq': freq, 'restarted': restarted})

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
        time.sleep(1)
        subprocess.run(['systemctl', '--user', 'restart', 'sonde.service'], capture_output=True)
    threading.Thread(target=restart, daemon=True).start()
    return jsonify({'ok': True, 'msg': msg})

@app.route('/api/version')
def get_version():
    result = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'],
                            cwd=os.path.dirname(os.path.abspath(__file__)),
                            capture_output=True, text=True)
    return jsonify({'version': result.stdout.strip() or 'unknown'})

@app.route('/api/restart', methods=['POST'])
def restart_app():
    def do_restart():
        time.sleep(1)
        subprocess.run(['systemctl', '--user', 'restart', 'sonde.service'], capture_output=True)
    threading.Thread(target=do_restart, daemon=True).start()
    return jsonify({'ok': True})

@app.route('/api/kill', methods=['POST'])
def kill_app():
    def do_stop():
        time.sleep(1)
        subprocess.run(['systemctl', '--user', 'stop', 'sonde.service'], capture_output=True)
    threading.Thread(target=do_stop, daemon=True).start()
    return jsonify({'ok': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5100, debug=False)
