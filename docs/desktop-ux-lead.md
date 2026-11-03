# Tài Liệu Kỹ Thuật: THMD-Guru Linux Desktop & Branding (`desktop-ux-lead`)

## 1. Hệ thống Nhận diện Thương hiệu (`core/branding/` & `packages/thmd-guru-branding/`)
- **Bảng màu (`palette.md`):** *Cyber Sapphire* (`#0B3D91`), *Deep Navy* (`#071A3A`), *Royal Gold* (`#D4AF37`), *Light Gold* (`#F5D77A`).
- **Logo & Wallpaper Vector (`thmd-guru-logo.svg`, `wallpaper-sapphire-gold.svg`):** Thiết kế SVG sắc nét ở mọi độ phân giải.
- **Plymouth Boot Theme (`plymouth/thmd-guru/`):** Màn hình khởi động chuyển sắc Sapphire/Navy với chữ Vàng kim.
- **KDE Color Scheme (`ThmdGuruSapphire.colors`):** Đồng bộ toàn bộ cửa sổ KDE Plasma sang tông màu của Học viện.

## 2. Ứng dụng Chào mừng Học viện (`packages/guru-welcome/`)
- Tự động khởi chạy ở lần đăng nhập đầu tiên hoặc qua lệnh `guru welcome`.
- Hỗ trợ cả giao diện đồ họa **GTK3** lẫn chế độ dòng lệnh (`--cli`), cho phép cài đặt nhanh **VS Code**, **Ollama Local AI** và các bộ công cụ học tập của Học viện.

## 3. Phiên bản Desktop (`editions/desktop/`)
- Tích hợp sẵn **KDE Plasma (Wayland/X11)**, âm thanh **PipeWire**, bộ gõ tiếng Việt `ibus-unikey`, bộ cài đồ họa **Calamares** mang thương hiệu `thmd-guru`, nén RAM **ZRAM (`zstd`)**, cùng trọn bộ trình biên dịch (`C/C++`, `Rust`, `Go`, `Python 3`, `Node.js`, `Java`, `Docker`).
