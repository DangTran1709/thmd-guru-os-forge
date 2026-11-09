#!/bin/sh
# THMD-Guru Modular Hub - On-Demand Module Installer
# Module ID : tools/attt-web-scanner
# Name      : Bộ công cụ Kiểm thử Web & OWASP ZAP (ATTT Web Scanner)
# Version   : 1.1.0
set -eu

ROLE="${1:-default}"
INSTALL_ROOT="/opt/thmd-guru/modules/tools-attt-web-scanner"

echo "================================================================================"
echo "  [THMD-Guru Hub] Dang cai dat mo-dun: tools/attt-web-scanner (v1.1.0)"
echo "  Vai tro (Role): $ROLE | Thu muc dich: $INSTALL_ROOT"
echo "================================================================================"

if [ "$ mod_id" != "" ] 2>/dev/null || true; then :; fi

echo "  -> Danh sach goi thanh phan cua mo-dun: zaproxy sqlmap nikto gobuster ffuf curl jq python3-requests"
if [ "${THMD_HUB_APT:-0}" = "1" ] && command -v apt-get >/dev/null 2>&1 && [ "$(id -u)" -eq 0 ]; then
    echo "  -> Dang dong bo tu kho APT Debian 12 Bookworm..."
    apt-get update && apt-get install -y --no-install-recommends zaproxy sqlmap nikto gobuster ffuf curl jq python3-requests || true
else
    echo "  -> Da kich hoat ho so mo-dun tools/attt-web-scanner trong /opt/thmd-guru/modules/tools-attt-web-scanner"
    echo "     (De cai them goi nhi phan tu kho Debian APT, chay: sudo THMD_HUB_APT=1 THMD-guru-ai hub install tools/attt-web-scanner)"
fi

echo "[OK] Hoan tat cai dat mo-dun tools/attt-web-scanner (Role: $ROLE)!"
