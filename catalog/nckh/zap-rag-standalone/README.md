# Phòng Lab NCKH Liên ngành: AI + Hybrid RAG Xác minh & Ưu tiên Cảnh báo OWASP ZAP (`nckh-zap-rag`)

Phòng thí nghiệm chuẩn hóa cho các đề tài Nghiên cứu Khoa học (NCKH), Khóa luận tốt nghiệp và Luận văn Thạc sĩ kết hợp **Kỹ thuật Mạng + An toàn Thông tin + Trí tuệ Nhân tạo (AI/RAG) + Công nghệ Phần mềm**.

## 1. Các Đề tài NCKH Hỗ trợ Trực tiếp
1. **Đề tài 1:** *Đánh giá hiệu quả AI kết hợp RAG trong xác minh và ưu tiên cảnh báo bảo mật Web từ ZAP*
2. **Đề tài 2:** *Ứng dụng AI trong phát hiện và đánh giá lỗ hổng bảo mật Web theo OWASP (OWASP Top 10)*

## 2. Hai Chế độ Triển khai Thực nghiệm

### Chế độ A: Chạy trên Hệ thống 4 Máy ảo VMware (`VMnet` Multi-VM Topology)
- **VM 1 (`THMD-Guru ATTT` - `VMnet2` `172.28.10.10/24`):**
  ```bash
  sudo THMD-guru-ai vm-node init scanner-red
  ```
- **VM 2 (`THMD-Guru Server` - `VMnet8, VMnet2, VMnet3, VMnet4`):**
  ```bash
  sudo THMD-guru-ai vm-node init edge-router-waf
  ```
- **VM 3 (`THMD-Guru Server` - `VMnet3` `172.28.20.10/24`):**
  ```bash
  sudo THMD-guru-ai vm-node init dmz-web-target
  ```
- **VM 4 (`THMD-Guru Desktop/Server` - `VMnet4` `172.28.30.10/24`):**
  ```bash
  sudo THMD-guru-ai vm-node init ai-rag-soc
  ```

### Chế độ B: Chạy Thực nghiệm & Xuất Số liệu Khoa học Ngay lập tức (`Precision`, `Recall`, `F1`, `FPRR`, `NDCG@5`)
```bash
THMD-guru-ai lab run nckh-zap-rag
```
Hoặc gọi trực tiếp:
```bash
python3 /usr/share/thmd-guru/labs/nckh-zap-rag/run_experiment.py --output-dir ./results
```

