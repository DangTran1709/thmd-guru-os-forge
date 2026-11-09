#!/bin/sh
# THMD-Guru Modular Hub - On-Demand Module Installer
# Module ID : tools/server-web-waf
# Name      : Máy chủ Web, Reverse Proxy & Tường lửa (Nginx / WAF / Cockpit)
# Version   : 1.1.0
set -eu

ROLE="${1:-default}"
INSTALL_ROOT="/opt/thmd-guru/modules/tools-server-web-waf"

echo "================================================================================"
echo "  [THMD-Guru Hub] Dang cai dat mo-dun: tools/server-web-waf (v1.1.0)"
echo "  Vai tro (Role): $ROLE | Thu muc dich: $INSTALL_ROOT"
echo "================================================================================"

if [ "$ mod_id" != "" ] 2>/dev/null || true; then :; fi

echo "  -> Danh sach goi thanh phan cua mo-dun: nginx nftables cockpit certbot"
if [ "${THMD_HUB_APT:-0}" = "1" ] && command -v apt-get >/dev/null 2>&1 && [ "$(id -u)" -eq 0 ]; then
    echo "  -> Dang dong bo tu kho APT Debian 12 Bookworm..."
    apt-get update && apt-get install -y --no-install-recommends nginx nftables cockpit certbot || true
else
    echo "  -> Da kich hoat ho so mo-dun tools/server-web-waf trong /opt/thmd-guru/modules/tools-server-web-waf"
    echo "     (De cai them goi nhi phan tu kho Debian APT, chay: sudo THMD_HUB_APT=1 THMD-guru-ai hub install tools/server-web-waf)"
fi

echo "[OK] Hoan tat cai dat mo-dun tools/server-web-waf (Role: $ROLE)!"
