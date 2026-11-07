#!/usr/bin/env bash
# THMD-Guru LAB — VM1 (Kali Linux / THMD-Guru ATTT) : OWASP ZAP scanner
# Dùng: sudo bash vm1-kali-zap/setup.sh
set -euo pipefail
[ "$(id -u)" -eq 0 ] || { echo "Cần chạy bằng sudo/root" >&2; exit 1; }
HERE="$(cd "$(dirname "$0")" && pwd)"

echo "[VM1] Cài OWASP ZAP, Python3, nftables..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
# Kali: gói 'zaproxy'. Debian/THMD-Guru ATTT không có sẵn -> dùng snap hoặc bản cài từ zaproxy.org
if ! apt-get install -y -qq zaproxy python3 nftables curl jq 2>/dev/null; then
    apt-get install -y -qq python3 nftables curl jq default-jre-headless
    if ! command -v zap.sh >/dev/null 2>&1; then
        echo "[VM1] Gói zaproxy không có trong kho. Tải bản Linux từ https://www.zaproxy.org/download/"
        echo "      rồi giải nén vào /opt/zaproxy và tạo liên kết: ln -s /opt/zaproxy/zap.sh /usr/local/bin/zap.sh"
    fi
fi

mkdir -p /etc/thmd-guru
if [ ! -s /etc/thmd-guru/zap-api-key ]; then
    head -c 24 /dev/urandom | od -An -tx1 | tr -d ' \n' > /etc/thmd-guru/zap-api-key
    chmod 640 /etc/thmd-guru/zap-api-key
    chgrp "${SUDO_USER:-root}" /etc/thmd-guru/zap-api-key 2>/dev/null || true
fi
echo "[VM1] ZAP API key: /etc/thmd-guru/zap-api-key"

# Lớp bảo vệ "Phạm vi an toàn": chặn VM1 gửi lưu lượng ra ngoài LAB
install -m 0644 "$HERE/egress-guard.nft" /etc/nftables.d-thmd-lab-guard.nft
nft -f /etc/nftables.d-thmd-lab-guard.nft
cat > /etc/systemd/system/thmd-lab-guard.service <<'EOF'
[Unit]
Description=THMD-Guru LAB egress guard (VM1 scanner chi duoc quet 192.168.80.20)
After=network-pre.target
Before=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/sbin/nft -f /etc/nftables.d-thmd-lab-guard.nft
ExecStop=/usr/sbin/nft delete table inet thmd_lab_guard
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable --now thmd-lab-guard.service >/dev/null
echo "[VM1] Egress guard đang bật. Tạm tắt để cập nhật gói: sudo systemctl stop thmd-lab-guard"

cat <<EOF

[OK] VM1 sẵn sàng. Các bước tiếp theo:
  zap.sh -daemon -host 127.0.0.1 -port 8090 -config api.key=\$(sudo cat /etc/thmd-guru/zap-api-key) &
  python3 $HERE/zap_scan.py --target http://192.168.80.20:3000 --mode baseline \\
          --push http://192.168.80.30:8000/api/v1/alerts
EOF

