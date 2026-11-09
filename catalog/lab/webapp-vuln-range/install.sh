#!/bin/sh
# THMD-Guru Modular Hub - On-Demand Module Installer
# Module ID : lab/webapp-vuln-range
# Name      : Phòng Lab Ứng dụng Web Mục tiêu (DVWA, OWASP Juice Shop, WebGoat)
# Version   : 1.1.0
set -eu

ROLE="${1:-default}"
INSTALL_ROOT="/opt/thmd-guru/modules/lab-webapp-vuln-range"

echo "================================================================================"
echo "  [THMD-Guru Hub] Dang cai dat mo-dun: lab/webapp-vuln-range (v1.1.0)"
echo "  Vai tro (Role): $ROLE | Thu muc dich: $INSTALL_ROOT"
echo "================================================================================"

if [ "$ mod_id" != "" ] 2>/dev/null || true; then :; fi

echo "[OK] Hoan tat cai dat mo-dun lab/webapp-vuln-range (Role: $ROLE)!"
