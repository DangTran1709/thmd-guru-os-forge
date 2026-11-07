# LAB NCKH: `vmware-zap-rag-pfsense`

**Đề tài:** Đánh giá hiệu quả AI kết hợp RAG trong xác minh và ưu tiên cảnh báo bảo mật Web từ OWASP ZAP
**Môi trường:** VMware Workstation, mạng LAB `VMnet2` (Host-Only) `192.168.80.0/24`, cổng ra là **pfSense**

```
 Internet ── Router (VMnet8 NAT / modem) ── pfSense (WAN: VMnet8 DHCP | LAN: 192.168.80.1/24)
                                                  │
                                    VMnet2 Host-Only / LAB 192.168.80.0/24
              ┌───────────────────────────────────┼───────────────────────────────────┐
     VM1 Kali + OWASP ZAP             VM2 Ubuntu Web Server (Target)       VM3 Ubuntu AI-RAG Server
     192.168.80.10  2 vCPU / 3 GB     192.168.80.20  2 vCPU / 4 GB          192.168.80.30  3 vCPU / 4 GB
     ZAP daemon :8090, Python script  Nginx :80 -> DVWA / Juice Shop /      FastAPI :8000, Qdrant :6333,
                                      WebGoat, MariaDB                      Ollama :11434 (LLM + embedding)
              │ (1) ZAP quét ──────────────► │                                     ▲
              └────── (2) Gửi Alert + Evidence (JSON) ─────────────────────────────┘
                                                              (3) AI-RAG phân tích, tạo báo cáo P1/P2/P3
                                                                         │
                                         Người đánh giá / GVHD: xem báo cáo, gắn nhãn Ground Truth, phản hồi
```

## 1. Danh sách máy và tài nguyên (máy Host 16 GB RAM, 6 nhân / 12 luồng)

| Máy | Hệ điều hành (thay thế bằng THMD-Guru) | vCPU | RAM | Ổ đĩa | Card mạng | IP |
|---|---|---|---|---|---|---|
| pfSense | pfSense CE 2.7.x | 1 | 1 GB | 16 GB | NIC1 = VMnet8 (WAN), NIC2 = VMnet2 (LAN) | WAN: DHCP, LAN: `192.168.80.1/24` |
| VM1 | Kali Linux 2024+ (hoặc THMD-Guru **ATTT**) | 2 | 3 GB | 40 GB | VMnet2 | `192.168.80.10/24`, GW `.1` |
| VM2 | Ubuntu Server 22.04/24.04 (hoặc THMD-Guru **Server**) | 2 | 4 GB | 40 GB | VMnet2 | `192.168.80.20/24`, GW `.1` |
| VM3 | Ubuntu Server 22.04/24.04 (hoặc THMD-Guru **Desktop**) | 3 | 4 GB | 60 GB | VMnet2 | `192.168.80.30/24`, GW `.1` |
| **Tổng** | | **8 luồng** | **12 GB** | | | Host còn ~4 GB |

> [!IMPORTANT]
> - **"Router" trong sơ đồ không phải một VM**: đó là NAT của VMware (VMnet8) hoặc modem nhà/trường. Không tạo thêm máy.
> - **RAM 4 GB cho VM3 chỉ đủ chạy mô hình nhỏ** (`qwen2.5:3b` / `llama3.2:3b` bản Q4, khoảng 2–2,5 GB) cộng mô hình embedding `nomic-embed-text` (khoảng 300 MB). Nếu muốn chạy mô hình 7B–8B, nâng VM3 lên 6–8 GB hoặc chạy Ollama trên máy Host (xem mục 4.3).
> - Nếu Host bị thiếu RAM, chỉ bật pfSense khi cần ra Internet tải gói; khi chạy thực nghiệm có thể tắt hẳn pfSense vì 3 VM vẫn liên lạc được với nhau trên cùng VMnet2.

## 2. Cấu hình VMware Virtual Network Editor (làm 1 lần)

1. `Edit → Virtual Network Editor → Change Settings`.
2. Chọn **VMnet2**, kiểu **Host-only**, Subnet IP `192.168.80.0`, mask `255.255.255.0`.
3. **Bỏ chọn** `Use local DHCP service` (pfSense hoặc IP tĩnh sẽ đảm nhiệm).
4. **Lưu ý trùng IP:** card ảo của máy Host trên VMnet2 mặc định lấy `192.168.80.1`, **trùng với pfSense**. Hãy làm một trong hai cách:
   - Bỏ chọn `Connect a host virtual adapter to this network` (cách cách ly tốt nhất), **hoặc**
   - Vào `ncpa.cpl → VMware Network Adapter VMnet2 → IPv4` trên Windows, đặt IP tĩnh **`192.168.80.254/24`**, không đặt gateway.
5. VMnet8 (NAT) để mặc định, chỉ dùng cho WAN của pfSense.

## 3. Cấu hình pfSense

Xem chi tiết từng bước và bảng luật tường lửa tại [pfsense/pfsense-setup.md](pfsense/pfsense-setup.md). Tóm tắt:
- LAN `192.168.80.1/24`, DNS Resolver bật, NAT Outbound tự động.
- **Luật Phạm vi an toàn:** chặn mọi lưu lượng từ VM1 (máy quét) đi ra Internet, chỉ cho VM1 truy cập `192.168.80.20` (mục tiêu) và `192.168.80.30:8000` (AI-RAG). VM2/VM3 chỉ được ra Internet qua cổng 80/443/53 để cập nhật gói.

## 4. Dựng từng máy

Sao chép thư mục lab này vào mỗi VM (USB, `scp`, hoặc nếu dùng THMD-Guru thì đã có sẵn tại `/usr/share/thmd-guru/labs/vmware-zap-rag-pfsense/`).

