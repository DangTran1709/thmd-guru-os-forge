# Chiến Lược Nhân Hệ Điều Hành (Kernel Strategy) — THMD-Guru Linux

**Chịu trách nhiệm:** `chief-os-architect`

## 1. Kiến trúc Hybrid Kernel Tuning (Mặc định cho v1.0 "Genesis")
Để đảm bảo tính tương thích phần cứng tối đa, hỗ trợ Secure Boot và nhận bản vá CVE tức thời từ Debian Security Team, **THMD-Guru Linux 1.0** sử dụng nhân `linux-image-amd64` (Debian 12 Bookworm LTS) kết hợp với **Hệ thống Cấu hình Động theo Phiên bản (`sysctl.d`)**:

- `core/includes.chroot/etc/sysctl.d/90-thmd-guru-base.conf`: Bảo vệ symlink/hardlink, ASLR mức 2 (`randomize_va_space=2`), chống ICMP broadcast & IP redirect.
- `core/kernel/sysctl/91-desktop.conf`: Tối ưu hóa độ trễ thấp, `inotify` lớn (1.048.576 watches) cho VS Code/IDE, ưu tiên nén RAM `zram`.
- `core/kernel/sysctl/91-server.conf`: Kích hoạt thuật toán chống tắc nghẽn **TCP BBR + fq**, mở rộng `somaxconn` (32768), `file-max` (4M), bật IP Forwarding cho Container/Kubernetes.
- `core/kernel/sysctl/91-attt.conf`: Gia cố nhân theo chuẩn **KSPP / CIS Benchmark** (`kptr_restrict=2`, `dmesg_restrict=1`, `yama.ptrace_scope=2`, `unprivileged_bpf_disabled=1`, `bpf_jit_harden=2`, `rp_filter=1`).

## 2. Nhánh Biên dịch Nhân Tùy biến (`build-custom-kernel.sh`)
Khi Học viện cần biên dịch nhân riêng mang hậu tố `-thmd-guru` từ mã nguồn `kernel.org`:
```bash
bash core/kernel/build-custom-kernel.sh
```
Script sẽ tải Linux 6.6 LTS, hợp nhất cấu hình phần cứng với `config-fragments/thmd-guru-hardened.config` và đóng gói thành `.deb` để đưa thẳng vào `config/packages.chroot/` của OS Forge.
