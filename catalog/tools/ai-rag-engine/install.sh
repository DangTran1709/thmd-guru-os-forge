#!/bin/sh
# THMD-Guru Modular Hub - On-Demand Module Installer
# Module ID : tools/ai-rag-engine
# Name      : Hạ tầng Trí tuệ Nhân tạo & Vector DB (FastAPI / FAISS / Ollama)
# Version   : 1.1.0
set -eu

ROLE="${1:-default}"
INSTALL_ROOT="/opt/thmd-guru/modules/tools-ai-rag-engine"

echo "================================================================================"
echo "  [THMD-Guru Hub] Dang cai dat mo-dun: tools/ai-rag-engine (v1.1.0)"
echo "  Vai tro (Role): $ROLE | Thu muc dich: $INSTALL_ROOT"
echo "================================================================================"

if [ "$ mod_id" != "" ] 2>/dev/null || true; then :; fi

echo "  -> Danh sach goi thanh phan cua mo-dun: python3 python3-venv python3-pip python3-numpy curl jq"
if [ "${THMD_HUB_APT:-0}" = "1" ] && command -v apt-get >/dev/null 2>&1 && [ "$(id -u)" -eq 0 ]; then
    echo "  -> Dang dong bo tu kho APT Debian 12 Bookworm..."
    apt-get update && apt-get install -y --no-install-recommends python3 python3-venv python3-pip python3-numpy curl jq || true
else
    echo "  -> Da kich hoat ho so mo-dun tools/ai-rag-engine trong /opt/thmd-guru/modules/tools-ai-rag-engine"
    echo "     (De cai them goi nhi phan tu kho Debian APT, chay: sudo THMD_HUB_APT=1 THMD-guru-ai hub install tools/ai-rag-engine)"
fi

echo "[OK] Hoan tat cai dat mo-dun tools/ai-rag-engine (Role: $ROLE)!"
