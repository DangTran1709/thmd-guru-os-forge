# Tài Liệu Kỹ Thuật: Core OS, Kernel & Bootloader (`chief-os-architect`)

## 1. Các hạng mục đã hoàn thành
- **Định danh Hệ điều hành (`/etc/os-release`, `/usr/lib/os-release`, `/etc/lsb-release`, `/etc/issue`, `/etc/motd`):** Định danh chuẩn `ID=thmd-guru`, `ID_LIKE=debian`, phiên bản `1.0 (Genesis)` với bộ màu ANSI Vàng Hoàng Gia và ASCII Art của **THMD-Guru Global Tech Academy**.
- **Tinh chỉnh Nhân (`core/kernel/`):**
  - `90-thmd-guru-base.conf`: Bảo mật lớp cơ sở dùng chung cho cả 3 bản.
  - `91-desktop.conf`: Độ trễ thấp, `inotify` 1M watches cho IDE, `zram` swappiness.
  - `91-server.conf`: TCP BBR + Fair Queueing, `somaxconn=32768`, `file-max=4M`, IPv4/IPv6 forwarding cho Container.
  - `91-attt.conf`: Hardening theo chuẩn KSPP/CIS (`kptr_restrict=2`, `yama.ptrace_scope=2`, `unprivileged_bpf_disabled=1`, `rp_filter=1`).
  - `build-custom-kernel.sh` & `config-fragments/thmd-guru-hardened.config`: Kịch bản biên dịch nhân Linux 6.6 LTS từ mã nguồn với hậu tố `-thmd-guru`.
- **Bootloader (`core/bootloader/`):** Cấu hình GRUB2 hỗ trợ cả BIOS (`grub-pc`) và UEFI (`grub-efi`) với 4 chế độ khởi động: *Live System*, *Install OS*, *Safe Mode (toram/nomodeset)*, và *Forensic Mode (noautomount/noswap)*.
- **Core Hook (`core/hooks/live/0100-thmd-guru-core.hook.chroot`):** Tự động thiết lập Locale (`en_US.UTF-8`, `vi_VN.UTF-8`), múi giờ `Asia/Ho_Chi_Minh`, giao diện Prompt Bash/Zsh và nạp đúng hồ sơ `sysctl` theo `/etc/thmd-guru/edition`.
