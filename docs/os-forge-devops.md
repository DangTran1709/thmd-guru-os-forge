# Tài Liệu Kỹ Thuật: Nhà Máy Đóng Gói OS Forge & CLI (`os-forge-devops`)

## 1. Công cụ Quản trị Trung tâm `guru-cli` (`packages/guru-cli/`)
- Cài đặt thực thi tại `/usr/bin/guru` kèm trang hướng dẫn `man guru` và gợi ý lệnh `bash-completion`.
- Hỗ trợ các lệnh tích hợp sẵn:
  - `guru info`: Hiển thị biểu tượng ASCII của **THMD-Guru Global Tech Academy** cùng thông tin OS, Kernel, CPU, RAM.
  - `guru status`: Kiểm tra trạng thái dịch vụ cốt lõi, tường lửa và hồ sơ `sysctl`.
  - `guru harden`: Chấm điểm và kiểm toán các thông số bảo mật nhân hệ điều hành.
  - `guru lab`: Khởi tạo và hướng dẫn thực hành các bài Lab của Học viện.
- Kiến trúc Plugin mở rộng tự động qua `/usr/lib/guru/commands/` (`welcome`, `console`, `sandbox`, `stealth`).

## 2. Dây chuyền Đóng gói Tự động (`builder/forge.sh` & `builder/Dockerfile`)
- Tự động biên dịch 5 gói `.deb` độc quyền bằng `dpkg-buildpackage`.
- Hợp nhất lớp nền tảng (`core/`) và lớp chuyên biệt (`editions/<edition>/`) vào cây thư mục `live-build`.
- Tạo ảnh đĩa Hybrid ISO (`live-image-amd64.hybrid.iso`) khởi động được trên cả UEFI và Legacy BIOS, kèm mã băm kiểm tra toàn vẹn `.sha256`.
