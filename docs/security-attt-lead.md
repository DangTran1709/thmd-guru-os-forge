# Tài Liệu Kỹ Thuật: THMD-Guru Linux ATTT (`security-attt-lead`)

## 1. Kiến trúc Bảo mật & Đào tạo An Toàn Thông Tin
- **Môi trường Đồ họa Tác chiến (`XFCE4 + LightDM`):** Tốc độ phản hồi tức thì, nhẹ, ổn định khi chạy nhiều máy ảo hoặc phân tích gói tin lớn.
- **Gia cố Nhân & Hệ thống (Kernel & Userland Hardening):**
  - Kích hoạt bắt buộc **AppArmor (`apparmor=1 security=apparmor`)** ngay từ tham số khởi động Kernel, đi kèm `apparmor-profiles-extra` và `auditd`.
  - Áp dụng cấu hình `91-attt.conf` khóa con trỏ nhân (`kptr_restrict=2`), chặn `ptrace` trái phép (`yama.ptrace_scope=2`), khóa `unprivileged_bpf_disabled=1`.
  - Tường lửa `nftables` mặc định chặn toàn bộ kết nối chiều vào (`policy drop`).
- **4 Nhóm Công cụ Đào tạo ATTT Chuẩn Debian 12:**
  1. **Kiểm toán & Phòng thủ (Blue Team / SOC):** `lynis`, `rkhunter`, `chkrootkit`, `clamav`, `aide`, `fail2ban`.
  2. **Chẩn đoán & Phân tích Mạng:** `wireshark`, `tshark`, `tcpdump`, `nmap`, `socat`, `mtr-tiny`, `wireguard-tools`.
  3. **Pháp y Số & Dịch ngược (DFIR & Reverse Engineering):** `sleuthkit`, `foremost`, `binwalk`, `exiftool`, `yara`, `radare2`, `gdb`, `testdisk`.
  4. **Cô lập & Ẩn danh Độc quyền (`guru-sandbox` & `guru-stealth`):**
     - `guru sandbox run <cmd>` / `guru sandbox netless <cmd>`: Thực thi tệp nghi ngờ trong container cô lập `Firejail` hạ toàn bộ capabilities (`--caps.drop=all --nonewprivs`).
     - `sudo guru stealth [on|off|status]`: Tự động ngẫu nhiên hóa địa chỉ MAC (`NetworkManager`) và ẩn phản hồi ICMP.
