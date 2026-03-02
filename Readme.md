# 🚋 Digital Twin – Predictive Maintenance Platform  
## RATP Dev Casablanca Tramway Network  

> This project is fully dedicated to **RATP Dev Casablanca** and was designed and implemented by **Chaymae El hamzaoui** as a digital twin and predictive maintenance demonstrator for urban tramways.

---

## 📋 Overview

This repository implements a **Digital Twin web platform** for the Casablanca tramway network operated by **RATP Dev**.  
The goal is to combine:

- A **geospatial digital twin** of the network (lines T1–T4,and busway 1 and 2 stations, moving trams).  
- An **industrial‑style predictive maintenance engine** (based on MetroPT / rail standards, not generative AI).  
- A **dashboard** for operators to monitor fleet health, alerts, and maintenance planning.

All predictive logic is **explicit and deterministic** (Isolation‑Forest‑like anomaly detection, XGBoost‑like rules, RUL estimation). Generative AI is only used optionally to explain results in natural language – never to make maintenance decisions.

---

## 🧩 Main Components

### 1. Dashboard Web App (`dashboard/app.py` + `dashboard/templates/index.html`)

Flask application serving the main web dashboard at `http://localhost:5000`.

**Key features:**

- **2D Digital Twin (Leaflet)**  
  - Dark basemap centered on Casablanca.  
  - Tramway network drawn from `dashboard/templates/tram_casablanca.geojson`.  
  - Automatic extraction of lines and stations from the GeoJSON.  
  - Animated “3D‑like” tram icons moving along the lines (T1–T4, BW1, BW2).

- **3D‑style View (MapLibre GL)**  
  - Toggle between 2D and a 3D perspective view.  
  - Lines rendered as elevated polylines.  
  - Trams represented as CSS‑based 2.5D markers with health‑dependent glow.

- **Predictive Maintenance Panel (right side)**  
  - Global fleet health score (OK / WARNING / CRITICAL counts).  
  - Queue of predictive alerts with risk level, component, probability and RUL (“J‑x”).  
  - Mini sparkline showing health evolution over 24 h.  
  - Actions to “plan” maintenance or focus the affected line on the map.

- **Integrated GeoJSON**  
  - `dashboard/app.py` loads `tram_casablanca.geojson` on the server side.  
  - The JSON is embedded into `index.html` (`<script id="embedded-tram-geojson">…`) so Leaflet can initialize the network without extra HTTP fetches.

### 2. Predictive Maintenance API (`src/api_backend.py` + `src/Predictive_maintenance.py`)

Separate Flask REST API (typically on `http://localhost:5001`) that encapsulates the **ML‑based predictive maintenance engine**.

**Domain model:**

- `SensorReading`: industrial sensor schema (pressures, temperatures, currents, GPS, environment) inspired by the **MetroPT** dataset.  
- `MaintenancePrediction`: unified output with:
  - anomaly score and `is_anomaly` flag,  
  - failure probability, predicted failure type,  
  - estimated RUL (hours),  
  - severity level (NORMAL / WARNING / CRITICAL),  
  - confidence and feature importances,  
  - human‑readable recommendation.

- `ComponentType` and `FailureType`:  
  - Components: Air Production Unit (APU), braking system, doors, traction, HVAC, pantograph, suspension, battery.  
  - Failures: air leaks, compressor failure, oil leak, motor overheating, etc.

**Pipeline (no generative AI for prediction):**

- **Anomaly detection**: Isolation‑Forest‑like score based on deviation from calibrated thresholds for pressure, temperature and current.  
- **Failure probability**: XGBoost‑style rule system tuned on MetroPT patterns (e.g. low TP2 + high differential pressure → air leak).  
- **Remaining Useful Life (RUL)**: degradation‑curve‑based estimation on pressure and temperature, capped at one week.  
- **Explainability**: simple SHAP‑like feature importance exposing which sensors drove each alert.  
- **Recommendations**: rule‑based textual guidance (remove from service, schedule preventive inspection, monitor specific sensors, etc.).

**Main endpoints (`api_backend.py`):**

