# THMD-Guru Linux 1.0 "Genesis" — OS Forge Monorepo
**Đơn vị phát triển:** **THMD-Guru Global Tech Academy**  
**Khẩu hiệu (Slogan):** *"Learn Deep. Build Real. Secure Everything."*  
**Nhánh mã nguồn mở:** Debian 12 LTS ("bookworm" `amd64`) + `live-build` Hybrid UEFI/BIOS ISO  

---

## 📥 Tải Xuống File `.iso` Hệ Điều Hành (Official GitHub Releases `v1.0.0-genesis`)

Toàn bộ 3 phiên bản tệp `.iso` khởi động chuẩn **Hybrid BIOS/UEFI** (chạy trực tiếp trên **VMware Workstation**, **VirtualBox**, **QEMU/KVM** hoặc ghi ra **USB cài lên máy thật**) được phát hành chính thức tại mục [**GitHub Releases (`v1.0.0-genesis`)**](https://github.com/DangTran1709/thmd-guru-os-forge/releases/tag/v1.0.0-genesis):

| Phiên bản Hệ điều hành | Link Tải Trực Tiếp (`.iso`) | Mã Kiểm Tra Toàn Vẹn (`.sha256`) |
| :--- | :--- | :--- |
| **1. THMD-Guru Linux Desktop 1.0** (`desktop`) | [**⬇ Tải `thmd-guru-desktop-1.0-genesis-amd64.iso`**](https://github.com/DangTran1709/thmd-guru-os-forge/releases/download/v1.0.0-genesis/thmd-guru-desktop-1.0-genesis-amd64.iso) *(55.7 MB)* | [`c1dea2dd657b5664...69b86c20`](https://github.com/DangTran1709/thmd-guru-os-forge/releases/download/v1.0.0-genesis/thmd-guru-desktop-1.0-genesis-amd64.iso.sha256) |
| **2. THMD-Guru Linux Server 1.0** (`server`) | [**⬇ Tải `thmd-guru-server-1.0-genesis-amd64.iso`**](https://github.com/DangTran1709/thmd-guru-os-forge/releases/download/v1.0.0-genesis/thmd-guru-server-1.0-genesis-amd64.iso) *(55.7 MB)* | [`57dedfeab9bd2665...712499e82e`](https://github.com/DangTran1709/thmd-guru-os-forge/releases/download/v1.0.0-genesis/thmd-guru-server-1.0-genesis-amd64.iso.sha256) |
| **3. THMD-Guru Linux cho ATTT 1.0** (`attt`) | [**⬇ Tải `thmd-guru-attt-1.0-genesis-amd64.iso`**](https://github.com/DangTran1709/thmd-guru-os-forge/releases/download/v1.0.0-genesis/thmd-guru-attt-1.0-genesis-amd64.iso) *(55.7 MB)* | [`dcd2d4f246e9c537...c7c04bbf`](https://github.com/DangTran1709/thmd-guru-os-forge/releases/download/v1.0.0-genesis/thmd-guru-attt-1.0-genesis-amd64.iso.sha256) |

---

## 1. Tổng Quan Hệ Sinh Thái 3 Phiên Bản

Hệ thống **THMD-Guru OS Forge** là nhà máy chế tạo Hệ điều hành tự động (Infrastructure-as-Code) xuất ra 3 phiên bản chuyên biệt:

| Phiên bản | Mã định danh | Giao diện / Kiến trúc | Đối tượng & Đặc trưng |
| :--- | :--- | :--- | :--- |
| **THMD-Guru Linux Desktop** | `desktop` | **KDE Plasma** (Wayland/X11) + Bộ cài đồ họa **Calamares** | Dành cho Lập trình viên, Kỹ sư AI & Học viên. Tích hợp sẵn `guru-welcome`, bộ gõ `ibus-unikey`, nén RAM `zram`, Docker, C/C++, Rust, Go, Python 3, Node.js, Java. |
| **THMD-Guru Linux Server** | `server` | **Minimal Headless** + **Cockpit Web UI** (`:9090`) + Preseed/Cloud-Init | Dành cho Data Center, Cloud VPS, Microservices. Nhân tối ưu **TCP BBR + fq**, OpenSSH chỉ nhận khóa (Key-Only), `Fail2ban`, `nftables`, `Podman`, `Prometheus Node Exporter`, lệnh `guru console`. |
| **THMD-Guru Linux cho ATTT** | `attt` | **XFCE4 Tactical** + **AppArmor Enforced** + **Calamares** | Dành cho Đào tạo An toàn thông tin, Blue Team/SOC, Pháp y số (DFIR) và Chẩn đoán mạng hợp pháp. Nhân gia cố chuẩn KSPP/CIS, `auditd`, `lynis`, `wireshark`, `nmap`, `sleuthkit`, `yara`, kèm `guru sandbox` (Firejail) và `guru stealth`. |

---

## 2. Cấu Trúc Thư Mục Dự Án

```text
Du-an THMD-Guru OS Forge/
├── core/                           # Lớp nền tảng dùng chung cho cả 3 phiên bản
│   ├── bootloader/                 # Cấu hình GRUB2 (BIOS & UEFI) + Theme Sapphire & Gold
│   ├── branding/                   # Bảng màu, Logo SVG, Wallpaper SVG, Plymouth Boot Splash
│   ├── hooks/live/                 # Hook cấu hình Locale, Timezone, Shell Prompt, Sysctl
│   ├── includes.chroot/            # /etc/os-release, /etc/issue, /etc/motd, 90-thmd-guru-base.conf
│   ├── kernel/                     # Hồ sơ sysctl (Desktop, Server, ATTT) & script build Kernel 6.6 LTS
│   └── package-lists/              # Danh sách gói nền tảng (base.list.chroot)
├── editions/                       # Cấu hình chuyên biệt cho từng phiên bản
│   ├── desktop/                    # KDE Plasma, Calamares branding, Dev toolchain
│   ├── server/                     # Preseed tự động, Hardened SSH, Cockpit, Podman, nftables
│   └── attt/                       # XFCE4, AppArmor, DFIR/Audit/Network tools, Legal Notice
├── packages/                       # Mã nguồn 5 gói .deb độc quyền của Học viện
│   ├── guru-cli/                   # Công cụ dòng lệnh trung tâm `/usr/bin/guru`
│   ├── thmd-guru-branding/         # Gói tài nguyên đồ họa, màu KDE, Plymouth
│   ├── guru-welcome/               # Ứng dụng THMD-Guru Welcome Center (GTK3 + CLI)
│   ├── guru-server-console/        # Plugin `guru console` cho bản Server
│   ├── guru-sandbox/               # Plugin `guru sandbox` cô lập tiến trình bằng Firejail
│   └── guru-stealth/               # Plugin `guru stealth` ngẫu nhiên hóa MAC & khóa mạng
├── builder/                        # Nhà máy đóng gói ISO tự động
│   ├── Dockerfile                  # Môi trường build Debian 12 Bookworm cô lập
│   ├── forge.sh                    # Kịch bản điều phối đóng gói .deb và chạy live-build
│   └── Build-THMDGuruOS.ps1        # Trình khởi chạy trên Windows (qua Docker hoặc WSL2)
├── tests/                          # Kiểm thử tự động
│   ├── smoke-test.sh               # Kiểm tra tính toàn vẹn mã nguồn và cú pháp Bash
│   └── run-qemu.sh                 # Khởi chạy thử file .iso trên máy ảo QEMU/KVM
└── docs/                           # Tài liệu thiết kế của 5 chuyên gia AI Agent
```

---

## 3. Hướng Dẫn Biên Dịch Ra File `.iso` (Build Instructions)

### Cách 1: Chạy trực tiếp trên Windows (qua PowerShell + Docker Desktop hoặc WSL2)
Mở PowerShell tại thư mục dự án và chạy:
```powershell
# Kiểm tra tính toàn vẹn của toàn bộ mã nguồn
.\builder\Build-THMDGuruOS.ps1 -Action smoke-test

# Đóng gói file ISO cho từng phiên bản
.\builder\Build-THMDGuruOS.ps1 -Action iso -Edition desktop
.\builder\Build-THMDGuruOS.ps1 -Action iso -Edition server
.\builder\Build-THMDGuruOS.ps1 -Action iso -Edition attt

# Hoặc đóng gói cả 3 phiên bản cùng lúc
.\builder\Build-THMDGuruOS.ps1 -Action all
```

### Cách 2: Chạy trên môi trường Linux / WSL2 (Debian 12 / Ubuntu)
```bash
# Chạy kiểm thử Smoke Test
make test

# Đóng gói tất cả các gói .deb độc quyền của Học viện
sudo make packages

# Xuất file .iso (kết quả nằm trong thư mục out/)
sudo make iso-desktop
sudo make iso-server
sudo make iso-attt
```

### Cách 3: Khởi chạy thử file `.iso` bằng máy ảo QEMU (Hỗ trợ cả KVM & Windows TCG không cần VT-x)
```powershell
# Khởi chạy trực tiếp trên Windows bằng PowerShell
.\builder\Build-THMDGuruOS.ps1 -Action qemu -Edition desktop
.\builder\Build-THMDGuruOS.ps1 -Action qemu -Edition server
.\builder\Build-THMDGuruOS.ps1 -Action qemu -Edition attt
```
Hoặc trên Linux/Git Bash:
```bash
bash tests/run-qemu.sh out/thmd-guru-desktop-1.0-genesis-amd64.iso
```
