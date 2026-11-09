#!/usr/bin/env bash
# THMD-Guru LAB — VM2 (Ubuntu Server / THMD-Guru Server): Web target
# Dùng: sudo bash vm2-web-target/setup.sh
set -euo pipefail
[ "$(id -u)" -eq 0 ] || { echo "Cần chạy bằng sudo/root" >&2; exit 1; }
HERE="$(cd "$(dirname "$0")" && pwd)"
LAB_IP="${LAB_IP:-192.168.80.20}"
DEST=/opt/thmd-lab/vm2-web-target

export DEBIAN_FRONTEND=noninteractive
if ! command -v docker >/dev/null 2>&1; then
    echo "[VM2] Cài Docker Engine + Compose plugin..."
    apt-get update -qq
    apt-get install -y -qq ca-certificates curl
    if apt-cache show docker-compose-v2 >/dev/null 2>&1; then
        apt-get install -y -qq docker.io docker-compose-v2      # Ubuntu 22.04+/24.04
    else
        apt-get install -y -qq docker.io docker-compose-plugin || apt-get install -y -qq docker.io docker-compose
    fi
    systemctl enable --now docker
fi
COMPOSE="docker compose"
$COMPOSE version >/dev/null 2>&1 || COMPOSE="docker-compose"

if ! ip -4 addr | grep -q "inet $LAB_IP/"; then
    echo "[WARN] Máy chưa có IP $LAB_IP. Chạy trước: sudo bash $HERE/../common/set-static-ip.sh vm2" >&2
    exit 1
fi

mkdir -p "$DEST" /var/log/nginx
cp -r "$HERE/docker-compose.yml" "$HERE/nginx" "$DEST/"
cd "$DEST"
echo "LAB_IP=$LAB_IP" > .env
echo "[VM2] Kéo image và khởi chạy (lần đầu mất vài phút)..."
$COMPOSE pull -q
$COMPOSE up -d

# Khởi tạo CSDL DVWA tự động (tương đương bấm "Create / Reset Database")
for _ in $(seq 1 30); do
    if curl -s -o /dev/null -w '%{http_code}' "http://$LAB_IP:8081/setup.php" | grep -q 200; then
        tok=$(curl -s -c /tmp/dvwa.c "http://$LAB_IP:8081/setup.php" | grep -o "user_token' value='[a-f0-9]*" | cut -d"'" -f3)
        curl -s -b /tmp/dvwa.c -d "create_db=Create+%2F+Reset+Database&user_token=$tok" \
            "http://$LAB_IP:8081/setup.php" >/dev/null && echo "[VM2] DVWA database initialized"
        break
    fi
    sleep 3
done

$COMPOSE ps
cat <<EOF

[OK] VM2 sẵn sàng:
  http://$LAB_IP/            Danh mục mục tiêu (Nginx)
  http://$LAB_IP:3000/       OWASP Juice Shop
  http://$LAB_IP:8081/       DVWA (admin / password)
  http://$LAB_IP:8080/WebGoat WebGoat
  Log bằng chứng: tail -f /var/log/nginx/lab_access.log
Nhớ chụp snapshot VMware "VM2-clean" trước khi quét.
EOF

