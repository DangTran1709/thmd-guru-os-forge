# 📋 Nhật Ký Bản Vá & Phiên Bản Phát Hành (Official Patch & Release Changelog)

**Dự án:** **THMD-Guru Linux 1.0 "Genesis" (OS Forge)**  
**Cơ chế quản lý bản vá tự động:** **THMD-Guru PatchWatch AI-Agent (`THMD-guru-ai patch-agent`)**  
**Kho phát hành chính thức:** [GitHub Releases — `DangTran1709/thmd-guru-os-forge`](https://github.com/DangTran1709/thmd-guru-os-forge/releases)

> Tài liệu này được cập nhật tự động bởi công cụ **AI-Agent (`builder/patch_agent.py` / `THMD-guru-ai patch-agent`)** mỗi khi phát hiện bản vá bảo mật mới từ nhánh thượng nguồn **Debian 12 ("Bookworm" `Kernel 6.1 LTS`)**, bản vá công cụ phòng Lab (**OWASP ZAP / AI-RAG**) hoặc bản sửa lỗi hệ thống trong kho mã nguồn.

---

## 🚀 Phiên bản [`v1.1.1-genesis`](https://github.com/DangTran1709/thmd-guru-os-forge/releases/tag/v1.1.1-genesis) — *Ngày phát hành: 09/11/2026*
- **Mức độ quan trọng (Severity):** `HIGH` *(Bản cập nhật đã kiểm증 bởi THMD-Guru PatchWatch AI-Agent (Hybrid Rule + LLM Advisory Synthesizer))*
- **Nhánh nhân (Kernel Branch):** `Linux 6.1 LTS / SLTS (Debian 12.15 Bookworm amd64)`
- **Tóm tắt bản vá:** **Nâng cấp Giao diện Đồ họa Cyber Sapphire & Royal Gold (Bootloader HD, Bảng điều khiển TUI guru-cockpit & Kho Modular Hub)**

### 🛠 Chi Tiết Các Hạng Mục Được Vá & Nâng Cấp Trong `v1.1.1-genesis`
- [VMWARE LAB & NCKH] Release(v1.1.0-genesis): Kiến trúc Mô-đun Hóa (Lean Core OS + On-Demand Modular Hub cho Apps, Tools, LAB & NCKH) [THMD-Guru PatchWatch AI-Agent]
- [KERNEL & BOOTLOADER] Release(v1.0.1-genesis): Bản vá Khởi động VMware Workstation (BIOS/UEFI), Trình cài đặt thmd-installer Mặc định & Tích hợp AI PatchWatch Agent [THMD-Guru PatchWatch AI-Agent]
- [KERNEL & BOOTLOADER] Set Install & VMware Lab Wizard as default top menu item (#1) across BIOS and UEFI for all 3 ISOs
- [KERNEL & BOOTLOADER] Fix VMware/UEFI/BIOS boot hang across all 3 editions (devtmpfs/udev, RRIP_1991A, thmd-installer wizard, VMnet2 static IP)
- [VMWARE LAB & NCKH] Add complete A-to-Z VMware installation & NCKH lab configuration .docx manual with visual step-by-step diagrams


### 🔐 Bảng Mã Băm Kiểm Tra Toàn Vẹn (`SHA-256`) — `v1.1.1-genesis`

| Phiên bản | Tên tệp `.ISO` | Dung lượng | Mã Băm `SHA-256` |
| :--- | :--- | :--- | :--- |
| **ATTT (`VM1`)** | `thmd-guru-attt-1.0-genesis-amd64.iso` | `58,494,976 bytes` | `8afe53892bd0c97881c83a59630e18af42f79ed46a810f5e6e5f4315406c2ad5` |
| **Server (`VM2`)** | `thmd-guru-server-1.0-genesis-amd64.iso` | `58,480,640 bytes` | `d46582c42d16b5ff7f2c39651f596e2153f661c9b8006ff6fbe253eee0c4fecb` |
| **Desktop (`VM3`)** | `thmd-guru-desktop-1.0-genesis-amd64.iso` | `58,468,352 bytes` | `3f33b90e494cd2c5292b3a3414bdc3c73fa660dd071505975222d38abdbac28b` |

---

## 🚀 Phiên bản [`v1.1.0-genesis`](https://github.com/DangTran1709/thmd-guru-os-forge/releases/tag/v1.1.0-genesis) — *Ngày phát hành: 09/11/2026*
- **Mức độ quan trọng (Severity):** `HIGH` *(Bản cập nhật đã kiểm증 bởi THMD-Guru PatchWatch AI-Agent (Hybrid Rule + LLM Advisory Synthesizer))*
- **Nhánh nhân (Kernel Branch):** `Linux 6.1 LTS / SLTS (Debian 12.15 Bookworm amd64)`
- **Tóm tắt bản vá:** **Kiến trúc Mô-đun Hóa (Lean Core OS + On-Demand Modular Hub cho Apps, Tools, LAB & NCKH)**

### 🛠 Chi Tiết Các Hạng Mục Được Vá & Nâng Cấp Trong `v1.1.0-genesis`
- [KIẾN TRÚC LEAN CORE OS] Tách biệt hoàn toàn Hệ điều hành Lõi (initrd.gz thuần khiết) khỏi các ứng dụng, bộ công cụ (Tools), Phòng thí nghiệm (LAB) và Đề tài NCKH.
- [MODULAR HUB CLI & TUI] Ra mắt trung tâm cài đặt mô-đun theo yêu cầu 'THMD-guru-ai hub' (list | install | remove | status | menu) hỗ trợ 12 gói độc lập.
- [DUAL-SOURCE ON-DEMAND] Hỗ trợ cài đặt mô-đun tức thì cả khi Online (tải từ GitHub Releases) lẫn khi Offline trên mạng cô lập VMnet2 (tự động giải nén từ /pool/modules/*.tar.gz trên đĩa ISO mà không tốn RAM khi khởi động).
- [PHÂN TÁCH VAI TRÒ NCKH] Hỗ trợ cờ --role (vm1-zap, vm2-target, vm3-airag, evaluator) để mỗi máy ảo chỉ cài đặt đúng thành phần của máy đó.


### 🔐 Bảng Mã Băm Kiểm Tra Toàn Vẹn (`SHA-256`) — `v1.1.0-genesis`

| Phiên bản | Tên tệp `.ISO` | Dung lượng | Mã Băm `SHA-256` |
| :--- | :--- | :--- | :--- |
| **ATTT (`VM1`)** | `thmd-guru-attt-1.0-genesis-amd64.iso` | `58,478,592 bytes` | `73fa1bdea3a6d59bce7fa8b4346bd29f835f75c5820f21763af48c08f8e27663` |
| **Server (`VM2`)** | `thmd-guru-server-1.0-genesis-amd64.iso` | `58,460,160 bytes` | `f623cdd7d013ace598d5bf3c9703be0ab85ce0b6f31b11f83a03eba7d32de520` |
| **Desktop (`VM3`)** | `thmd-guru-desktop-1.0-genesis-amd64.iso` | `58,451,968 bytes` | `3bf0d742816cffc09381ae79f641698e8c1424f9798e072cc2d51431c7730f52` |

---

## 🚀 Phiên bản [`v1.0.1-genesis`](https://github.com/DangTran1709/thmd-guru-os-forge/releases/tag/v1.0.1-genesis) — *Ngày phát hành: 07/11/2026*
- **Mức độ quan trọng (Severity):** `HIGH` *(Bản cập nhật đã kiểm증 bởi THMD-Guru PatchWatch AI-Agent (Hybrid Rule + LLM Advisory Synthesizer))*
- **Nhánh nhân (Kernel Branch):** `Linux 6.1 LTS / SLTS (Debian 12.15 Bookworm amd64)`
- **Tóm tắt bản vá:** **Bản vá Khởi động VMware Workstation (BIOS/UEFI), Trình cài đặt thmd-installer Mặc định & Tích hợp AI PatchWatch Agent**

### 🛠 Chi Tiết Các Hạng Mục Được Vá & Nâng Cấp Trong `v1.0.1-genesis`
- [KERNEL & BOOTLOADER] Đặt mục '1. Install & VMware Lab Wizard' làm mặc định (default #1) trên cả BIOS (ISOLINUX) và UEFI (GRUB2).
- [VMWARE & INITRAMFS] Khắc phục triệt để lỗi treo khung trắng (vga=788 bogl-bterm) và lỗi thiếu /dev/tty0, /dev/tty1 bằng cơ chế tự động khởi tạo devtmpfs + systemd-udevd + nạp driver VMware (e1000, vmxnet3, mptspi, nvme).
- [UEFI ISO-9660] Bổ sung bản ghi mở rộng Rock Ridge RRIP_1991A (ER record) chuẩn hóa khả năng khởi động UEFI GRUB2.
- [VMWARE LAB NCKH] Bổ sung công cụ thmd-installer hỗ trợ gán IP tĩnh 1-chạm (192.168.80.10/.20/.30) trên mạng cô lập VMnet2 không có DHCP.
- [AI-AGENT] Tích hợp công cụ tự động theo dõi bản vá, đánh số phiên bản và phát hành GitHub Release (THMD-guru-ai patch-agent).


### 🔐 Bảng Mã Băm Kiểm Tra Toàn Vẹn (`SHA-256`) — `v1.0.1-genesis`

| Phiên bản | Tên tệp `.ISO` | Dung lượng | Mã Băm `SHA-256` |
| :--- | :--- | :--- | :--- |
| **ATTT (`VM1`)** | `thmd-guru-attt-1.0-genesis-amd64.iso` | `58,451,968 bytes` | `61e884d0352755f96913ca40908fc2fadb9c1cde02e141d4f30b33e020e8f346` |
| **Server (`VM2`)** | `thmd-guru-server-1.0-genesis-amd64.iso` | `58,433,536 bytes` | `92b8c83e9d76ee9bf09f48f624e8e668b7fd9cce6c94d67fb457fe081eee5b49` |
| **Desktop (`VM3`)** | `thmd-guru-desktop-1.0-genesis-amd64.iso` | `58,425,344 bytes` | `d7f6fd3e1faa565282f4b021816594dab1557868df22c0d253fba1ec45212965` |

---

## 🎉 Phiên bản [`v1.0.0-genesis`](https://github.com/DangTran1709/thmd-guru-os-forge/releases/tag/v1.0.0-genesis) — *Ngày phát hành: 03/11/2026*
- **Mức độ quan trọng (Severity):** `INITIAL RELEASE`
- **Tóm tắt:** Phát hành phiên bản đầu tiên của hệ sinh thái **THMD-Guru Linux 1.0 ("Genesis")** gồm 3 phiên bản (`desktop`, `server`, `attt`), công cụ điều hành `THMD-guru-ai`, kho gói `.deb` ký số RSA-4096 và phòng Lab thực nghiệm NCKH (`OWASP ZAP + AI Hybrid RAG + pfSense Firewall`).
