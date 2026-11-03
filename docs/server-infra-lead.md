# Tài Liệu Kỹ Thuật: THMD-Guru Linux Server (`server-infra-lead`)

## 1. Kiến trúc Máy chủ Doanh nghiệp & Cloud-Native
- **Minimal Headless Architecture:** Không cài đặt X11/Wayland, giảm tối đa diện tích bề mặt tấn công (Attack Surface) và tiết kiệm RAM (< 250MB khi khởi động).
- **Cài đặt Tự động (`preseed/thmd-guru-server.cfg`) & Cloud-Init:** Hỗ trợ cài đặt tự động phân vùng LVM hoặc khởi tạo tức thì trên AWS, GCP, Proxmox, OpenStack.
- **Bảo mật Truy cập & Tường lửa:**
  - `90-thmd-guru-hardened.conf`: Khóa đăng nhập SSH bằng mật khẩu, chỉ cho phép `PubkeyAuthentication yes`, tắt `X11Forwarding`, giới hạn `MaxAuthTries 3`.
  - `thmd-guru-sshd.local`: Kích hoạt `Fail2ban` tự động chặn IP brute-force SSH.
  - `nftables.conf`: Chính sách mặc định `policy drop` chiều vào, chỉ mở cổng `22/tcp` (SSH) và `9090/tcp` (Cockpit HTTPS).
- **Vận hành & Container:** Tích hợp sẵn **Podman**, **Cockpit Web UI**, **Prometheus Node Exporter**, **LVM2 / Btrfs / MDADM** và lệnh `guru console` (`packages/guru-server-console/`).
