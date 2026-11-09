# Cấu hình pfSense cho LAB `vmware-zap-rag-pfsense`

## 1. Tạo máy ảo
- `New Virtual Machine → Custom`, Guest OS: **Other → FreeBSD 14 64-bit**, 1 vCPU, 1 GB RAM, 16 GB disk.
- **Network Adapter 1 → VMnet8 (NAT)**: sẽ là `WAN` (`em0` / `vmx0`).
- **Add → Network Adapter 2 → Custom: VMnet2**: sẽ là `LAN` (`em1` / `vmx1`).
- Gắn ISO `pfSense-CE-2.7.x-RELEASE-amd64.iso`, cài mặc định (ZFS hoặc UFS đều được).

## 2. Console sau khi cài
```
1) Assign Interfaces      -> VLANs: n | WAN: em0 | LAN: em1
2) Set interface(s) IP    -> 2 (LAN) -> 192.168.80.1 / 24 -> không đặt gateway upstream
                          -> IPv6: none
                          -> Enable DHCP server on LAN? n   (dùng IP tĩnh cho 3 VM, giúp lặp lại thực nghiệm)
                          -> Revert to HTTP webConfigurator? n
```
WAN nhận DHCP từ VMnet8 (ví dụ `192.168.x.128`). Truy cập WebGUI từ VM bất kỳ trong LAB: `https://192.168.80.1` (admin / pfsense, **đổi mật khẩu ngay**).

## 3. Thiết lập chung (System → General Setup)
- Hostname `lab-pfsense`, Domain `thmd.lab`, DNS `1.1.1.1`, `8.8.8.8`.
- `Services → DNS Resolver`: bật, tạo **Host Overrides**:
  | Host | Domain | IP |
  |---|---|---|
  | `kali` | `thmd.lab` | `192.168.80.10` |
  | `target` | `thmd.lab` | `192.168.80.20` |
  | `airag` | `thmd.lab` | `192.168.80.30` |
- `Firewall → NAT → Outbound`: **Automatic** (mặc định).

## 4. Aliases (Firewall → Aliases)
| Tên | Loại | Giá trị |
|---|---|---|
| `VM1_SCANNER` | Host | `192.168.80.10` |
| `VM2_TARGET`  | Host | `192.168.80.20` |
| `VM3_AIRAG`   | Host | `192.168.80.30` |
| `LAB_NET`     | Network | `192.168.80.0/24` |
| `UPDATE_PORTS`| Port | `53, 80, 443` |
| `AIRAG_PORTS` | Port | `8000` |

## 5. Luật LAN (Firewall → Rules → LAN), xử lý từ trên xuống

| # | Action | Source | Destination | Port | Mô tả |
|---|---|---|---|---|---|
| 1 | Pass | LAN net | LAN address | 443, 53 | Anti-lockout WebGUI + DNS Resolver |
| 2 | **Block + Log** | `VM1_SCANNER` | `! LAB_NET` | any | **Phạm vi an toàn:** máy quét không được ra ngoài LAB |
| 3 | Pass | `VM2_TARGET` | any | `UPDATE_PORTS` | VM2 cập nhật gói / kéo image Docker |
| 4 | Pass | `VM3_AIRAG` | any | `UPDATE_PORTS` | VM3 cập nhật gói / kéo mô hình Ollama |
| 5 | Block + Log | LAN net | any | any | Chặn mọi thứ còn lại (thay thế luật "Default allow LAN to any") |

> [!NOTE]
> Lưu lượng **giữa các VM cùng subnet `192.168.80.0/24`** (VM1 → VM2, VM1 → VM3) đi thẳng qua switch ảo VMnet2 ở tầng 2, **không đi qua pfSense**. Vì vậy pfSense ở mô hình này đóng vai trò **tường lửa biên (egress) và DNS**, không lọc được luồng quét nội bộ. Các luồng nội bộ được kiểm soát bằng:
> - nftables egress-guard trên VM1 (`vm1-kali-zap/egress-guard.nft`): VM1 chỉ được gửi tới `192.168.80.20` và `192.168.80.30:8000`.
> - nftables trên VM2/VM3 do `setup.sh` cài đặt.
>
> Nếu đề tài cần pfSense **lọc cả luồng quét** (ví dụ đo ảnh hưởng của WAF/IPS Suricata lên cảnh báo ZAP), hãy tách VM2 sang một VMnet riêng (ví dụ VMnet3 `192.168.90.0/24`, thêm NIC3 cho pfSense làm `OPT1/DMZ`). Khi đó toàn bộ luồng VM1 → VM2 bắt buộc đi qua pfSense.

## 6. Tuỳ chọn: bật Suricata IDS để so sánh
`System → Package Manager → Available Packages → suricata`. Bật trên `LAN` ở chế độ **IDS (Legacy, không chặn)** để ghi lại cảnh báo mạng song song với cảnh báo ZAP. Chỉ bật khi Host còn dư RAM (Suricata cần thêm ~512 MB, nên tăng pfSense lên 2 GB).

## 7. Sao lưu
`Diagnostics → Backup & Restore → Download configuration as XML`, lưu cùng thư mục đề tài để hội đồng có thể dựng lại y hệt.
