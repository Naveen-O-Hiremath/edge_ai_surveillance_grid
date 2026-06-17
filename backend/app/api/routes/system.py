import json

import logging

import socket

from pathlib import Path



from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import httpx

from app.api.deps import require_admin
from app.config import get_settings
from app.database import get_db
from app.models.entities import Camera, Incident, SurveillanceSession, User
from app.services.camera_health import is_camera_streaming, sync_camera_from_frames



logger = logging.getLogger(__name__)

router = APIRouter(prefix="/system", tags=["System"])

settings = get_settings()



HOST_LAN_FILE = Path("/app/data/host-network/host-lan.json")





def _is_docker_ip(ip: str) -> bool:

    if ip.startswith("172."):

        second = int(ip.split(".")[1]) if len(ip.split(".")) > 1 else 0

        return 16 <= second <= 31

    return False





def _is_apipa(ip: str) -> bool:

    return ip.startswith("169.254.")





def _load_host_lan() -> dict | None:

    try:

        if HOST_LAN_FILE.is_file():

            return json.loads(HOST_LAN_FILE.read_text(encoding="utf-8"))

    except (OSError, json.JSONDecodeError) as e:

        logger.debug("Could not read host LAN file: %s", e)

    return None





@router.get("/network-hints")

async def network_hints(request: Request):

    """Return candidate frontend URLs for mobile QR (prefers host-detected Wi-Fi IP)."""

    host_header = request.headers.get("x-forwarded-host") or request.headers.get("host") or "localhost:3000"

    hostname = host_header.split(":")[0]

    port = host_header.split(":")[1] if ":" in host_header else "3000"

    scheme = "https" if request.headers.get("x-forwarded-proto") == "https" else "http"



    candidates: list[str] = []

    warning: str | None = None

    recommended: str | None = None

    host_lan = _load_host_lan()



    if settings.public_base_url:

        candidates.append(settings.public_base_url.rstrip("/"))

        recommended = settings.public_base_url.rstrip("/")



    if host_lan:

        if host_lan.get("warning"):

            warning = host_lan["warning"]

        lan_ip = host_lan.get("lan_ip")

        if lan_ip:

            url = f"http://{lan_ip}:{port}"

            if url not in candidates:

                candidates.insert(0, url)

            recommended = url

        for item in host_lan.get("candidates") or []:

            url = item.get("url") or (f"http://{item['ip']}:{port}" if item.get("ip") else None)

            if url and url not in candidates:

                candidates.append(url)



    if hostname not in ("localhost", "127.0.0.1"):

        client_url = f"{scheme}://{host_header}"

        if client_url not in candidates:

            candidates.append(client_url)



    try:

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        s.connect(("8.8.8.8", 80))

        ip = s.getsockname()[0]

        s.close()

        if not _is_docker_ip(ip) and ip not in ("127.0.0.1", "0.0.0.0") and not _is_apipa(ip):

            url = f"http://{ip}:{port}"

            if url not in candidates:

                candidates.append(url)

    except OSError:

        pass



    candidates.append(f"http://localhost:{port}")



    filtered = [

        u for u in candidates

        if "172." not in u and "169.254." not in u

    ]



    lan_first = sorted(

        filtered,

        key=lambda u: (

            0 if "192.168." in u else 1,

            0 if u.startswith("http://10.") else 2,

            3 if "localhost" in u or "127.0.0.1" in u else 1,

        ),

    )



    if not recommended:

        recommended = next((u for u in lan_first if "192.168." in u or u.startswith("http://10.")), None)



    if not recommended and lan_first:

        recommended = lan_first[0]



    if not warning and not any("192.168." in u or u.startswith("http://10.") for u in lan_first):

        warning = (

            "No Wi-Fi/Ethernet IP detected. Connect your PC to Wi-Fi, run scripts\\get-lan-ip.ps1, "

            "or set PUBLIC_BASE_URL in docker-compose."

        )



    return {

        "port": int(port) if str(port).isdigit() else 3000,

        "hostname": hostname,

        "recommended_base_url": recommended or f"http://localhost:{port}",

        "candidates": lan_first,

        "warning": warning,

        "note": "Use your PC Wi-Fi IP (not Hyper-V vEthernet). Phone must be on the same Wi-Fi network.",

    }


@router.get("/status")
async def system_status(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Honest aggregate health — only counts cameras that are actually streaming frames."""
    cameras = (await db.execute(select(Camera))).scalars().all()
    for cam in cameras:
        sync_camera_from_frames(cam)
    await db.flush()

    streaming = sum(1 for c in cameras if is_camera_streaming(c))
    active_sessions = (
        await db.execute(select(SurveillanceSession).where(SurveillanceSession.is_active.is_(True)))
    ).scalars().all()
    open_incidents = (
        await db.execute(select(Incident).where(Incident.status == "open"))
    ).scalars().all()

    edge_ok = False
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(f"{settings.edge_ai_url}/health")
            edge_ok = r.status_code == 200
    except httpx.HTTPError:
        edge_ok = False

    cameras_configured = len(cameras)
    healthy = edge_ok and (cameras_configured == 0 or streaming > 0)

    return {
        "healthy": healthy,
        "edge_ai_reachable": edge_ok,
        "cameras_total": cameras_configured,
        "cameras_streaming": streaming,
        "surveillance_sessions": len(active_sessions),
        "open_incidents": len(open_incidents),
        "message": (
            "All systems ready"
            if healthy
            else "Start a camera publisher and keep the tab open — no live feeds detected"
            if cameras_configured and streaming == 0
            else "Edge AI unreachable — rebuild or restart the edge-ai container"
            if not edge_ok
            else "Degraded"
        ),
    }