```bash
# Trên mỗi VM, đặt IP tĩnh trước (tự nhận diện netplan / NetworkManager / ifupdown)
sudo bash common/set-static-ip.sh vm1   # hoặc vm2 / vm3
```

### 4.1. VM2: Web Server mục tiêu (dựng trước)
```bash
sudo bash vm2-web-target/setup.sh       # Docker + Nginx + DVWA + Juice Shop + WebGoat + MariaDB
```
| URL qua Nginx (cổng 80) | Ứng dụng |
|---|---|
| `http://192.168.80.20/` | Trang danh mục mục tiêu |
| `http://192.168.80.20/dvwa/` hoặc `:8081` | DVWA (admin / password, nhớ bấm *Create / Reset Database*) |
| `http://192.168.80.20:3000/` | OWASP Juice Shop (SPA, nên truy cập thẳng cổng 3000) |
| `http://192.168.80.20:8080/WebGoat` | WebGoat |

Log truy cập Nginx được ghi tại `/var/log/nginx/lab_access.log` để đối chiếu bằng chứng quét.

### 4.2. VM1: Kali + OWASP ZAP
```bash
sudo bash vm1-kali-zap/setup.sh         # zaproxy, python3, nftables egress-guard (chỉ cho phép quét 192.168.80.20)
# Chạy ZAP daemon (API key lưu ở /etc/thmd-guru/zap-api-key)
zap.sh -daemon -host 127.0.0.1 -port 8090 -config api.key=$(sudo cat /etc/thmd-guru/zap-api-key) &
# (1) Quét  +  (2) gửi Alert + Evidence sang AI-RAG
python3 vm1-kali-zap/zap_scan.py --target http://192.168.80.20:3000 --mode baseline \
        --push http://192.168.80.30:8000/api/v1/alerts
```
Kết quả thô lưu tại `./zap-output/<run_id>/zap_alerts.json` (kèm request/response làm bằng chứng).

### 4.3. VM3: AI-RAG Server
```bash
sudo bash vm3-ai-rag/setup.sh           # Docker (Qdrant, Ollama), Python venv, FastAPI service systemd
# Mặc định kéo qwen2.5:3b + nomic-embed-text. Đổi mô hình:
sudo LLM_MODEL=llama3.2:3b bash vm3-ai-rag/setup.sh
# Nếu Host có GPU và chạy Ollama trên Windows: OLLAMA_URL=http://192.168.80.254:11434
```
| Endpoint | Chức năng |
|---|---|
| `POST /api/v1/alerts` | Nhận Alert + Evidence từ VM1 (bước 2) |
| `POST /api/v1/runs/{run_id}/analyze` | (3) RAG truy hồi OWASP/CWE/CVE/ZAP Docs, LLM xác minh TP/FP, tính điểm ưu tiên P1/P2/P3 |
| `GET  /api/v1/runs/{run_id}/report?format=md\|html\|json` | Báo cáo có trích dẫn nguồn tri thức |
| `POST /api/v1/runs/{run_id}/labels` | Người đánh giá gắn nhãn Ground Truth / phản hồi |
| `GET  /api/v1/runs/{run_id}/metrics` | Precision / Recall / F1, FPRR, NDCG@5, thời gian xử lý, chi phí (token) |
| `GET  /` | Dashboard đơn giản cho GVHD |

Kho tri thức (`vm3-ai-rag/kb/`) gồm OWASP Top 10, CWE, CVSS, quy tắc loại trừ dương tính giả theo WSTG và mô tả rule ZAP. Có thể bổ sung tài liệu `.md`/`.json`/`.txt` rồi chạy lại `python3 -m app.ingest`.

## 5. Người đánh giá / GVHD: gắn nhãn và đo kết quả

```bash
# Trên máy bất kỳ trong LAB (hoặc Host qua 192.168.80.254)
python3 evaluator/evaluate.py --server http://192.168.80.30:8000 --run <run_id> --labels evaluator/ground_truth_template.csv
```
Script in bảng so sánh **3 phương pháp** (ZAP thô, LLM không RAG, LLM + RAG) theo các đầu ra nghiên cứu trong sơ đồ:

| Đầu ra nghiên cứu | Chỉ số đo |
|---|---|
| Giảm false positive | FP, **FPRR %** so với ZAP thô |
| Ưu tiên cảnh báo quan trọng | **NDCG@5**, phân hạng P1/P2/P3 |
| Báo cáo có nguồn dẫn | Tỷ lệ cảnh báo có trích dẫn CWE/WSTG/OWASP (**Citation Coverage %**) |
| Precision / Recall / F1 | Tính theo nhãn Ground Truth của người đánh giá |
| Thời gian xử lý và chi phí | ms/cảnh báo, tổng token vào/ra, chi phí ước tính (0 nếu chạy LLM nội bộ) |

Chạy thử **không cần dựng VM** (dùng bộ dữ liệu mẫu, chế độ luật thuần, không cần Ollama):
```bash
THMD-guru-ai lab run vmware-zap-rag-pfsense
# hoặc
python3 evaluator/evaluate.py --offline-demo
```

## 6. Phạm vi an toàn (bắt buộc ghi trong đề cương)

- Chỉ quét trong môi trường LAB được cấp phép trên VMware (`192.168.80.20`).
- `vm1-kali-zap/zap_scan.py` **từ chối** mọi mục tiêu ngoài danh sách cho phép trong `topology.json` (`allowed_scan_targets`).
- Lớp chặn thứ hai: nftables egress-guard trên VM1 và luật pfSense chặn VM1 ra Internet.
- Chụp **snapshot** cả 4 máy sau khi dựng xong, trước mỗi lần thực nghiệm, để khôi phục trạng thái gốc và đảm bảo tính lặp lại (reproducibility).
