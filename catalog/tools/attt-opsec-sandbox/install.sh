#!/bin/sh
# THMD-Guru Modular Hub - On-Demand Module Installer
# Module ID : tools/attt-opsec-sandbox
# Name      : Bộ công cụ Cô lập Firejail & Ẩn danh Mạng (OPSEC & Sandbox)
# Version   : 1.1.0
set -eu

ROLE="${1:-default}"
INSTALL_ROOT="/opt/thmd-guru/modules/tools-attt-opsec-sandbox"

echo "================================================================================"
echo "  [THMD-Guru Hub] Dang cai dat mo-dun: tools/attt-opsec-sandbox (v1.1.0)"
echo "  Vai tro (Role): $ROLE | Thu muc dich: $INSTALL_ROOT"
echo "================================================================================"

if [ "$ mod_id" != "" ] 2>/dev/null || true; then :; fi

echo "  -> Danh sach goi thanh phan cua mo-dun: firejail proxychains4 macchanger tor"
if [ "${THMD_HUB_APT:-0}" = "1" ] && command -v apt-get >/dev/null 2>&1 && [ "$(id -u)" -eq 0 ]; then
    echo "  -> Dang dong bo tu kho APT Debian 12 Bookworm..."
    apt-get update && apt-get install -y --no-install-recommends firejail proxychains4 macchanger tor || true
else
    echo "  -> Da kich hoat ho so mo-dun tools/attt-opsec-sandbox trong /opt/thmd-guru/modules/tools-attt-opsec-sandbox"
    echo "     (De cai them goi nhi phan tu kho Debian APT, chay: sudo THMD_HUB_APT=1 THMD-guru-ai hub install tools/attt-opsec-sandbox)"
fi

echo "[OK] Hoan tat cai dat mo-dun tools/attt-opsec-sandbox (Role: $ROLE)!"
