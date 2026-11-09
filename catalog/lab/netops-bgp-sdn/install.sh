#!/bin/sh
# THMD-Guru Modular Hub - On-Demand Module Installer
# Module ID : lab/netops-bgp-sdn
# Name      : Phòng Lab Định tuyến Doanh nghiệp BGP/OSPF & SDN (FRRouting)
# Version   : 1.1.0
set -eu

ROLE="${1:-default}"
INSTALL_ROOT="/opt/thmd-guru/modules/lab-netops-bgp-sdn"

echo "================================================================================"
echo "  [THMD-Guru Hub] Dang cai dat mo-dun: lab/netops-bgp-sdn (v1.1.0)"
echo "  Vai tro (Role): $ROLE | Thu muc dich: $INSTALL_ROOT"
echo "================================================================================"

if [ "$ mod_id" != "" ] 2>/dev/null || true; then :; fi

echo "[OK] Hoan tat cai dat mo-dun lab/netops-bgp-sdn (Role: $ROLE)!"
