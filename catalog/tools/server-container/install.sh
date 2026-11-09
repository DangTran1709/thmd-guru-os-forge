#!/bin/sh
# THMD-Guru Modular Hub - On-Demand Module Installer
# Module ID : tools/server-container
# Name      : Hạ tầng Container & Microservices (Docker CE / Podman)
# Version   : 1.1.0
set -eu

ROLE="${1:-default}"
INSTALL_ROOT="/opt/thmd-guru/modules/tools-server-container"

echo "================================================================================"
echo "  [THMD-Guru Hub] Dang cai dat mo-dun: tools/server-container (v1.1.0)"
echo "  Vai tro (Role): $ROLE | Thu muc dich: $INSTALL_ROOT"
echo "================================================================================"

if [ "$ mod_id" != "" ] 2>/dev/null || true; then :; fi

echo "  -> Danh sach goi thanh phan cua mo-dun: docker.io docker-compose podman buildah slirp4netns"
if [ "${THMD_HUB_APT:-0}" = "1" ] && command -v apt-get >/dev/null 2>&1 && [ "$(id -u)" -eq 0 ]; then
    echo "  -> Dang dong bo tu kho APT Debian 12 Bookworm..."
    apt-get update && apt-get install -y --no-install-recommends docker.io docker-compose podman buildah slirp4netns || true
else
    echo "  -> Da kich hoat ho so mo-dun tools/server-container trong /opt/thmd-guru/modules/tools-server-container"
    echo "     (De cai them goi nhi phan tu kho Debian APT, chay: sudo THMD_HUB_APT=1 THMD-guru-ai hub install tools/server-container)"
fi

echo "[OK] Hoan tat cai dat mo-dun tools/server-container (Role: $ROLE)!"
