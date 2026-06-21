# AI-Assisted Cloud Resource Optimization Framework

This project is a dissertation-ready prototype for monitoring real server resource usage, estimating cost, detecting inefficiencies with AI/ML, and recommending optimization actions.

## Features

- Admin login and dashboard
- Live CPU, memory, disk and network metric tracking from the host machine
- Historical metric storage
- Cost estimation and prediction
- Isolation Forest anomaly and inefficiency detection
- Rule-based optimization recommendations
- Reports and graphs
- Prometheus metrics endpoint with live application and server gauges
- Docker-based deployment
- GitHub Actions test automation

## Tech Stack

- Python 3.11
- FastAPI
- SQLAlchemy
- PostgreSQL in Docker, SQLite locally by default
- Jinja2, HTML, CSS, Bootstrap
- Pandas, NumPy, Scikit-learn
- Prometheus and Grafana
- Pytest
- Psutil

## Quick Start

Create a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Start the app:

```powershell
uvicorn app.main:app --reload
```

The application automatically creates a live monitored resource named `local-host-server` and collects a real metric record on startup. It continues collecting live server metrics every 60 seconds while the app is running.

To manually collect a live metric record:

```powershell
curl -X POST http://127.0.0.1:8000/api/collect-live
```

To run AI analysis:

```powershell
curl -X POST http://127.0.0.1:8000/api/analyse
```

Open:

- App: http://127.0.0.1:8000
- Dashboard: http://127.0.0.1:8000/dashboard
- API docs: http://127.0.0.1:8000/docs
- Prometheus metrics: http://127.0.0.1:8000/metrics

Demo login:

- Username: `admin`
- Password: `admin123`

Optional demo data is still available if you need simulated multi-resource workloads for screenshots or comparison:

```powershell
python -m scripts.seed_demo_data
```

## Real Data Mode

The default mode now uses real host/server metrics through `psutil`:

- CPU usage from the running machine
- RAM usage from the running machine
- Disk usage from the running machine
- Network traffic received and sent during the collection interval
- Response-time sample from the application process

This means the system can be deployed on an AWS EC2 instance, Azure VM, Render/Railway service or local server and collect real metrics from that environment.

For a cloud deployment, run the app on the VM/server you want to monitor. The dashboard will then show that server's actual resource usage.

## Docker

```powershell
docker compose up --build
```

Services:

- App: http://127.0.0.1:8000
- Prometheus: http://127.0.0.1:9090
- Grafana: http://127.0.0.1:3000

Grafana default login is usually `admin` / `admin`.

## Evaluation Plan

Compare system behavior before and after recommendations:

- CPU utilization improvement
- Memory utilization improvement
- Estimated cost reduction
- Response time
- System availability
- Prediction accuracy
- Recommendation usefulness
- Dashboard usability

## Suggested Dissertation Structure

1. Introduction
2. Literature Review
3. Methodology: Design Science Research Methodology
4. System Analysis and Design
5. Implementation
6. Testing and Evaluation
7. Conclusion and Future Work
