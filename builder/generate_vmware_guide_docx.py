#!/usr/bin/env python3
"""
THMD-Guru Linux 1.0 "Genesis" — VMware Workstation A-to-Z Installation & Configuration Guide (.docx)
Generates:
  1. 3 High-Resolution (1600x1000) VMware Visual Guide Mockups:
     - docs/ui-mockups/vmware_guide_1_virtual_network_editor.png
     - docs/ui-mockups/vmware_guide_2_new_vm_wizard.png
     - docs/ui-mockups/vmware_guide_3_end_to_end_commands.png
  2. Complete A-to-Z Microsoft Word (.docx) Manual with 10 embedded visual figures & step-by-step tables:
     - HUONG-DAN-CAI-DAT-VA-CAU-HINH-TREN-VMWARE-TU-A-DEN-Z.docx
     - docs/HUONG-DAN-CAI-DAT-VA-CAU-HINH-TREN-VMWARE-TU-A-DEN-Z.docx
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
from docx.shared import Inches, Pt, RGBColor

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

W, H = 1600, 1000

# THMD-Guru Design System 2.0 Palette
BG_INK = (10, 15, 30)
BG_NAVY = (12, 24, 48)
BG_CARD = (17, 34, 68)
BG_CARD_ALT = (22, 43, 84)
BORDER_SUBTLE = (35, 65, 120)
SAPPHIRE_OLD = (11, 61, 145)
SAPPHIRE_TEXT = (96, 165, 250)
GOLD_ROYAL = (212, 175, 55)
GOLD_BRIGHT = (245, 215, 122)
TEXT_PRIMARY = (230, 236, 247)
TEXT_MUTED = (148, 163, 184)
GREEN_OK = (16, 185, 129)
AMBER_WARN = (245, 158, 11)
RED_DANGER = (239, 68, 68)
CYAN_ACCENT = (56, 189, 248)
PURPLE_AI = (192, 132, 252)


def load_fonts():
    win_fonts = Path(r"C:\Windows\Fonts")
    try:
        return {
            "h1": ImageFont.truetype(str(win_fonts / "segoeuib.ttf"), 28),
            "h2": ImageFont.truetype(str(win_fonts / "segoeuib.ttf"), 21),
            "h3": ImageFont.truetype(str(win_fonts / "segoeuib.ttf"), 17),
            "body": ImageFont.truetype(str(win_fonts / "segoeui.ttf"), 15),
            "body_b": ImageFont.truetype(str(win_fonts / "segoeuib.ttf"), 15),
            "small": ImageFont.truetype(str(win_fonts / "segoeui.ttf"), 13),
            "small_b": ImageFont.truetype(str(win_fonts / "segoeuib.ttf"), 13),
            "mono": ImageFont.truetype(str(win_fonts / "consola.ttf"), 14),
            "mono_b": ImageFont.truetype(str(win_fonts / "consolab.ttf"), 14),
            "mono_sm": ImageFont.truetype(str(win_fonts / "consola.ttf"), 12),
        }
    except Exception:
        default = ImageFont.load_default()
        return {k: default for k in ["h1", "h2", "h3", "body", "body_b", "small", "small_b", "mono", "mono_b", "mono_sm"]}


def draw_rounded_card(draw: ImageDraw.ImageDraw, box, fill, outline=BORDER_SUBTLE, width=1, radius=10):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def draw_badge(draw: ImageDraw.ImageDraw, x, y, text, bg_col, fg_col, font, pad_x=10, pad_y=4):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.rounded_rectangle((x, y, x + tw + pad_x * 2, y + th + pad_y * 2 + 2), radius=6, fill=bg_col)
    draw.text((x + pad_x, y + pad_y - 1), text, fill=fg_col, font=font)
    return tw + pad_x * 2


def render_vmware_guide_1_network_editor(fonts, out_paths: list[Path]):
    """Visual Guide 1: VMware Virtual Network Editor Configuration (VMnet8 NAT + VMnet2 Host-Only 192.168.80.0/24)."""
    img = Image.new("RGB", (W, H), BG_INK)
    d = ImageDraw.Draw(img)

    # Top Header
    d.rectangle((0, 0, W, 64), fill=BG_NAVY)
    d.line((0, 64, W, 64), fill=GOLD_ROYAL, width=2)
    d.text((28, 18), "HƯỚNG DẪN BƯỚC 1: CẤU HÌNH MẠNG ẢO TRONG VMWARE VIRTUAL NETWORK EDITOR (VMNET2 & VMNET8)", fill=GOLD_BRIGHT, font=fonts["h2"])
    draw_badge(d, W - 290, 18, "VMWARE NETWORK SETUP", CYAN_ACCENT, BG_INK, fonts["small_b"])

    # Window Frame simulating VMware Virtual Network Editor
    draw_rounded_card(d, (60, 88, 1540, 952), fill=BG_NAVY, outline=GOLD_ROYAL, width=2, radius=14)
    d.rounded_rectangle((60, 88, 1540, 138), radius=14, fill=SAPPHIRE_OLD)
    d.rectangle((60, 118, 1540, 138), fill=SAPPHIRE_OLD)
    d.text((88, 102), "► VMware Workstation Pro — Edit -> Virtual Network Editor (Đã bấm nút 'Change Settings' quyền Administrator)", fill=GOLD_BRIGHT, font=fonts["h3"])

    # Upper Table of Virtual Networks
    draw_rounded_card(d, (92, 160, 1508, 360), fill=BG_INK, outline=BORDER_SUBTLE, width=2, radius=10)
    d.rectangle((92, 160, 1508, 200), fill=BG_CARD)
    d.text((116, 170), "Name        Type          External Connection          Host Connection     DHCP       Subnet Address        Subnet Mask", fill=GOLD_BRIGHT, font=fonts["mono_b"])

    net_rows = [
        ("VMnet0      Bridged       Auto-bridging                -                   -          -                     -", False, TEXT_MUTED),
        ("VMnet1      Host-only     -                            Connected           Enabled    192.168.100.0         255.255.255.0", False, TEXT_MUTED),
        ("VMnet2  ◄   Host-only     - (MẠNG LAB NCKH CHÍNH)      Connected (.80.254) DISABLED   192.168.80.0          255.255.255.0", True, GREEN_OK),
        ("VMnet8      NAT           NAT (Cấp Internet cho WAN)   Connected           Enabled    192.168.220.0         255.255.255.0", False, CYAN_ACCENT),
    ]
    ry = 212
    for rtxt, sel, col in net_rows:
        if sel:
            draw_rounded_card(d, (104, ry - 4, 1496, ry + 30), fill=BG_CARD_ALT, outline=GOLD_ROYAL, width=2, radius=6)
        d.text((116, ry), rtxt, fill=col, font=fonts["mono_b"] if sel else fonts["mono"])
        ry += 36

    # Lower Configuration Panel for Selected VMnet2
    draw_rounded_card(d, (92, 382, 980, 740), fill=BG_CARD, outline=GOLD_ROYAL, width=2, radius=12)
    d.text((118, 400), "THÔNG SỐ CẤU HÌNH CHI TIẾT CHO MẠNG [VMnet2] (CHỌN ĐÚNG 4 MỤC SAU):", fill=GOLD_BRIGHT, font=fonts["body_b"])

    cfg_steps = [
        ("[1] VMnet Information — Chọn kiểu mạng:", "(●) Host-only (connect VMs internally in a private network)", GREEN_OK),
        ("[2] Host Virtual Adapter — Kết nối máy Host:", "[x] Connect a host virtual adapter to this network (Đặt IP tĩnh .80.254 trên Windows)", CYAN_ACCENT),
        ("[3] Local DHCP Service — Tắt DHCP của VMware:", "[ ] Use local DHCP service to distribute IP address to VMs (BỎ TÍCH Ô NÀY!)", RED_DANGER),
        ("[4] Subnet IP & Subnet Mask — Nhập dải mạng LAB:", "Subnet IP: [ 192.168.80.0 ]     Subnet Mask: [ 255.255.255.0 ]", GOLD_BRIGHT),
    ]
    cy = 442
    for ctitle, cval, ccol in cfg_steps:
        draw_rounded_card(d, (118, cy, 954, cy + 62), fill=BG_INK, outline=BORDER_SUBTLE, width=1, radius=8)
        d.text((136, cy + 8), ctitle, fill=TEXT_PRIMARY, font=fonts["body_b"])
        d.text((136, cy + 34), cval, fill=ccol, font=fonts["mono_b"])
        cy += 72

    # Right Callout Box: Host Adapter IP Warning (Avoiding 192.168.80.1 conflict with pfSense)
    draw_rounded_card(d, (1004, 382, 1508, 740), fill=(18, 30, 56), outline=CYAN_ACCENT, width=2, radius=12)
    d.text((1028, 400), "LƯU Ý QUAN TRỌNG TRÊN WINDOWS HOST:", fill=CYAN_ACCENT, font=fonts["body_b"])
    d.text((1028, 430), "Tránh đụng độ IP 192.168.80.1 với pfSense!", fill=GOLD_BRIGHT, font=fonts["body_b"])

    notes = [
        "Mặc định trên Windows, card mạng ảo",
        "'VMware Network Adapter VMnet2' sẽ tự lấy",
        "địa chỉ IP 192.168.80.1 — trùng với địa chỉ",
        "LAN của tường lửa pfSense (192.168.80.1)!",
        "",
        "► Cách xử lý trong 15 giây trên Windows:",
        "1. Bấm Win + R -> gõ: ncpa.cpl -> Enter",
        "2. Nhấp đúp 'VMware Network Adapter VMnet2'",
        "3. Chọn Internet Protocol Version 4 (TCP/IPv4)",
        "4. Đặt IP tĩnh cho máy thật Windows là:",
        "   • IP address  : 192.168.80.254",
        "   • Subnet mask : 255.255.255.0",
        "   • Default GW  : (Để trống)",
    ]
    ny = 466
    for nline in notes:
        d.text((1028, ny), nline, fill=GREEN_OK if nline.startswith("   •") else TEXT_PRIMARY, font=fonts["mono_sm"] if nline.startswith("   •") else fonts["small"])
        ny += 20

    # Bottom Summary of IP Allocation Table across VMnet2
    draw_rounded_card(d, (92, 760, 1508, 926), fill=BG_INK, outline=GREEN_OK, width=2, radius=10)
    d.text((118, 774), "SƠ ĐỒ QUY HOẠCH ĐỊA CHỈ IP TĨNH TRÊN MẠNG LAB VMNET2 (192.168.80.0/24):", fill=GREEN_OK, font=fonts["body_b"])

    ip_boxes = [
        ("pfSense Firewall", "192.168.80.1 / 24", "WAN: VMnet8 | LAN: VMnet2", AMBER_WARN),
        ("VM1: ATTT / ZAP", "192.168.80.10 / 24", "GW: .80.1 | Quét Web & Đẩy Alert", CYAN_ACCENT),
        ("VM2: Web Target", "192.168.80.20 / 24", "GW: .80.1 | Nginx, DVWA, JuiceShop", GREEN_OK),
        ("VM3: AI-RAG Server", "192.168.80.30 / 24", "GW: .80.1 | FastAPI :8000, Qdrant", GOLD_ROYAL),
        ("Windows Host PC", "192.168.80.254 / 24", "Mở trình duyệt xem Dashboard :8000", PURPLE_AI),
    ]
    bx = 118
    for btitle, bip, bsub, bcol in ip_boxes:
        draw_rounded_card(d, (bx, 808, bx + 262, 908), fill=BG_CARD, outline=bcol, width=2, radius=8)
        d.text((bx + 14, 818), btitle, fill=bcol, font=fonts["body_b"])
        d.text((bx + 14, 846), bip, fill=TEXT_PRIMARY, font=fonts["mono_b"])
        d.text((bx + 14, 874), bsub, fill=TEXT_MUTED, font=fonts["small"])
        bx += 276

    for p in out_paths:
        p.parent.mkdir(parents=True, exist_ok=True)
        img.save(p, "PNG")


def render_vmware_guide_2_new_vm_wizard(fonts, out_paths: list[Path]):
    """Visual Guide 2: VMware New Virtual Machine Wizard & Hardware Allocation Matrix."""
    img = Image.new("RGB", (W, H), BG_INK)
    d = ImageDraw.Draw(img)

    # Top Header
    d.rectangle((0, 0, W, 64), fill=BG_NAVY)
    d.line((0, 64, W, 64), fill=GOLD_ROYAL, width=2)
    d.text((28, 18), "HƯỚNG DẪN BƯỚC 2: TẠO MÁY ẢO MỚI (NEW VIRTUAL MACHINE WIZARD) & GẮN FILE .ISO", fill=GOLD_BRIGHT, font=fonts["h2"])
    draw_badge(d, W - 290, 18, "VMWARE VM CREATION", GOLD_ROYAL, BG_INK, fonts["small_b"])

    # Left Column: 6-Step Wizard Walkthrough
    draw_rounded_card(d, (48, 88, 780, 952), fill=BG_NAVY, outline=GOLD_ROYAL, width=2, radius=14)
    d.rounded_rectangle((48, 88, 780, 138), radius=14, fill=SAPPHIRE_OLD)
    d.rectangle((48, 118, 780, 138), fill=SAPPHIRE_OLD)
    d.text((74, 102), "► 6 Bước Tạo Máy Ảo Chuẩn Trong VMware (Ctrl + N)", fill=GOLD_BRIGHT, font=fonts["h3"])

    wiz_steps = [
        ("Bước 1: Chọn kiểu cấu hình (Welcome Wizard)", "• Chọn (●) Typical (recommended) hoặc Custom -> Bấm Next.", CYAN_ACCENT),
        ("Bước 2: Chọn đĩa cài đặt ISO (Guest OS Installation)", "• Chọn (●) Installer disc image file (iso):\n• Bấm Browse... -> Trỏ tới file thmd-guru-<edition>-1.0-genesis-amd64.iso", GREEN_OK),
        ("Bước 3: Chọn loại Hệ điều hành (Select a Guest OS)", "• Guest operating system: (●) Linux\n• Version: Chọn [ Debian 12.x 64-bit ] (Với pfSense chọn FreeBSD 14 64-bit)", GOLD_BRIGHT),
        ("Bước 4: Đặt tên & Thư mục lưu VM (Name the VM)", "• Virtual machine name: Đặt rõ tên (VD: VM1-THMD-Guru-ATTT-ZAP)\n• Location: Nên lưu trên ổ cứng SSD/NVMe còn trống tối thiểu 60GB.", TEXT_PRIMARY),
        ("Bước 5: Dung lượng ổ cứng (Specify Disk Capacity)", "• Maximum disk size: 40 GB (VM1, VM2) hoặc 60 GB (VM3 AI-RAG)\n• Chọn (●) Split virtual disk into multiple files -> Bấm Customize Hardware...", SAPPHIRE_TEXT),
        ("Bước 6: Tùy chỉnh Phần cứng (Customize Hardware)", "• Memory (RAM) & Processors (vCPU): Đặt đúng theo bảng bên phải.\n• Network Adapter: Chọn (●) Custom: Specific virtual network -> [ VMnet2 ]", PURPLE_AI),
    ]
    wy = 158
    for wtitle, wdesc, wcol in wiz_steps:
        draw_rounded_card(d, (72, wy, 756, wy + 116), fill=BG_CARD, outline=wcol, width=1, radius=10)
        d.text((92, wy + 12), wtitle, fill=wcol, font=fonts["body_b"])
        ly = wy + 42
        for ln in wdesc.split("\n"):
            d.text((92, ly), ln, fill=TEXT_PRIMARY, font=fonts["small"])
            ly += 26
        wy += 128

    # Right Column: Hardware Profile Cards for Each VM in the Lab
    draw_rounded_card(d, (804, 88, 1552, 952), fill=BG_NAVY, outline=CYAN_ACCENT, width=2, radius=14)
    d.rounded_rectangle((804, 88, 1552, 138), radius=14, fill=SAPPHIRE_OLD)
    d.rectangle((804, 118, 1552, 138), fill=SAPPHIRE_OLD)
    d.text((830, 102), "► Bảng Thông Số Phần Cứng & File ISO Cho Từng Máy Ảo", fill=GOLD_BRIGHT, font=fonts["h3"])

    vm_cards = [
        (
            "1. Máy ảo VM1 — Máy Quét Bảo Mật Web (OWASP ZAP)",
            "File ISO: thmd-guru-attt-1.0-genesis-amd64.iso (Hoặc Kali Linux)",
            "• Guest OS : Linux -> Debian 12.x 64-bit\n• Bộ xử lý : 2 Processors (2 vCPU)  |  Bộ nhớ RAM : 3072 MB (3 GB)\n• Ổ cứng   : 40 GB NVMe/SCSI        |  Card mạng  : Custom -> VMnet2\n• Địa chỉ  : 192.168.80.10/24 (Gateway: 192.168.80.1)",
            CYAN_ACCENT,
        ),
        (
            "2. Máy ảo VM2 — Máy Chủ Web Mục Tiêu (Target Server)",
            "File ISO: thmd-guru-server-1.0-genesis-amd64.iso (Hoặc Ubuntu Server)",
            "• Guest OS : Linux -> Debian 12.x 64-bit\n• Bộ xử lý : 2 Processors (2 vCPU)  |  Bộ nhớ RAM : 4096 MB (4 GB)\n• Ổ cứng   : 40 GB NVMe/SCSI        |  Card mạng  : Custom -> VMnet2\n• Địa chỉ  : 192.168.80.20/24 (Chạy Nginx, Juice Shop, DVWA, WebGoat)",
            GREEN_OK,
        ),
        (
            "3. Máy ảo VM3 — Máy Chủ Phân Tích AI-RAG (AI-RAG Server)",
            "File ISO: thmd-guru-desktop-1.0-genesis-amd64.iso (Hoặc Ubuntu)",
            "• Guest OS : Linux -> Debian 12.x 64-bit (Bật Virtualize IOMMU nếu cần)\n• Bộ xử lý : 3 Processors (3 vCPU)  |  Bộ nhớ RAM : 4096 MB (4 GB - 6 GB)\n• Ổ cứng   : 60 GB NVMe/SCSI        |  Card mạng  : Custom -> VMnet2\n• Địa chỉ  : 192.168.80.30/24 (Chạy FastAPI :8000, Qdrant :6333, Ollama)",
            GOLD_ROYAL,
        ),
        (
            "4. Máy ảo pfSense Firewall (Gateway Biên — Tùy chọn)",
            "File ISO: pfSense-CE-2.7.2-RELEASE-amd64.iso",
            "• Guest OS : Other -> FreeBSD 14 64-bit\n• Bộ xử lý : 1 Processor (1 vCPU)   |  Bộ nhớ RAM : 1024 MB (1 GB)\n• Ổ cứng   : 16 GB SCSI             |  2 Card mạng: NIC1=VMnet8, NIC2=VMnet2\n• Địa chỉ  : WAN = DHCP (VMnet8)    |  LAN = 192.168.80.1/24 (VMnet2)",
            AMBER_WARN,
        ),
    ]
    vy = 158
    for vtitle, viso, vspec, vcol in vm_cards:
        draw_rounded_card(d, (828, vy, 1528, vy + 182), fill=BG_INK, outline=vcol, width=2, radius=10)
        d.text((848, vy + 12), vtitle, fill=vcol, font=fonts["body_b"])
        d.text((848, vy + 38), viso, fill=GOLD_BRIGHT, font=fonts["mono_b"])
        sy = vy + 68
        for sln in vspec.split("\n"):
            d.text((848, sy), sln, fill=TEXT_PRIMARY, font=fonts["small"])
            sy += 24
        vy += 196

    for p in out_paths:
        p.parent.mkdir(parents=True, exist_ok=True)
        img.save(p, "PNG")


def render_vmware_guide_3_commands(fonts, out_paths: list[Path]):
    """Visual Guide 3: End-to-End Command Execution & Verification Cheat Sheet across VM1, VM2, VM3 & Host."""
    img = Image.new("RGB", (W, H), BG_INK)
    d = ImageDraw.Draw(img)

    # Top Header
    d.rectangle((0, 0, W, 64), fill=BG_NAVY)
    d.line((0, 64, W, 64), fill=GOLD_ROYAL, width=2)
    d.text((28, 18), "HƯỚNG DẪN BƯỚC 3: BẢNG LỆNH TRIỂN KHAI & VẬN HÀNH THỰC NGHIỆM TỪ A–Z TRÊN 3 MÁY ẢO", fill=GOLD_BRIGHT, font=fonts["h2"])
    draw_badge(d, W - 290, 18, "COMMAND CHEAT SHEET", GREEN_OK, BG_INK, fonts["small_b"])

    # 4 Quadrants for VM2 -> VM3 -> VM1 -> Evaluator
    boxes = [
        (
            (48, 88, 784, 504),
            "TRÊN MÁY ẢO VM2 (192.168.80.20 — WEB SERVER TARGET)",
            GREEN_OK,
            [
                ("# 1. Đặt IP tĩnh 192.168.80.20/24 và khai báo vai trò VM2:", GOLD_BRIGHT),
                ("sudo THMD-guru-ai vm-node init lab80-vm2", CYAN_ACCENT),
                ("", TEXT_PRIMARY),
                ("# 2. Khởi chạy Docker (Nginx + Juice Shop + DVWA + WebGoat + DB):", GOLD_BRIGHT),
                ("cd /usr/share/thmd-guru/labs/vmware-zap-rag-pfsense", TEXT_PRIMARY),
                ("sudo bash vm2-web-target/setup.sh", CYAN_ACCENT),
                ("", TEXT_PRIMARY),
                ("# 3. Kiểm tra các cổng dịch vụ mục tiêu đã mở:", GOLD_BRIGHT),
                ("curl -I http://192.168.80.20:3000   # OWASP Juice Shop", GREEN_OK),
                ("curl -I http://192.168.80.20:8081   # DVWA (admin / password)", GREEN_OK),
                ("tail -f /var/log/nginx/lab_access.log", TEXT_MUTED),
            ],
        ),
        (
            (816, 88, 1552, 504),
            "TRÊN MÁY ẢO VM3 (192.168.80.30 — AI-RAG SERVER)",
            GOLD_ROYAL,
            [
                ("# 1. Đặt IP tĩnh 192.168.80.30/24 và tối ưu Kernel vm.max_map_count:", GOLD_BRIGHT),
                ("sudo THMD-guru-ai vm-node init lab80-vm3", CYAN_ACCENT),
                ("sudo THMD-guru-ai harden --apply", CYAN_ACCENT),
                ("", TEXT_PRIMARY),
                ("# 2. Dựng FastAPI (:8000) + Qdrant (:6333) + Ollama (qwen2.5:3b):", GOLD_BRIGHT),
                ("cd /usr/share/thmd-guru/labs/vmware-zap-rag-pfsense", TEXT_PRIMARY),
                ("sudo bash vm3-ai-rag/setup.sh", CYAN_ACCENT),
                ("", TEXT_PRIMARY),
                ("# 3. Kiểm tra trạng thái AI-RAG API & Kho tri thức OWASP/CWE:", GOLD_BRIGHT),
                ("curl http://192.168.80.30:8000/health", GREEN_OK),
                ("# -> {\"status\":\"ok\",\"llm\":true,\"kb_chunks\":35}", GREEN_OK),
            ],
        ),
        (
            (48, 528, 784, 952),
            "TRÊN MÁY ẢO VM1 (192.168.80.10 — KALI / ATTT + OWASP ZAP)",
            CYAN_ACCENT,
            [
                ("# 1. Đặt IP tĩnh 192.168.80.10/24 và bật Egress-Guard (Phạm vi an toàn):", GOLD_BRIGHT),
                ("sudo THMD-guru-ai vm-node init lab80-vm1", CYAN_ACCENT),
                ("cd /usr/share/thmd-guru/labs/vmware-zap-rag-pfsense", TEXT_PRIMARY),
                ("sudo bash vm1-kali-zap/setup.sh", CYAN_ACCENT),
                ("", TEXT_PRIMARY),
                ("# 2. Khởi chạy OWASP ZAP Daemon ở cổng 8090:", GOLD_BRIGHT),
                ("zap.sh -daemon -host 127.0.0.1 -port 8090 \\", TEXT_PRIMARY),
                ("  -config api.key=$(sudo cat /etc/thmd-guru/zap-api-key) &", TEXT_PRIMARY),
                ("", TEXT_PRIMARY),
                ("# 3. Thực thi Bước (1) Quét Web & Bước (2) Đẩy Alert+Evidence sang VM3:", GOLD_BRIGHT),
                ("python3 vm1-kali-zap/zap_scan.py --target http://192.168.80.20:3000 \\", GREEN_OK),
                ("  --mode baseline --push http://192.168.80.30:8000/api/v1/alerts", GREEN_OK),
            ],
        ),
        (
            (816, 528, 1552, 952),
            "NGƯỜI ĐÁNH GIÁ / GVHD (TRÌNH DUYỆT HOST HOẶC CLI)",
            PURPLE_AI,
            [
                ("# Cách A: Chạy Demo kiểm thử nhanh không cần chờ ZAP quét:", GOLD_BRIGHT),
                ("THMD-guru-ai lab run vmware-zap-rag-pfsense", GREEN_OK),
                ("", TEXT_PRIMARY),
                ("# Cách B: Mở Dashboard trên trình duyệt máy thật Windows:", GOLD_BRIGHT),
                ("# Truy cập: http://192.168.80.30:8000/  (Hoặc /docs)", CYAN_ACCENT),
                ("", TEXT_PRIMARY),
                ("# Cách C: Tải mẫu CSV, gắn nhãn Ground Truth & xuất chỉ số NCKH:", GOLD_BRIGHT),
                ("python3 evaluator/evaluate.py --server http://192.168.80.30:8000 --list", TEXT_PRIMARY),
                ("python3 evaluator/evaluate.py --run <run_id> --template labels.csv", TEXT_PRIMARY),
                ("python3 evaluator/evaluate.py --run <run_id> --labels labels.csv \\", CYAN_ACCENT),
                ("  --reviewer \"Hoi-Dong-NCKH\" --report report.html", CYAN_ACCENT),
            ],
        ),
    ]

    for box, title, col, lines in boxes:
        draw_rounded_card(d, box, fill=BG_NAVY, outline=col, width=2, radius=12)
        d.rounded_rectangle((box[0], box[1], box[2], box[1] + 46), radius=12, fill=SAPPHIRE_OLD)
        d.rectangle((box[0], box[1] + 24, box[2], box[1] + 46), fill=SAPPHIRE_OLD)
        d.text((box[0] + 20, box[1] + 12), "► " + title, fill=col, font=fonts["body_b"])

        ty = box[1] + 62
        for ltxt, lcol in lines:
            d.text((box[0] + 22, ty), ltxt, fill=lcol, font=fonts["mono_b"] if lcol in (CYAN_ACCENT, GREEN_OK) else fonts["mono_sm"])
            ty += 28

    for p in out_paths:
        p.parent.mkdir(parents=True, exist_ok=True)
        img.save(p, "PNG")


def set_cell_bg(cell, hex_color: str):
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    cell._tc.get_or_add_tcPr().append(shading)


def add_styled_table(doc: Document, headers: list[str], rows: list[list[str]]):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    hdr_cells = table.rows[0].cells
    for i, h_text in enumerate(headers):
        hdr_cells[i].text = ""
        p = hdr_cells[i].paragraphs[0]
        run = p.add_run(h_text)
        run.bold = True
        run.font.name = "Segoe UI"
        run.font.size = Pt(10)
        run.font.color.rgb = RGBColor(245, 215, 122)
        set_cell_bg(hdr_cells[i], "0B3D91")

    for r_idx, row_data in enumerate(rows):
        row_cells = table.add_row().cells
        bg = "F4F7FB" if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, val in enumerate(row_data):
            row_cells[c_idx].text = ""
            p = row_cells[c_idx].paragraphs[0]
            run = p.add_run(val)
            run.font.name = "Segoe UI"
            run.font.size = Pt(9.5)
            if c_idx == 0:
                run.bold = True
                run.font.color.rgb = RGBColor(11, 61, 145)
            else:
                run.font.color.rgb = RGBColor(20, 30, 50)
            set_cell_bg(row_cells[c_idx], bg)
    doc.add_paragraph()


def add_heading_styled(doc: Document, text: str, level: int = 1):
    h = doc.add_heading(text, level=level)
    for run in h.runs:
        run.font.name = "Segoe UI"
        if level == 1:
            run.font.size = Pt(15)
            run.font.color.rgb = RGBColor(11, 61, 145)
        elif level == 2:
            run.font.size = Pt(12.5)
            run.font.color.rgb = RGBColor(180, 130, 20)
        else:
            run.font.size = Pt(11)
            run.font.color.rgb = RGBColor(30, 64, 130)
    return h


def add_para(doc: Document, text: str, bold_prefix: str = "", bullet: bool = False):
    p = doc.add_paragraph(style="List Bullet" if bullet else None)
    p.paragraph_format.space_after = Pt(5)
    p.paragraph_format.line_spacing = 1.2
    if bold_prefix:
        r_pre = p.add_run(bold_prefix)
        r_pre.bold = True
        r_pre.font.name = "Segoe UI"
        r_pre.font.size = Pt(10.5)
        r_pre.font.color.rgb = RGBColor(11, 61, 145)
    r = p.add_run(text)
    r.font.name = "Segoe UI"
    r.font.size = Pt(10.5)
    r.font.color.rgb = RGBColor(25, 35, 50)
    return p


def add_code_block(doc: Document, code_text: str):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = table.rows[0].cells[0]
    set_cell_bg(cell, "0A0F1E")
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(4)
    run = p.add_run(code_text.strip())
    run.font.name = "Consolas"
    run.font.size = Pt(9.5)
    run.font.color.rgb = RGBColor(96, 165, 250)
    doc.add_paragraph()


def add_figure(doc: Document, img_path: Path, caption: str, width_inches: float = 6.4):
    if not img_path.exists():
        return
    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img.paragraph_format.space_before = Pt(6)
    p_img.paragraph_format.space_after = Pt(3)
    run_img = p_img.add_run()
    run_img.add_picture(str(img_path), width=Inches(width_inches))

    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap.paragraph_format.space_after = Pt(10)
    run_cap = p_cap.add_run(caption)
    run_cap.italic = True
    run_cap.bold = True
    run_cap.font.name = "Segoe UI"
    run_cap.font.size = Pt(9.5)
    run_cap.font.color.rgb = RGBColor(11, 61, 145)


def build_vmware_manual_docx(root: Path, mockups_dir: Path, artifact_dir: Path, out_docx_paths: list[Path]):
    doc = Document()

    for section in doc.sections:
        section.top_margin = Inches(0.75)
        section.bottom_margin = Inches(0.75)
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)

    # ==========================================================================
    # COVER PAGE
    # ==========================================================================
    p_org = doc.add_paragraph()
    p_org.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p_org.add_run("THMD-GURU GLOBAL TECH ACADEMY\nTRUNG TÂM NGHIÊN CỨU PHÁT TRIỂN HỆ ĐIỀU HÀNH & AN TOÀN THÔNG TIN")
    r.bold = True
    r.font.name = "Segoe UI"
    r.font.size = Pt(13)
    r.font.color.rgb = RGBColor(11, 61, 145)

    p_line = doc.add_paragraph()
    p_line.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_line = p_line.add_run("────────────────────────────────────────────────────────")
    r_line.font.color.rgb = RGBColor(212, 175, 55)

    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(16)
    p_title.paragraph_format.space_after = Pt(10)
    r_t = p_title.add_run(
        "CẨM NANG HƯỚNG DẪN TẢI, CÀI ĐẶT VÀ CẤU HÌNH TỪ A–Z\n"
        "HỆ ĐIỀU HÀNH THMD-GURU LINUX 1.0 (\"GENESIS\")\n"
        "& PHÒNG LAB NCKH OWASP ZAP + AI/RAG TRÊN VMWARE WORKSTATION"
    )
    r_t.bold = True
    r_t.font.name = "Segoe UI"
    r_t.font.size = Pt(18)
    r_t.font.color.rgb = RGBColor(10, 15, 30)

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_sub = p_sub.add_run(
        "Tài liệu thực hành chi tiết từng bước: Tải ISO từ GitHub Releases • Kiểm tra SHA-256 • Cấu hình VMnet2 (192.168.80.0/24)\n"
        "• Tạo & Cài đặt 3 Máy ảo (ATTT, Server, Desktop) + pfSense • Khởi chạy Thực nghiệm NCKH OWASP ZAP + AI/RAG"
    )
    r_sub.italic = True
    r_sub.font.name = "Segoe UI"
    r_sub.font.size = Pt(10.5)
    r_sub.font.color.rgb = RGBColor(80, 95, 120)

    add_figure(
        doc,
        mockups_dir / "vmware_guide_1_virtual_network_editor.png",
        "Hình bìa: Quy hoạch mạng ảo VMnet2 (192.168.80.0/24) trên VMware Workstation cho hệ sinh thái THMD-Guru Linux.",
        width_inches=6.1,
    )

    add_styled_table(
        doc,
        ["Thông tin Tài liệu", "Chi tiết Kỹ thuật & Đường dẫn Chính thức"],
        [
            ["Tên Hệ điều hành", "THMD-Guru Linux 1.0 \"Genesis\" (Desktop, Server, ATTT) — Debian 12 Bookworm amd64"],
            ["Kho mã nguồn GitHub", "https://github.com/DangTran1709/thmd-guru-os-forge"],
            ["Trang tải bộ cài (.iso)", "https://github.com/DangTran1709/thmd-guru-os-forge/releases/tag/v1.0.0-genesis"],
            ["Phần mềm Ảo hóa", "VMware Workstation Pro / Player 17.x (Hỗ trợ tương đương trên VirtualBox / Proxmox / QEMU)"],
            ["Đề tài NCKH Tích hợp", "Đánh giá hiệu quả AI kết hợp RAG trong xác minh và ưu tiên cảnh báo bảo mật Web từ ZAP"],
        ],
    )

    doc.add_page_break()

    # ==========================================================================
    # CHƯƠNG 1: CHUẨN BỊ & TẢI FILE .ISO TỪ GITHUB RELEASES
    # ==========================================================================
    add_heading_styled(doc, "CHƯƠNG 1: CHUẨN BỊ MÁY TRẠM (HOST PC) & TẢI BỘ CÀI .ISO TỪ GITHUB RELEASES", 1)

    add_heading_styled(doc, "1.1. Yêu cầu Cấu hình Máy tính Thật (Host PC / Workstation)", 2)
    add_para(doc, "Windows 10/11 64-bit hoặc Linux 64-bit, đã bật ảo hóa phần cứng (Intel VT-x hoặc AMD-V) trong BIOS/UEFI.", "Hệ điều hành máy thật: ", bullet=True)
    add_para(doc, "Tối thiểu 8 GB RAM (nếu chạy từng máy ảo đơn lẻ) hoặc khuyến nghị 16 GB RAM, 6 Core / 12 Thread (để chạy đồng thời cả 3 máy ảo VM1 + VM2 + VM3 và tường lửa pfSense).", "Bộ nhớ RAM & Vi xử lý: ", bullet=True)
    add_para(doc, "Còn trống tối thiểu 60 GB – 150 GB trên ổ cứng SSD/NVMe để đạt tốc độ đọc/ghi container và Vector DB nhanh nhất.", "Dung lượng ổ cứng: ", bullet=True)
    add_para(doc, "VMware Workstation Pro 17.x (hiện đã miễn phí cho mục đích cá nhân/nghiên cứu).", "Phần mềm ảo hóa: ", bullet=True)

    add_heading_styled(doc, "1.2. Đường dẫn Tải Trực Tiếp 3 File .ISO từ GitHub Releases", 2)
    add_para(
        doc,
        "Truy cập trang phát hành chính thức tại https://github.com/DangTran1709/thmd-guru-os-forge/releases/tag/v1.0.0-genesis và tải về 3 tệp .iso tương ứng với 3 vai trò máy ảo trong phòng Lab:",
    )

    add_styled_table(
        doc,
        ["Phiên bản Hệ điều hành", "Vai trò trong Phòng Lab VMware", "Link Tải Trực Tiếp (.iso) & Mã Băm SHA-256"],
        [
            [
                "1. THMD-Guru ATTT 1.0\n(thmd-guru-attt-1.0-genesis-amd64.iso)",
                "VM1 (192.168.80.10)\nMáy quét bảo mật Web OWASP ZAP",
                "Link: https://github.com/DangTran1709/thmd-guru-os-forge/releases/download/v1.0.0-genesis/thmd-guru-attt-1.0-genesis-amd64.iso\nSHA256: 61e884d0352755f96913ca40908fc2fadb9c1cde02e141d4f30b33e020e8f346",
            ],
            [
                "2. THMD-Guru Server 1.0\n(thmd-guru-server-1.0-genesis-amd64.iso)",
                "VM2 (192.168.80.20)\nWeb Server Mục tiêu (Nginx, DVWA, Juice Shop)",
                "Link: https://github.com/DangTran1709/thmd-guru-os-forge/releases/download/v1.0.0-genesis/thmd-guru-server-1.0-genesis-amd64.iso\nSHA256: 92b8c83e9d76ee9bf09f48f624e8e668b7fd9cce6c94d67fb457fe081eee5b49",
            ],
            [
                "3. THMD-Guru Desktop 1.0\n(thmd-guru-desktop-1.0-genesis-amd64.iso)",
                "VM3 (192.168.80.30)\nMáy chủ AI-RAG (FastAPI, Qdrant, Ollama)",
                "Link: https://github.com/DangTran1709/thmd-guru-os-forge/releases/download/v1.0.0-genesis/thmd-guru-desktop-1.0-genesis-amd64.iso\nSHA256: d7f6fd3e1faa565282f4b021816594dab1557868df22c0d253fba1ec45212965",
            ],
        ],
    )

    add_heading_styled(doc, "1.3. Kiểm tra Tính Toàn Vẹn của File .ISO vừa tải về (Windows PowerShell)", 2)
    add_para(doc, "Sau khi tải 3 file .iso về thư mục Downloads, mở Windows PowerShell và chạy lệnh sau để đối chiếu mã băm SHA-256:")
    add_code_block(
        doc,
        "cd $HOME\\Downloads\n"
        "Get-FileHash thmd-guru-*-1.0-genesis-amd64.iso -Algorithm SHA256 | Format-List Path, Hash",
    )

    doc.add_page_break()

    # ==========================================================================
    # CHƯƠNG 2: CẤU HÌNH MẠNG ẢO VMWARE VIRTUAL NETWORK EDITOR
    # ==========================================================================
    add_heading_styled(doc, "CHƯƠNG 2: CẤU HÌNH MẠNG ẢO TRONG VMWARE VIRTUAL NETWORK EDITOR (VMNET2 & VMNET8)", 1)

    add_para(
        doc,
        "Để 3 máy ảo (VM1, VM2, VM3) và tường lửa pfSense liên lạc với nhau trên dải mạng cô lập 192.168.80.0/24 đúng như sơ đồ nghiên cứu, bạn cần thiết lập Switch ảo VMnet2 trong VMware Workstation theo 5 bước dưới đây (chỉ cần làm 1 lần duy nhất):",
    )

    add_para(doc, "Mở VMware Workstation Pro -> Trên thanh menu chọn Edit -> Virtual Network Editor...", "Bước 1: ", bullet=True)
    add_para(doc, "Ở góc dưới bên phải cửa sổ, bấm nút [Change Settings] và chọn Yes (cấp quyền Administrator).", "Bước 2: ", bullet=True)
    add_para(doc, "Bấm nút [Add Network...] -> Chọn [VMnet2] -> Bấm OK (Nếu đã có sẵn VMnet2 thì nhấp chọn dòng VMnet2).", "Bước 3: ", bullet=True)
    add_para(doc, "Tại khung VMnet Information bên dưới, thiết lập chính xác 4 thông số của VMnet2:\n  • Chọn kiểu mạng: (●) Host-only (connect VMs internally in a private network)\n  • Tích chọn: [x] Connect a host virtual adapter to this network\n  • BỎ TÍCH: [ ] Use local DHCP service to distribute IP address to VMs (Rất quan trọng: để dùng IP tĩnh chuẩn NCKH)\n  • Nhập Subnet IP: 192.168.80.0  |  Subnet mask: 255.255.255.0 -> Bấm [Apply] -> [OK].", "Bước 4: ", bullet=True)
    add_para(doc, "Tránh đụng địa chỉ IP 192.168.80.1 giữa máy thật Windows và pfSense: Mở hộp thoại Run (Win + R) -> gõ ncpa.cpl -> Nhấp đúp vào card 'VMware Network Adapter VMnet2' -> Chọn IPv4 -> Đặt IP tĩnh cho máy thật Windows là 192.168.80.254, Subnet Mask 255.255.255.0 (để trống Default Gateway).", "Bước 5 (Quan trọng): ", bullet=True)

    add_figure(
        doc,
        mockups_dir / "vmware_guide_1_virtual_network_editor.png",
        "Hình 2.1: Giao diện thiết lập mạng VMnet2 (Host-Only 192.168.80.0/24) trong VMware Virtual Network Editor.",
    )

    doc.add_page_break()

    # ==========================================================================
    # CHƯƠNG 3: TẠO MÁY ẢO MỚI (NEW VIRTUAL MACHINE WIZARD)
    # ==========================================================================
    add_heading_styled(doc, "CHƯƠNG 3: HƯỚNG DẪN TẠO MÁY ẢO (NEW VIRTUAL MACHINE WIZARD) & GẮN FILE .ISO", 1)

    add_para(
        doc,
        "Trong VMware Workstation, bấm tổ hợp phím Ctrl + N (hoặc File -> New Virtual Machine...) và thực hiện lần lượt theo 6 bước trên màn hình hướng dẫn để tạo các máy ảo VM1, VM2, VM3 (và pfSense nếu cần):",
    )

    add_figure(
        doc,
        mockups_dir / "vmware_guide_2_new_vm_wizard.png",
        "Hình 3.1: Hướng dẫn 6 bước tạo máy ảo trong VMware Workstation và bảng phân bổ tài nguyên phần cứng cho từng VM.",
    )

    add_styled_table(
        doc,
        ["Tên Máy Ảo (VM Name)", "Guest OS Version", "vCPU", "RAM", "Ổ Cứng", "Card Mạng (NIC)", "File .ISO Gắn Vào Ổ CD/DVD"],
        [
            ["VM1-THMD-Guru-ATTT-ZAP", "Debian 12.x 64-bit", "2 vCPU", "3 GB (3072 MB)", "40 GB", "Custom: VMnet2", "thmd-guru-attt-1.0-genesis-amd64.iso"],
            ["VM2-THMD-Guru-Server-Web", "Debian 12.x 64-bit", "2 vCPU", "4 GB (4096 MB)", "40 GB", "Custom: VMnet2", "thmd-guru-server-1.0-genesis-amd64.iso"],
            ["VM3-THMD-Guru-AI-RAG", "Debian 12.x 64-bit", "3 vCPU", "4 GB (4096 MB)", "60 GB", "Custom: VMnet2", "thmd-guru-desktop-1.0-genesis-amd64.iso"],
            ["VM0-pfSense-Firewall (Tùy chọn)", "FreeBSD 14 64-bit", "1 vCPU", "1 GB (1024 MB)", "16 GB", "NIC1: VMnet8 (NAT)\nNIC2: VMnet2 (LAN)", "pfSense-CE-2.7.2-RELEASE-amd64.iso"],
        ],
    )

    doc.add_page_break()

    # ==========================================================================
    # CHƯƠNG 4: KHỞI ĐỘNG & CÀI ĐẶT HỆ ĐIỀU HÀNH TỪ 0% ĐẾN 100%
    # ==========================================================================
    add_heading_styled(doc, "CHƯƠNG 4: QUÁ TRÌNH KHỞI ĐỘNG (BOOTLOADER) & CÀI ĐẶT HỆ ĐIỀU HÀNH TỪ 0% ĐẾN 100%", 1)

    add_para(
        doc,
        "Sau khi tạo xong máy ảo, bấm nút [Power on this virtual machine]. Hệ điều hành THMD-Guru Linux hỗ trợ 2 phương thức vận hành linh hoạt:",
    )
    add_para(
        doc,
        "Chọn mục số 1 (Mặc định - Default) '1. THMD-Guru Linux 1.0 - Install & VMware Lab Wizard' (trình hướng dẫn thmd-installer tự động mở ngay sau 5 giây, cho phép gán tự động IP tĩnh 192.168.80.10 / .20 / .30 bằng 1 phím bấm 1/2/3 trên mạng VMnet2 không có DHCP) hoặc chạy bộ cài đồ họa Calamares trên bản Full Production ISO:",
        "Phương thức A (Mặc định - Mục 1) — Trình hướng dẫn Cài đặt & Cấu hình Phòng Lab (thmd-installer / Calamares): ",
        bullet=True,
    )
    add_para(
        doc,
        "Chọn mục số 2 '2. THMD-Guru Linux 1.0 - Live System (RAM OS)'. Hệ điều hành khởi động thẳng vào bộ nhớ RAM trong chưa đầy 5 giây (hỗ trợ cả BIOS và UEFI), tự động khởi tạo udev/devtmpfs, nạp sẵn công cụ THMD-guru-ai và toàn bộ kịch bản phòng Lab tại /usr/share/thmd-guru/labs/.",
        "Phương thức B (Mục 2) — Khởi động tức thời vào Shell (Live RAM OS < 5 giây): ",
        bullet=True,
    )

    add_figure(
        doc,
        mockups_dir / "step1_bootloader_bios_uefi.png",
        "Hình 4.1 (Giai đoạn 1): Màn hình Bootloader GRUB2/ISOLINUX khi bấm Power On máy ảo trong VMware.",
        width_inches=6.0,
    )
    add_figure(
        doc,
        mockups_dir / "step2_calamares_installer_welcome_part.png",
        "Hình 4.2 (Giai đoạn 2): Trình cài đặt đồ họa Calamares — Tự động phân vùng ổ cứng LVM/LUKS2, bật ZRAM và chọn vai trò máy ảo VMware.",
        width_inches=6.0,
    )

    doc.add_page_break()

    add_figure(
        doc,
        mockups_dir / "step3_calamares_installing_progress.png",
        "Hình 4.3 (Giai đoạn 3): Tiến trình cài đặt 78% — Xác thực chữ ký số RSA-4096, giải nén THMD-guru-ai, open-vm-tools và phòng Lab NCKH.",
        width_inches=6.0,
    )
    add_figure(
        doc,
        mockups_dir / "step4_installation_completed.png",
        "Hình 4.4 (Giai đoạn 4): Hoàn tất cài đặt 100% — Hiển thị bảng kiểm tra cấu hình sau cài đặt và khởi động lại vào màn hình chính.",
        width_inches=6.0,
    )

    doc.add_page_break()

    # ==========================================================================
    # CHƯƠNG 5: CẤU HÌNH TƯỜNG LỬA PFSENSE (192.168.80.1)
    # ==========================================================================
    add_heading_styled(doc, "CHƯƠNG 5: CẤU HÌNH TƯỜNG LỬA PFSENSE GATEWAY (192.168.80.1/24)", 1)

    add_para(
        doc,
        "Nếu bạn triển khai theo sơ đồ có tường lửa pfSense đứng làm cổng nối giữa VMnet8 (Internet) và VMnet2 (192.168.80.0/24), hãy thực hiện các bước sau trên máy ảo pfSense:",
    )

    uploaded_diag = artifact_dir / ".user_uploaded" / "media_1793723120037_b6e5112f.jpg"
    if uploaded_diag.exists():
        add_figure(
            doc,
            uploaded_diag,
            "Hình 5.1: Sơ đồ tổng thể hệ thống LAB trên VMware Workstation (pfSense Firewall + VMnet2 192.168.80.0/24 + 3 VM + Người đánh giá).",
            width_inches=6.2,
        )

    add_para(doc, "Tại màn hình Console đen trắng của pfSense sau khi khởi động, chọn phím 1) Assign Interfaces -> Không dùng VLAN (n) -> Gán WAN là em0 (card VMnet8) và LAN là em1 (card VMnet2).", "Bước 1 (Gán Card Mạng): ", bullet=True)
    add_para(doc, "Chọn phím 2) Set interface(s) IP address -> Chọn số 2 (LAN) -> Nhập IP: 192.168.80.1, Subnet bit count: 24 -> Enter (không đặt Upstream Gateway cho LAN) -> Tắt DHCP Server trên LAN (n) để 3 VM dùng IP tĩnh chuẩn.", "Bước 2 (Đặt IP LAN 192.168.80.1/24): ", bullet=True)
    add_para(doc, "Từ trình duyệt trên VM1/VM3 (hoặc máy thật Windows 192.168.80.254), truy cập https://192.168.80.1 (Tài khoản: admin / Mật khẩu: pfsense). Vào Services -> DNS Resolver -> Thêm 3 Host Overrides: kali.thmd.lab (192.168.80.10), target.thmd.lab (192.168.80.20), airag.thmd.lab (192.168.80.30).", "Bước 3 (Cấu hình WebGUI & DNS nội bộ): ", bullet=True)
    add_para(doc, "Vào Firewall -> Rules -> LAN và thiết lập 5 luật từ trên xuống để đảm bảo 'Phạm vi an toàn: Chỉ quét môi trường lab được cấp phép trên VMware':", "Bước 4 (Thiết lập Luật Tường lửa Phạm vi An toàn): ", bullet=True)

    add_styled_table(
        doc,
        ["Thứ tự", "Action", "Source (Nguồn)", "Destination (Đích)", "Port", "Mục đích Bảo mật trong Đề tài NCKH"],
        [
            ["Luật 1", "Pass", "LAN net", "LAN address (.80.1)", "443, 53", "Cho phép truy cập WebGUI pfSense & phân giải DNS nội bộ"],
            ["Luật 2", "BLOCK + Log", "192.168.80.10 (VM1 ZAP)", "! 192.168.80.0/24", "Any", "PHẠM VI AN TOÀN: Chặn tuyệt đối máy quét VM1 đi ra ngoài Internet"],
            ["Luật 3", "Pass", "192.168.80.20 (VM2)", "Any", "80, 443, 53", "Cho phép VM2 tải Docker image (DVWA, Juice Shop, WebGoat) khi cài đặt"],
            ["Luật 4", "Pass", "192.168.80.30 (VM3)", "Any", "80, 443, 53", "Cho phép VM3 tải gói Python & mô hình LLM nội bộ từ Ollama"],
            ["Luật 5", "BLOCK + Log", "LAN net", "Any", "Any", "Chặn toàn bộ kết nối trái phép còn lại"],
        ],
    )

    doc.add_page_break()

    # ==========================================================================
    # CHƯƠNG 6: CẤU HÌNH 3 MÁY ẢO VM1, VM2, VM3 & VẬN HÀNH THỰC NGHIỆM NCKH
    # ==========================================================================
    add_heading_styled(doc, "CHƯƠNG 6: CẤU HÌNH CHI TIẾT 3 MÁY ẢO (VM2, VM3, VM1) & VẬN HÀNH THỰC NGHIỆM TỪ A–Z", 1)

    add_para(
        doc,
        "Toàn bộ mã nguồn tự động hóa của Phòng Lab đã được cài đặt sẵn trong hệ điều hành tại đường dẫn /usr/share/thmd-guru/labs/vmware-zap-rag-pfsense/ (hoặc có thể tải trực tiếp bằng lệnh git clone https://github.com/DangTran1709/thmd-guru-os-forge.git). Hãy thực hiện tuần tự theo bảng lệnh dưới đây:",
    )

    add_figure(
        doc,
        mockups_dir / "vmware_guide_3_end_to_end_commands.png",
        "Hình 6.1: Bảng tổng hợp các câu lệnh cấu hình và chạy thực nghiệm từ A–Z trên VM2, VM3, VM1 và máy của Người đánh giá / GVHD.",
    )

    add_heading_styled(doc, "6.1. Cấu hình Máy ảo VM2 — Web Server Mục tiêu (192.168.80.20)", 2)
    add_para(doc, "Đăng nhập vào máy ảo VM2 (THMD-Guru Server hoặc Ubuntu Server) và chạy 3 lệnh sau để đặt IP tĩnh 192.168.80.20/24 và khởi chạy toàn bộ cụm ứng dụng Web mục tiêu:")
    add_code_block(
        doc,
        "# 1. Tự động đặt IP tĩnh 192.168.80.20/24 (GW 192.168.80.1) và hostname lab-vm2-web-target\n"
        "sudo THMD-guru-ai vm-node init lab80-vm2\n\n"
        "# 2. Khởi chạy Docker Compose (Nginx :80, OWASP Juice Shop :3000, DVWA :8081, WebGoat :8080, MariaDB)\n"
        "cd /usr/share/thmd-guru/labs/vmware-zap-rag-pfsense\n"
        "sudo bash vm2-web-target/setup.sh\n\n"
        "# 3. Theo dõi log truy cập HTTP trực tiếp để làm bằng chứng đối chiếu\n"
        "tail -f /var/log/nginx/lab_access.log",
    )

    add_heading_styled(doc, "6.2. Cấu hình Máy ảo VM3 — AI-RAG Server (192.168.80.30)", 2)
    add_para(doc, "Đăng nhập vào máy ảo VM3 (THMD-Guru Desktop/Server) và chạy các lệnh sau để đặt IP tĩnh 192.168.80.30/24, nạp kho tri thức OWASP/CWE/WSTG/ZAP và bật máy chủ FastAPI (:8000):")
    add_code_block(
        doc,
        "# 1. Tự động đặt IP tĩnh 192.168.80.30/24 và nâng vm.max_map_count = 1048576 cho Vector DB\n"
        "sudo THMD-guru-ai vm-node init lab80-vm3\n"
        "sudo THMD-guru-ai harden --apply\n\n"
        "# 2. Cài đặt Qdrant (:6333), Ollama (:11434, mô hình qwen2.5:3b + nomic-embed-text) và dịch vụ FastAPI (:8000)\n"
        "cd /usr/share/thmd-guru/labs/vmware-zap-rag-pfsense\n"
        "sudo bash vm3-ai-rag/setup.sh\n\n"
        "# (Tùy chọn) Nếu máy có ít RAM, có thể chạy ở chế độ Hybrid RAG + Rule Engine siêu nhẹ (không cần GPU/Ollama):\n"
        "sudo USE_LLM=0 bash vm3-ai-rag/setup.sh",
    )

    add_heading_styled(doc, "6.3. Cấu hình Máy ảo VM1 — Kali / THMD-Guru ATTT + OWASP ZAP (192.168.80.10)", 2)
    add_para(doc, "Đăng nhập vào máy ảo VM1 (THMD-Guru ATTT hoặc Kali Linux) và thực hiện Bước (1) Quét Web + Bước (2) Gửi Alert & Evidence sang VM3:")
    add_code_block(
        doc,
        "# 1. Tự động đặt IP tĩnh 192.168.80.10/24 và bật tường lửa Egress-Guard (chỉ cho phép quét 192.168.80.20)\n"
        "sudo THMD-guru-ai vm-node init lab80-vm1\n"
        "cd /usr/share/thmd-guru/labs/vmware-zap-rag-pfsense\n"
        "sudo bash vm1-kali-zap/setup.sh\n\n"
        "# 2. Khởi chạy OWASP ZAP ở chế độ Daemon (cổng 8090)\n"
        "zap.sh -daemon -host 127.0.0.1 -port 8090 -config api.key=$(sudo cat /etc/thmd-guru/zap-api-key) &\n\n"
        "# 3. Thực thi Bước (1) Quét mục tiêu VM2 và Bước (2) Đẩy tự động Alert + Evidence sang AI-RAG VM3\n"
        "python3 vm1-kali-zap/zap_scan.py --target http://192.168.80.20:3000 --mode baseline \\\n"
        "        --push http://192.168.80.30:8000/api/v1/alerts",
    )

    add_heading_styled(doc, "6.4. Thao tác của Người đánh giá / GVHD / Nhóm NCKH (Gắn nhãn Ground Truth & Xuất Báo cáo)", 2)
    add_para(doc, "Sau khi VM3 phân tích xong (Bước 3), Người đánh giá / GVHD có thể mở trình duyệt truy cập http://192.168.80.30:8000/ hoặc chạy công cụ đánh giá để gắn nhãn Ground Truth và xuất bảng chỉ số khoa học:")
    add_code_block(
        doc,
        "# Cách 1: Chạy trực tiếp bài kiểm thử chuẩn 20 cảnh báo (Juice Shop + DVWA) ngay trên bất kỳ máy nào:\n"
        "THMD-guru-ai lab run vmware-zap-rag-pfsense\n\n"
        "# Cách 2: Tương tác với máy chủ AI-RAG thực tế (192.168.80.30:8000) để gắn nhãn Ground Truth:\n"
        "cd /usr/share/thmd-guru/labs/vmware-zap-rag-pfsense\n"
        "python3 evaluator/evaluate.py --server http://192.168.80.30:8000 --list\n"
        "python3 evaluator/evaluate.py --server http://192.168.80.30:8000 --run <run_id> --template my_labels.csv\n"
        "# (Mở file my_labels.csv điền cột ground_truth_tp = 1 hoặc 0 và expert_relevance = 0..3, sau đó đẩy lên VM3):\n"
        "python3 evaluator/evaluate.py --server http://192.168.80.30:8000 --run <run_id> \\\n"
        "        --labels my_labels.csv --reviewer \"GVHD\" --report bao_cao_xac_minh.html",
    )

    doc.add_page_break()

    # ==========================================================================
    # CHƯƠNG 7: QUẢN LÝ SNAPSHOT, LINKED CLONE & XỬ LÝ SỰ CỐ (TROUBLESHOOTING)
    # ==========================================================================
    add_heading_styled(doc, "CHƯƠNG 7: QUẢN LÝ SNAPSHOT, NHÂN BẢN LINKED CLONE & XỬ LÝ SỰ CỐ TRÊN VMWARE", 1)

    add_heading_styled(doc, "7.1. Quy tắc Chụp Snapshot 'Clean-Baseline' để Đảm bảo Tính Lặp lại Khoa học", 2)
    add_para(
        doc,
        "Trong nghiên cứu khoa học thực nghiệm, môi trường mục tiêu (VM2) phải ở trạng thái sạch giống hệt nhau trước mỗi lần quét (Baseline vs Zero-Shot LLM vs AI+RAG). Ngay sau khi chạy xong setup.sh trên cả 3 máy ảo:",
    )
    add_para(doc, "Trên menu VMware Workstation, bấm VM -> Snapshot -> Take Snapshot... và đặt tên là '01-Clean-Lab-Ready'.", "1. Chụp Snapshot: ", bullet=True)
    add_para(doc, "Nếu muốn nhân bản nhanh máy ảo bằng tính năng 'Manage -> Clone -> Create a linked clone' (tiết kiệm 80% ổ cứng), hãy chạy lệnh dưới đây trước khi tắt máy làm khuôn mẫu (Base Template) để tránh trùng lặp định danh mạng:", "2. Chuẩn bị trước khi Clone: ", bullet=True)
    add_code_block(doc, "sudo THMD-guru-ai vm-node clone-prep")

    add_heading_styled(doc, "7.2. Bảng Xử lý 6 Sự cố Thường gặp Nhất trên VMware Workstation (Troubleshooting A–Z)", 2)

    add_styled_table(
        doc,
        ["Hiện tượng / Sự cố", "Nguyên nhân Gốc rễ", "Cách Khắc phục Triệt để"],
        [
            [
                "1. Không ping được 192.168.80.1 hoặc mạng chập chờn",
                "Card ảo 'VMware Network Adapter VMnet2' trên Windows Host mặc định lấy IP 192.168.80.1 trùng với pfSense.",
                "Mở ncpa.cpl trên Windows -> Đổi IPv4 của VMware Network Adapter VMnet2 thành 192.168.80.254/24 (không điền Gateway).",
            ],
            [
                "2. Máy ảo nhận IP 192.168.80.128 thay vì .10 / .20 / .30",
                "Chưa bỏ tích 'Use local DHCP service' trên VMnet2 trong Virtual Network Editor hoặc chưa chạy lệnh đặt IP tĩnh.",
                "Bỏ tích DHCP của VMnet2 và chạy lại lệnh: sudo THMD-guru-ai vm-node init lab80-vm1 (hoặc vm2 / vm3).",
            ],
            [
                "3. VM1 báo lỗi [DENY] hoặc không truy cập được Internet",
                "Tính năng bảo vệ 'Phạm vi an toàn' (egress-guard.nft) trên VM1 đang khóa kết nối ra ngoài LAB.",
                "Đây là cơ chế an toàn chủ động. Nếu cần tạm mở để cài thêm gói apt trên VM1, chạy: sudo systemctl stop thmd-lab-guard (cài xong bật lại bằng start).",
            ],
            [
                "4. Máy thật Windows bị đầy RAM khi bật đồng thời 4 VM",
                "Ollama trên VM3 đang nạp mô hình LLM quá lớn (> 7B) hoặc mở nhiều ứng dụng nặng trên Windows.",
                "Dùng mô hình nhẹ qwen2.5:3b (mặc định) hoặc chạy chế độ siêu nhẹ USE_LLM=0 (RAG + WSTG Regex chỉ tốn < 150 MB RAM).",
            ],
            [
                "5. Cửa sổ máy ảo bị nhỏ, không tự co giãn theo màn hình",
                "Dịch vụ open-vm-tools-desktop chưa khởi chạy ở chế độ Live tối giản.",
                "Trong VMware chọn View -> Fit Guest Now, hoặc chạy: sudo systemctl restart open-vm-tools.",
            ],
            [
                "6. Lỗi 'Virtualized Intel VT-x/EPT is not supported'",
                "Chưa bật ảo hóa trong BIOS hoặc xung đột với Hyper-V / Virtualization Based Security trên Windows 11.",
                "Bật Intel VT-x / AMD SVM trong BIOS; trong VMware bỏ tích 'Virtualize Intel VT-x/EPT or AMD-V/RVI' nếu máy ảo không chạy KVM lồng nhau.",
            ],
        ],
    )

    for out_p in out_docx_paths:
        out_p.parent.mkdir(parents=True, exist_ok=True)
        try:
            doc.save(str(out_p))
            print(f"[VMware Guide Builder] Saved Word manual: {out_p} ({out_p.stat().st_size:,} bytes)")
        except PermissionError:
            print(f"[VMware Guide Builder] Skipped locked file (currently open in Word): {out_p}")


def main():
    root = Path(__file__).resolve().parent.parent
    artifact_dir = Path(r"C:\Users\asust\.gemini\antigravity\brain\0efdaf13-f2bc-4a66-81d1-4477922186a8")
    docs_mockups = root / "docs" / "ui-mockups"
    fonts = load_fonts()

    render_vmware_guide_1_network_editor(
        fonts,
        [docs_mockups / "vmware_guide_1_virtual_network_editor.png", artifact_dir / "vmware_guide_1_virtual_network_editor.png"],
    )
    render_vmware_guide_2_new_vm_wizard(
        fonts,
        [docs_mockups / "vmware_guide_2_new_vm_wizard.png", artifact_dir / "vmware_guide_2_new_vm_wizard.png"],
    )
    render_vmware_guide_3_commands(
        fonts,
        [docs_mockups / "vmware_guide_3_end_to_end_commands.png", artifact_dir / "vmware_guide_3_end_to_end_commands.png"],
    )

    build_vmware_manual_docx(
        root,
        docs_mockups,
        artifact_dir,
        [
            root / "HUONG-DAN-CAI-DAT-VA-CAU-HINH-TREN-VMWARE-TU-A-DEN-Z.docx",
            root / "docs" / "HUONG-DAN-CAI-DAT-VA-CAU-HINH-TREN-VMWARE-TU-A-DEN-Z.docx",
        ],
    )


if __name__ == "__main__":
    main()

