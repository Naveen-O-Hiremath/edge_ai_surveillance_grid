# Sentinel AI — Edge Surveillance & Situational Awareness Platform

Enterprise-grade intelligent surveillance that transforms CCTV streams into structured situational intelligence. The system understands environments, learns normal states, detects anomalies, recognizes people, correlates threats, and delivers actionable alerts — operating primarily on edge devices.

## Architecture

```
Camera Stream → Edge AI (Detection/Tracking) → Event Engine → Threat Engine → Storage → Alerts → Dashboard
                     ↓                              ↓
              Deterministic Algorithms        Event Correlation
              (motion, door, state diff)      (theft chains, intrusion)
```

### Core Principle

**Use AI only where intelligence is required. Use deterministic algorithms everywhere else.**

| AI-Powered | Algorithm-Based |
|---|---|
| Person recognition | Door open/close detection |
| Object recognition | Motion detection |
| Scene understanding | State comparison (asset moved/removed) |
| Anomaly detection | Rule evaluation |
| Event summarization | Alert routing |

## Project Structure

```
smart_surveillance_eai/
├── backend/          # FastAPI — REST API, threat engine, event pipeline, PostgreSQL
├── edge-ai/          # Edge processing — YOLO detection, motion, face recognition, surveillance
├── frontend/         # React + Tailwind — Admin command center dashboard
├── mobile/           # Flutter — Push alerts and real-time notifications
├── infra/            # MQTT broker config
└── docker-compose.yml
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- (Optional) NVIDIA GPU for edge AI acceleration

### Run the Full Stack

```bash
docker compose up --build
```

| Service | URL |
|---|---|
| Admin Dashboard | http://localhost:3000 |
| API Docs | http://localhost:8000/docs |
| Edge AI | http://localhost:8001/docs |

**Default login:** `admin@sentinel.ai` / `admin123`

### Local Development (without Docker)

**Backend:**
```bash
cd backend
pip install -r requirements.txt
# Start PostgreSQL and Redis locally, then:
uvicorn app.main:app --reload --port 8000
```

**Edge AI:**
```bash
cd edge-ai
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Platform Workflow

### Demo Cameras (No CCTV Required)

Use **Laptop Webcam** or **Mobile Camera** instead of RTSP for demonstrations:

1. **Configure** → select camera source (Webcam or Mobile)
2. Add camera → open the **publisher link** (or scan QR for mobile)
3. Allow camera permission → tap **Start Camera**
4. Return to Configure → **Start Environment Learning**

**Mobile tip:** Your phone must reach your PC on the same Wi‑Fi. Set your LAN URL before starting Docker:

```bash
# Windows PowerShell — replace with your PC's IP
$env:PUBLIC_BASE_URL="http://192.168.1.5:3000"
docker compose up -d --build
```

### Phase 1 — Environment Learning

1. Add a room and camera in **Configure**
2. Click **Start Environment Learning**
3. AI scans the scene and inventories all visible objects (monitor, laptop, headphones, etc.)
4. Low-confidence detections prompt: *"What is this object?"*
5. Admin labels unknown items — system learns permanently

### Phase 2 — Person Registration

1. Go to **Persons** → **Register Person**
2. Capture 5 angles: front, left, right, up, down
3. System generates face embeddings (InsightFace in production)
4. Only embeddings stored — no raw image matching

### Phase 3 — Continuous Surveillance

1. Click **Activate Surveillance** in Configure
2. System monitors:
   - Person enter/exit, unknown/masked individuals
   - Asset removed, moved, or returned
   - Door open/close, monitor on/off
   - Motion in unoccupied areas
3. Events flow through threat engine with severity + risk scoring
4. Correlated incidents auto-generated (e.g., unknown person + asset removed = potential theft)

### Alert Configuration

Configure threat rules in **Alert Rules**:
- Event type (masked person, unknown visitor, asset removed, etc.)
- Minimum severity threshold
- Channels: push, desktop, email, SMS, WhatsApp, audible alarm

### AI Summary

Generate daily security briefings in **AI Summary**:
> *"Between 9 AM and 6 PM, 18 personnel entries were recorded. One unknown individual entered at 2:15 PM..."*

### Natural Language Search

Query logs in plain English:
- *"What happened yesterday after 10 PM?"*
- *"Show all unknown visitors last week"*
- *"Show every laptop movement"*

## API Overview

| Endpoint | Description |
|---|---|
| `POST /api/v1/cameras/configure/learning` | Phase 1 environment scan |
| `POST /api/v1/cameras/configure/surveillance` | Start monitoring |
| `POST /api/v1/persons/register` | Multi-angle face enrollment |
| `POST /api/v1/events/ingest` | Edge AI event ingestion |
| `GET /api/v1/analytics/dashboard` | Dashboard infographics |
| `POST /api/v1/analytics/summary` | AI daily summary |
| `POST /api/v1/search` | Natural language query |
| `WS /ws/live` | Real-time events and alerts |

## Edge AI Hardware

Target devices:
- NVIDIA Jetson Orin / Xavier
- Intel NUC
- Google Coral TPU

Uncomment the GPU section in `docker-compose.yml` for NVIDIA acceleration.

## Production AI Models

The edge service auto-detects and loads:
- **YOLOv8** — object detection (falls back to demo mode)
- **InsightFace** — face embeddings (configure in production)
- **OpenCV** — motion, door state, brightness (monitor on/off)
- **Haar Cascades** — face region detection

Install full AI stack:
```bash
pip install ultralytics insightface onnxruntime-gpu
```

## Mobile App

```bash
cd mobile
flutter pub get
flutter run
```

Connects via WebSocket to receive real-time push alerts with sound and vibration for critical threats.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React, TypeScript, Tailwind CSS, Framer Motion, Recharts |
| Backend | FastAPI, PostgreSQL, Redis, SQLAlchemy |
| Edge AI | YOLO, OpenCV, custom pipelines |
| Messaging | MQTT, WebSockets |
| Mobile | Flutter |
| Deployment | Docker, Kubernetes-ready |

## License

Proprietary — Sentinel AI Platform
