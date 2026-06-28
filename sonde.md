type:: project
status:: active
tags:: #sonde #radiosonde #sdr #cyberdeck
updated:: 2026-06-23

# Sonde Tracker

> Custom radiosonde tracking frontend for the Cyberdeck. Dark/gold aesthetic, Leaflet map, frequency presets for Central/wider Europe. Frontend to radiosonde_auto_rx decoder.

## State

| **Status**       | Active — app running, auto_rx running as autorx.service |
| **Port**         | 5100 |
| **Host**         | Cyberdeck (rock-5b, 100.97.104.107) |
| **Service**      | sonde.service (user systemd, enabled) |
| **auto_rx**      | Installed at ~/radiosonde_auto_rx/, runs as autorx.service |
| **auto_rx svc**  | autorx.service (user systemd, NOT enabled — started via Scan button in app) |
| **MapTiler key** | Not yet entered — enter via key icon in header |

## Access

| Resource | Value |
|----------|-------|
| App URL  | http://localhost:5100 (on CD) |
| App path | ~/Projects/sonde/ |
| Repo     | github.com/Slofi/sonde-app |
| Service  | systemctl --user start/stop/restart sonde.service |

## Quick Commands

**Start/stop Sonde App:**
```bash
systemctl --user start sonde.service
systemctl --user stop sonde.service
systemctl --user restart sonde.service
```

**Logs:**
```bash
journalctl --user -u sonde.service -f
```

**Start/stop auto_rx manually (normally done via Scan button):**
```bash
systemctl --user start autorx
systemctl --user stop autorx
journalctl --user -u autorx -f
```

## Key Paths

| Item | Path |
|------|------|
| App | ~/Projects/sonde/app.py |
| Template | ~/Projects/sonde/templates/index.html |
| Presets | ~/Projects/sonde/presets.json |
| Venv | ~/Projects/sonde/venv/ |
| GPS config | ~/Projects/sonde/gps_config.json |
| Sonde service | ~/.config/systemd/user/sonde.service |
| auto_rx service | ~/.config/systemd/user/autorx.service |
| auto_rx install | ~/radiosonde_auto_rx/ |
| auto_rx config | ~/radiosonde_auto_rx/auto_rx/station.cfg |

## Pending

- Enter MapTiler API key in app (key icon in header)
- Verify/correct European frequency presets against live data (Radiosonde Tracker app, sondehub.org)
- **Reception debugging on CD** — at 14:00 CEST 2026-06-08 launch, sonde MEC500925 was at 22 km altitude climbing NNW, but tight scan around 404.6 MHz showed flat noise even at max gain. Antenna orientation/length/position is the suspected culprit. Test next time: vertical, λ/4 ≈ 18 cm, away from walls
- Verify Ljubljana frequency over multiple launches — was 404.6 MHz (M20) on 2026-06-08; sondes typically re-use frequencies but it's not guaranteed
- The `verified: true` flag in presets is misleading right now — needs a real verification workflow

## Ideas (deferred)

- **Export drawings + sonde tracks to Map App** — on-demand transfer via shared GeoJSON files in `~/maps/overlays/`. Sonde App exports drawings (lines/areas/circles) and sonde track polylines to GeoJSON; Map App loads and displays them as toggleable overlay layers. Deferred until Map App UI/UX pass is done first.
- **Add Voyager + Esri Topo to layer list** — both Sonde App and Map App. Carto Voyager is free/no key, Esri Topo is free. See map notes below.

## Map Layer Notes (Filip's review, 2026-05-24)

Preferences for the layer picker across all apps:

| Layer | Verdict | Notes |
|-------|---------|-------|
| MT Topo | ★ Favourite | Topo lines, clean, not cluttered, good colours — current winner |
| Voyager (Carto) | ★ Good | Clean, modern — replaced by MT Topo but still worth keeping |
| Esri Topo | ★ Good | Topo lines, terrain visible — slightly too bright |
| TF Landscape | Good | Topo lines, colours need getting used to |
| Stadia Outdoors | Good colours, no topo | Warm palette but terrain is flat — misleading name |
| MT Streets | OK | Same palette as MT Topo but no topo lines |
| MT Winter | Interesting | Cool/unusual colour take — niche use |
| Esri Dark Gray | Night use | Good for low-light / night shift use |
| Esri Streets | OK | Warm colours, nothing special |
| TF Pioneer | Nice colours | That's all — no topo |
| TF Atlas | Nice | No topo lines |
| Positron | Too bright | — |
| Stamen Terrain | Too white | Hills are nice but too much whitespace |
| TF Outdoors | Cluttered | Trails and markers everywhere, too bad |
| Toner Lite/Dark | Not useful | Interesting but not practical |
| Esri Hillshade | Unclear value | — |
| OpenTopoMap | Remove | Buildings too bold, too much contrast, hard on eyes — remove from OM |

## Changelog