- `GET /api/health` – API status.  
- `GET /api/fleet/summary` – fleet‑level health and prediction breakdown.  
- `GET /api/vehicle/<vehicle_id>/prediction` – prediction for one vehicle (e.g. `T1-001`).  
- `GET /api/vehicle/<vehicle_id>/sensors` – current simulated sensor readings.  
- `GET /api/alerts` – list of active maintenance alerts (critical + warning).  
- `GET /api/line/<line_id>/health` – health summary per line (T1–T4).  
- `POST /api/maintenance/schedule` – mock scheduling of a maintenance task.  
- `GET /api/statistics/daily` – synthetic daily stats for charts.  
- `GET /api/components/health` – synthetic health per component family.

The dashboard consumes these endpoints to power the right‑hand maintenance panel.

### 3. Operations & Historical Data (`dashboard/app.py` + `src/data/raw/*`)

In addition to the predictive engine, the dashboard integrates basic operational analytics:

- **MySQL‑backed endpoints** in `dashboard/app.py`:
  - `/api/status` – DB connectivity and global counts.  
  - `/api/realtime/trams` – recent operations per tram (load, delay, incident flag).  
  - `/api/analytics/global` – KPIs by line and by hour.  
  - `/api/maintenance/alerts` – rule‑based alerts from a `maintenance` table.  
  - `/api/predictions/delays` – simple delay prediction demo.  
  - `/api/stations/list` – stations per line (T1–T4).

- **Offline scripts** in `src/` (optional):
  - `Data_generation.py`, `fill_mysql.py`, `read_data.py`, `main.py` – generate synthetic data and populate the MySQL database for demo purposes (not required at runtime once DB is filled).

---

## 🛠️ Tech Stack

| Layer        | Technologies                                                                 |
|-------------|------------------------------------------------------------------------------|
| Backend     | Python 3, Flask, NumPy (ML logic implemented manually)                       |
| Frontend    | HTML5, vanilla JavaScript, Leaflet, MapLibre GL, Font Awesome               |
| Data        | GeoJSON (OpenStreetMap‑based), MySQL (tram operations & maintenance)        |
| Visuals     | Custom CSS, 2.5D tram markers, inline SVG sparklines                         |
| Domain base | MetroPT dataset structure, railway standards (EN 45545, EN 50121, etc.)     |

The predictive engine is written to be **transparent and explainable**, so that railway engineers can understand and debate the rules and thresholds.

---

## ▶️ How to Run the Platform

From the project root:

### 1. Start the Predictive Maintenance API

```bash
cd src
python api_backend.py
```

This starts the predictive API on `http://localhost:5001`.

### 2. Start the Digital Twin Dashboard

```bash
cd dashboard
python app.py
```

The dashboard will run on `http://localhost:5000`.

The main page (`/`) will:

- Render `index.html`.  
- Embed `tram_casablanca.geojson` in the HTML.  
- Initialize the 2D/3D maps and animated trams.  
- Call the predictive API periodically to keep fleet health and alerts up to date.

---

## 📁 Repository Structure (simplified)

```text
DigitalTwin_Tram_RATPDev/
├─ dashboard/
│  ├─ app.py                 # Flask app for dashboard UI + ops APIs
│  ├─ templates/
│  │  ├─ index.html          # Main digital twin dashboard (2D/3D + maintenance)
│  │  └─ tram_casablanca.geojson  # Casablanca tramway network
│  └─ static/
│     ├─ css/style.css       # Styles
│     └─ js/…                # (legacy / optional scripts)
│
├─ src/
│  ├─ api_backend.py         # Predictive maintenance REST API
│  ├─ Predictive_maintenance.py  # ML engine and fleet monitor
│  ├─ data/raw/*.csv         # Raw operational / maintenance data (optional)
│  └─ *.py                   # Data generation & DB helper scripts (offline)
│
└─ Readme.md                 # You are here
```

---

## 🎓 About the Project & Author

- **Client focus**: RATP Dev Casablanca – tramway network.  
- **Author**: **Chaymae Elhamzaoui**.  
- **Scope**: research and demonstrator project on digital twins and predictive maintenance for urban rail.  
- **Objectives**:
  - Build a coherent **digital twin** of the Casablanca tram network.  
  - Implement a **non‑generative, explainable predictive maintenance engine**.  
  - Provide a **clear, operator‑oriented dashboard** for maintenance and control room teams.

This work is a **pedagogical and experimental platform**, not a production system, but it is inspired by real‑world railway practices and RATP Dev constraints.

---

> *“Towards a reliable, explainable and operator‑centric predictive maintenance for urban mobility in Casablanca.”*  