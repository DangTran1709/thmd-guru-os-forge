#!/usr/bin/env bash
# THMD-Guru LAB — VM3 (Ubuntu Server / THMD-Guru Desktop): AI-RAG Server
# Dùng: sudo bash vm3-ai-rag/setup.sh
#       sudo LLM_MODEL=llama3.2:3b bash vm3-ai-rag/setup.sh
#       sudo OLLAMA_URL=http://192.168.80.254:11434 bash vm3-ai-rag/setup.sh   (dùng GPU của máy Host)
#       sudo USE_LLM=0 bash vm3-ai-rag/setup.sh                                (chỉ RAG + luật, không LLM)
set -euo pipefail
[ "$(id -u)" -eq 0 ] || { echo "Cần chạy bằng sudo/root" >&2; exit 1; }
HERE="$(cd "$(dirname "$0")" && pwd)"
LAB_IP="${LAB_IP:-192.168.80.30}"
LLM_MODEL="${LLM_MODEL:-qwen2.5:3b}"
EMBED_MODEL="${EMBED_MODEL:-nomic-embed-text}"
OLLAMA_URL="${OLLAMA_URL:-http://127.0.0.1:11434}"
USE_LLM="${USE_LLM:-auto}"
DEST=/opt/thmd-lab/vm3-ai-rag

export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq python3 python3-venv python3-pip curl nftables
if ! command -v docker >/dev/null 2>&1; then
    apt-cache show docker-compose-v2 >/dev/null 2>&1 \
        && apt-get install -y -qq docker.io docker-compose-v2 \
        || apt-get install -y -qq docker.io docker-compose-plugin || apt-get install -y -qq docker.io docker-compose
    systemctl enable --now docker
fi
COMPOSE="docker compose"; $COMPOSE version >/dev/null 2>&1 || COMPOSE="docker-compose"

# Kernel tuning cho Vector DB / LLM (giống profile THMD-Guru Desktop)
cat > /etc/sysctl.d/91-thmd-lab-airag.conf <<'EOF'
vm.max_map_count = 1048576
vm.swappiness = 10
EOF
sysctl -q --system || true

mkdir -p "$DEST"
cp -r "$HERE/app" "$HERE/kb" "$HERE/docker-compose.yml" "$HERE/requirements.txt" "$DEST/"
cd "$DEST"

echo "[VM3] Khởi chạy Qdrant + Ollama..."
if [ "$OLLAMA_URL" = "http://127.0.0.1:11434" ]; then
    $COMPOSE up -d
else
    $COMPOSE up -d qdrant       # LLM chạy ở máy khác (Host GPU)
fi
for _ in $(seq 1 30); do curl -sf http://127.0.0.1:6333/readyz >/dev/null && break; sleep 2; done

if [ "$USE_LLM" != "0" ] && [ "$OLLAMA_URL" = "http://127.0.0.1:11434" ]; then
    for _ in $(seq 1 30); do curl -sf "$OLLAMA_URL/api/tags" >/dev/null && break; sleep 2; done
    echo "[VM3] Tải mô hình $LLM_MODEL và $EMBED_MODEL (lần đầu ~2.5 GB)..."
    docker exec lab-ollama ollama pull "$LLM_MODEL"
    docker exec lab-ollama ollama pull "$EMBED_MODEL"
fi

python3 -m venv "$DEST/.venv"
"$DEST/.venv/bin/pip" install -q --upgrade pip
"$DEST/.venv/bin/pip" install -q -r requirements.txt

cat > /etc/default/thmd-lab-airag <<EOF
OLLAMA_URL=$OLLAMA_URL
LLM_MODEL=$LLM_MODEL
EMBED_MODEL=$EMBED_MODEL
QDRANT_URL=http://127.0.0.1:6333
USE_LLM=$USE_LLM
DATA_DIR=$DEST/data
USD_PER_1K_TOKENS=0
EOF

if [ "$USE_LLM" != "0" ]; then
    set -a; . /etc/default/thmd-lab-airag; set +a
    "$DEST/.venv/bin/python" -m app.ingest || echo "[WARN] Chưa nạp được vector vào Qdrant; hệ thống vẫn chạy với BM25."
fi

cat > /etc/systemd/system/thmd-lab-airag.service <<EOF
[Unit]
Description=THMD-Guru LAB AI-RAG Server (FastAPI :8000)
After=docker.service network-online.target
Wants=network-online.target

[Service]
EnvironmentFile=/etc/default/thmd-lab-airag
WorkingDirectory=$DEST
ExecStart=$DEST/.venv/bin/uvicorn app.main:app --host $LAB_IP --port 8000
Restart=on-failure
NoNewPrivileges=yes
ProtectSystem=strict
ReadWritePaths=$DEST/data

[Install]
WantedBy=multi-user.target
EOF
mkdir -p "$DEST/data"
systemctl daemon-reload
systemctl enable --now thmd-lab-airag.service

# Chỉ nhận API từ LAB; Qdrant/Ollama đã bind 127.0.0.1
cat > /etc/nftables.d-thmd-lab-airag.nft <<'EOF'
table inet thmd_lab_airag {
    chain input {
        type filter hook input priority 0; policy accept;
        tcp dport 8000 ip saddr != { 127.0.0.1, 192.168.80.0/24 } drop
    }
}
EOF
nft -f /etc/nftables.d-thmd-lab-airag.nft || true

sleep 3
curl -s "http://$LAB_IP:8000/health" && echo
cat <<EOF

[OK] VM3 sẵn sàng: http://$LAB_IP:8000/  (API docs: http://$LAB_IP:8000/docs)
  Log dịch vụ : journalctl -u thmd-lab-airag -f
  Đổi mô hình : sửa /etc/default/thmd-lab-airag rồi systemctl restart thmd-lab-airag
EOF