**2026-06-23** — GPS position/chase features: own position marker (blue dot) on map, Distance + Bearing telem bar fields, dashed chase line to selected sonde, GPS status dot in header. GPS source selector in burger panel (OPS-TOC / OM / Direct). Backend `gps.py` module with watchdog, UBX init, OM proxy + fallback. Config at `gps_config.json`. Shutdown/restart styled splash screens. Commits `bc5a31b` pushed to `github.com/Slofi/sonde-app`. (Session 348)
**2026-06-08** — Preset-based frequency tuning. Clicking a preset writes `only_scan = [freq]` to auto_rx's station.cfg and restarts autorx so it listens on that exact frequency. Deselect → empty `only_scan`, full scan mode resumes. Visible left-edge stripe on preset items: gold = user-selected, green = sonde detected on that frequency. Toast feedback. Backend endpoint `POST /api/preset/tune`. Initial slip used wrong config key `frequency_list` (silently ignored by auto_rx) — corrected to `only_scan`. Ljubljana preset corrected: 403.000 → 404.600 MHz (M20, verified via Radiosonde Tracker for 2026-06-08 launch MEC500925). station.cfg: `max_freq` 403.0 → 406.0, `gain` -1 → 49.6. Launcher tile renamed Radiosonde → Sonde, repointed from :5000 to :5100, starts both autorx + sonde services. Commit `ab7d1a6` on github.com/Slofi/sonde-app. (Session 329)
**2026-05-24** — Draw manager: shape list (show/hide, edit, delete per shape), labels toggle, shape edit mode with draggable handles, bold draw colours. Cursor fix during drawing. Commits 865fd7c, d6a3d8e, 025a597. (Session 309)
**2026-05-24** — Shared tile path confirmed: Map App downloads MBTiles into `~/maps/mbtiles/`, `mbtileserver` serves on port 8092, Sonde App Local tile picker reads it. (Session 308)
**2026-05-24** — Local tile layer added: fetches tilesets from mbtileserver (port 8092), shows picker. (Session 308)
**2026-05-24** — autorx.service created (user systemd, started via Scan button). In-app upgrade button added (git pull + service restart). GPX track export added. Duplicate add-preset button removed. App renamed to Sonde App. All pushed to GitHub. (Session 308)
**2026-05-24** — socket.io fixed: namespace /update_status, event telemetry_event, field id not callsign, freq as formatted string. CORS fixed in auto_rx web.py. MT Topo layer changed to MapTiler (API key required). Scan + Release RTL buttons added. (Session 308)
**2026-05-24** — Initial build. Flask app on port 5100, Leaflet map, editable presets, telemetry bar. Launcher tile added. auto_rx installed, built, configured (lat/lon/alt), udev rules fixed, RTL-SDR Blog V4 confirmed working. (Session 308)

---
---
# ////// FULL REFERENCE //////

## Architecture

```
auto_rx (port 5000)            Sonde App (port 5100)
  RTL-SDR scanning       →     Flask serves HTML/JS
  Sonde decoding         →     JS connects to auto_rx socket.io
  socket.io server             displays sondes on Leaflet map
  namespace: /update_status    draws live track, exports GPX
  event: telemetry_event
```

**Key design decision:** Sonde App is a pure frontend. auto_rx handles all RTL-SDR interaction and decoding. We only connect to its socket.io to display data.

**auto_rx is NOT always running** — it's started on demand via the Scan button in the app header. This avoids blocking the RTL-SDR dongle when not tracking sondes.

## Map Layers

| Button | Source | Notes |
|--------|--------|-------|
| OSM | OpenStreetMap | Always available |
| Topo | OpenTopoMap | Always available |
| MT Topo | MapTiler Topo | Requires API key (enter via key icon) |
| Sat | ESRI World Imagery | Always available |
| Local | mbtileserver :8092 | Shows picker of downloaded tilesets from Map App |

## auto_rx socket.io Details

| Field | Value |
|-------|-------|
| URL | http://localhost:5000 |
| Namespace | /update_status |
| Event | telemetry_event |
| Callsign field | `id` (not `callsign`) |
| Frequency field | `freq` — formatted string, e.g. "403.000 MHz" |
| Other fields | lat, lon, alt, vel_v (climb m/s), vel_h (speed m/s), temp, humidity, snr, type |

## auto_rx Setup (complete)

- Installed: `~/radiosonde_auto_rx/`
- Decoders compiled via `build.sh`
- Python venv at `~/radiosonde_auto_rx/auto_rx/venv/`
- Station config: lat=46.0410, lon=14.4999, alt=260 (Ljubljana area)
- Scan range: 400.0–406.0 MHz
- udev rules: `/etc/udev/rules.d/60-librtlsdr2.rules`
- RTL-SDR Blog V4 confirmed working (`rtl_test` passes)
- CORS patched in auto_rx `web.py`: `cors_allowed_origins='*'`

## Frequency Presets (built-in)

| Station | Country | Freq (MHz) | Type | Verified |
|---------|---------|------------|------|----------|
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

Unverified freqs should be cross-checked on [sondehub.org](https://sondehub.org) when auto_rx is running. Presets are editable in the app and saved to `~/Projects/sonde/presets.json`.
