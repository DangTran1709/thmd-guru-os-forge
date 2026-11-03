# Tài Liệu Kỹ Thuật & Kiểm Toán Bảo Mật: THMD-Guru Linux ATTT (`security-attt-lead`)

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
     - `guru sandbox run <cmd>` / `guru sandbox netless <cmd>`: Kiến trúc **Fail-Closed (CWE-636 Mitigation)** — ưu tiên thực thi qua `Firejail` (`--seccomp --caps.drop=all --nonewprivs --noroot`), chuyển tiếp sang `Bubblewrap (bwrap)` hoặc `Linux Kernel Namespaces (unshare -r -n -m -p -u -i -f)`, và **từ chối thực thi (`exit 126`)** nếu không có cơ chế cô lập nhân.
     - `sudo guru stealth [on|off|status]`: Đổi địa chỉ MAC trực tiếp trên card mạng đang hoạt động (`02:xx:xx:xx:xx:xx`), chặn cả ICMPv4 & ICMPv6, vô hiệu hóa IPv6 (`disable_ipv6=1`) chống rò rỉ địa chỉ MAC qua SLAAC EUI-64, và nạp bảng `nftables` chặn phát tán tên máy qua mDNS (`UDP 5353`), LLMNR (`TCP/UDP 5355`), NetBIOS (`UDP 137-138`).

## 2. Nhật Ký Vá Lỗ Hổng Pentest & QA (Security Hardening Patch)
1. **CWE-636 (Fail-Closed Sandbox):** Loại bỏ hoàn toàn nhánh thực thi trần khi thiếu `firejail`.
2. **CWE-798 (Hardcoded Credentials & Privilege Escalation):** Mã hóa SHA-512 mật khẩu khởi tạo trong `preseed.cfg`, ép buộc đổi mật khẩu ở lần đăng nhập đầu tiên (`chage -d 0 guru`), loại bỏ `NOPASSWD:ALL` trong `cloud-init`, đặt cứng `PermitRootLogin no` và giới hạn tốc độ kết nối mới (`limit rate 10/minute burst 5 packets`) trên cổng `22` & `9090`.
3. **Cross-Edition Package Isolation:** Cô lập tuyệt đối kho gói `/pool/main/*.deb` và plugin `/usr/lib/guru/commands/*` theo từng phiên bản (`desktop`, `server`, `attt`), ngăn chặn thư viện đồ họa GTK3 tràn sang bản Server Headless.
4. **Supply Chain RSA-4096 Signing:** Ký số toàn bộ kho APT (`dists/genesis/Release.gpg`) bằng khóa RSA-4096 và xác thực chữ ký bằng `openssl dgst -sha256 -verify` trước khi cài đặt.
