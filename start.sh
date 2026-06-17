#!/usr/bin/env bash
# One command to ship Sentinel AI with Docker.
# Usage: ./start.sh [--detach] [--no-build] [--open-firewall]
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

DETACH=false
NO_BUILD=false

for arg in "$@"; do
  case "$arg" in
    --detach|-d) DETACH=true ;;
    --no-build) NO_BUILD=true ;;
    -h|--help)
      echo "Usage: ./start.sh [--detach] [--no-build]"
      exit 0
      ;;
  esac
done

log() { echo "[sentinel] $*"; }

if [[ ! -f .env && -f .env.example ]]; then
  cp .env.example .env
  log "Created .env from .env.example"
fi

mkdir -p data

# Best-effort LAN IP for mobile camera QR (written to data/host-lan.json)
detect_lan() {
  local ip=""
  if command -v ip >/dev/null 2>&1; then
    ip=$(ip -4 route get 1.1.1.1 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i=="src") print $(i+1)}' | head -1)
  elif command -v hostname >/dev/null 2>&1; then
    ip=$(hostname -I 2>/dev/null | awk '{print $1}')
  fi
  if [[ -n "$ip" && "$ip" != 127.* ]]; then
    local url="http://${ip}:3000"
    export PUBLIC_BASE_URL="$url"
    cat > data/host-lan.json <<EOF
{"lan_ip":"$ip","port":3000,"url":"$url","updated_at":"$(date -u +%Y-%m-%dT%H:%M:%SZ)"}
EOF
    log "PUBLIC_BASE_URL=$url"
  fi
}

detect_lan

compose=(compose up)
[[ "$NO_BUILD" == false ]] && compose+=(--build)
[[ "$DETACH" == true ]] && compose+=(-d --wait)

log "docker ${compose[*]}"
docker "${compose[@]}"

if [[ "$DETACH" == true ]]; then
  echo ""
  echo "Sentinel AI is running."
  echo "  Dashboard: http://localhost:3000"
  echo "  Login:     admin@sentinel.ai / admin123"
  [[ -n "${PUBLIC_BASE_URL:-}" ]] && echo "  Mobile QR: ${PUBLIC_BASE_URL}/publish/..."
  echo ""
fi
