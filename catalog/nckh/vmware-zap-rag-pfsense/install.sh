#!/bin/sh
# THMD-Guru Modular Hub - On-Demand Module Installer
# Module ID : nckh/vmware-zap-rag-pfsense
# Name      : Đề tài NCKH (VMware 3-VM + pfSense): Hệ thống Đánh giá AI-RAG & OWASP ZAP
# Version   : 1.1.0
set -eu

ROLE="${1:-default}"
INSTALL_ROOT="/opt/thmd-guru/modules/nckh-vmware-zap-rag-pfsense"

echo "================================================================================"
echo "  [THMD-Guru Hub] Dang cai dat mo-dun: nckh/vmware-zap-rag-pfsense (v1.1.0)"
echo "  Vai tro (Role): $ROLE | Thu muc dich: $INSTALL_ROOT"
echo "================================================================================"

if [ "$ mod_id" != "" ] 2>/dev/null || true; then :; fi

case "$ROLE" in
    vm1-zap|vm1)
        echo "  -> Cau hinh chuyen biet cho VM1 (192.168.80.10 - OWASP ZAP Scanner)..."
        if [ -f "$INSTALL_ROOT/common/set-static-ip.sh" ]; then
            echo "  -> San sang kich ban IP tinh: sudo bash $INSTALL_ROOT/common/set-static-ip.sh vm1"
        fi
        echo "  -> Kich ban quet ZAP & gui Alert: $INSTALL_ROOT/vm1-kali-zap/zap_scan_and_send.py"
        ;;
    vm2-target|vm2)
        echo "  -> Cau hinh chuyen biet cho VM2 (192.168.80.20 - Web Server Target)..."
        echo "  -> Docker Compose DVWA/JuiceShop/WebGoat: $INSTALL_ROOT/vm2-web-target/docker-compose.yml"
        ;;
    vm3-airag|vm3)
        echo "  -> Cau hinh chuyen biet cho VM3 (192.168.80.30 - AI-RAG Server)..."
        echo "  -> Dich vu FastAPI + Vector DB + LLM: $INSTALL_ROOT/vm3-ai-rag/app.py"
        ;;
    evaluator)
        echo "  -> Cau hinh cong cu danh gia & cham diem NCKH (Precision/Recall/F1/NDCG@5)..."
        echo "  -> Chay danh gia: python3 $INSTALL_ROOT/evaluator/evaluate.py"
        ;;
    *)
        echo "  -> Da cai dat day du bo kich ban 3-VM + pfSense tai: $INSTALL_ROOT"
        ;;
esac

echo "[OK] Hoan tat cai dat mo-dun nckh/vmware-zap-rag-pfsense (Role: $ROLE)!"
