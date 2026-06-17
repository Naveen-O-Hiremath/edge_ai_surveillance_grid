# Sentinel AI — Edge Surveillance Platform

## Ship with one command

**Windows (PowerShell):**
```powershell
.\run-all.ps1 -Detach
```

**Linux / macOS:**
```bash
chmod +x start.sh
./start.sh --detach
```

**Or plain Docker Compose** (after `cp .env.example .env`):
```bash
docker compose up --build -d --wait
```

Open **http://localhost:3000** — login `admin@sentinel.ai` / `admin123`

Only **port 3000** is exposed. API (`/api/v1`) and WebSockets (`/ws`) are proxied through nginx.

### Mobile camera (phone on same Wi‑Fi)

1. On Windows, run as Admin: `.\scripts\open-firewall.ps1`
2. Detect LAN IP: `.\scripts\get-lan-ip.ps1` (auto-run by `run-all.ps1`)
3. In **Configure**, use the mobile QR link — phone opens `http://<your-lan-ip>:3000/...`
4. Laptop webcam links use `localhost:3000` (browsers require secure context for camera on LAN HTTP)

### Useful commands

| Action | Command |
|--------|---------|
| Start (foreground) | `.\run-all.ps1` |
| Start (background) | `.\run-all.ps1 -Detach` |
| Stop | `docker compose down` |
| Logs | `docker compose logs -f` |
| Rebuild | `docker compose up --build -d --wait` |

### Project layout

```
backend/     FastAPI API, events, PostgreSQL
edge-ai/     YOLO detection, surveillance pipeline
frontend/    React dashboard (nginx in Docker)
infra/       MQTT broker config
scripts/     LAN IP + firewall helpers (Windows)
```

### Local development (without Docker)

See service READMEs in `backend/`, `edge-ai/`, `frontend/` — run PostgreSQL, Redis, and MQTT locally, then start each service with `uvicorn` / `npm run dev`.
