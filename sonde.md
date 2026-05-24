type:: project
status:: active
tags:: #sonde #radiosonde #sdr #cyberdeck
updated:: 2026-05-24

# Sonde Tracker

> Custom radiosonde tracking frontend for the Cyberdeck. Dark/gold aesthetic, Leaflet map, frequency presets for Central/wider Europe. Frontend to radiosonde_auto_rx decoder.

## State

| **Status**  | Active — app running, auto_rx not yet installed |
| **Port**    | 5100 |
| **Host**    | Cyberdeck (rock-5b, 100.97.104.107) |
| **Service** | sonde.service (user systemd, enabled) |
| **Backend** | radiosonde_auto_rx (port 5000) — not yet installed |

## Access

| Resource | Value |
|----------|-------|
| App URL  | http://localhost:5100 (on CD) |
| App path | ~/sonde/ |
| Service  | systemctl --user start/stop/restart sonde.service |
| auto_rx  | https://github.com/projecthorus/radiosonde_auto_rx |

## Quick Commands

**Start/stop:**
```bash
systemctl --user start sonde.service
systemctl --user stop sonde.service
systemctl --user restart sonde.service
```

**Logs:**
```bash
journalctl --user -u sonde.service -f
```

## Key Paths

| Item | Path |
|------|------|
| App | ~/sonde/app.py |
| Template | ~/sonde/templates/index.html |
| Presets | ~/sonde/presets.json |
| Venv | ~/sonde/venv/ |
| Service | ~/.config/systemd/user/sonde.service |

## Pending

- Install radiosonde_auto_rx (see GitHub wiki for ARM64/Debian install)
- Verify/correct European frequency presets against live data (sondehub.org)
- Test socket.io connection to auto_rx once installed
- Consider landing zone prediction integration (future)

## Changelog

**2026-05-24** — Initial build. Flask app on port 5100, Leaflet map (OSM/Topo/MT Topo/Sat), editable frequency presets, socket.io connection to auto_rx, telemetry bar. Launcher tile added. (Session 308)

---
---
# ////// FULL REFERENCE //////

## Architecture

```
auto_rx (port 5000)          Our app (port 5100)
  RTL-SDR scanning     →     Flask serves HTML
  Sonde decoding       →     Frontend JS connects
  socket.io server     →     to auto_rx socket.io
  event: telemetry_data      displays on Leaflet map
```

**Key design decision:** Our app is purely a frontend. auto_rx handles all RTL-SDR interaction and decoding. We connect to its socket.io websocket to receive live telemetry.

## Frequency Presets (built-in)

| Station | Country | Freq (MHz) | Type | Verified |
|---------|---------|-----------|------|----------|
| Ljubljana | SI | 403.00 | M20 | ✓ |
| Zagreb | HR | 402.00 | RS41 | ✓ |
| Wien | AT | 403.50 | RS41 | ✓ |
| Wien Alt | AT | 405.00 | RS41 | — |
| Udine | IT | 403.00 | M20 | — |
| Budapest | HU | 402.00 | RS41 | — |
| Praha | CZ | 402.50 | RS41 | — |
| Beograd | RS | 402.00 | RS41 | — |
| München | DE | 403.00 | RS41 | — |
| Payerne | CH | 402.00 | RS41 | — |
| Milano | IT | 403.00 | RS41 | — |

Unverified freqs should be cross-checked on [sondehub.org](https://sondehub.org) once auto_rx is running.

## Map Layers

| Button | Source |
|--------|--------|
| OSM | OpenStreetMap tile server |
| Topo | OpenTopoMap |
| MT Topo | OpenStreetMap base + Waymarked Trails hiking overlay |
| Sat | ESRI World Imagery |

## auto_rx socket.io

- **URL:** `http://localhost:5000`
- **Event:** `telemetry_data`
- **Key fields:** callsign, freq, type, lat, lon, alt, vel_v (climb m/s), vel_h (speed m/s), temp, humidity, snr

## auto_rx Install (pending)

Follow: https://github.com/projecthorus/radiosonde_auto_rx/wiki
- Requires Python 3, rtl-sdr tools, various decoders
- Install to /opt/radiosonde_auto_rx/
- Configure station.cfg (location, scan range 400.0–406.0 MHz)
- Run as service on port 5000
