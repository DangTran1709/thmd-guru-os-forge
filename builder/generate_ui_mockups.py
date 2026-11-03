#!/usr/bin/env python3
"""
THMD-Guru Linux 1.0 (Genesis) — Professional Linux GUI & CLI/TUI Design Mockup Renderer
Generates 4 high-resolution (1600x1000) visual UI/CLI illustrations for:
  1. ui_mockup_1_design_system.png   : Design System 2.0 (WCAG AAA Contrast, Palette, Typography, Before/After)
  2. ui_mockup_2_desktop_gui.png     : THMD-Guru Desktop (KDE Plasma + THMD-guru-ai Welcome Studio 2.0 GUI)
  3. ui_mockup_3_attt_tactical_gui.png: THMD-Guru ATTT (XFCE4 Tactical OPSEC HUD + ZAP AI-RAG Live Triage)
  4. ui_mockup_4_cli_tui_cockpit.png : THMD-guru-ai CLI 2.0 & Server Terminal TUI Dashboard
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H = 1600, 1000

# Color Tokens (THMD-Guru Design System 2.0)
BG_INK = (10, 15, 30)          # #0A0F1E Obsidian Ink (Surface 0)
BG_NAVY = (12, 24, 48)         # #0C1830 Deep Navy (Surface 1)
BG_CARD = (17, 34, 68)         # #112244 Elevated Card (Surface 2)
BG_CARD_ALT = (22, 43, 84)     # #162B54 Hover/Active Card (Surface 3)
SAPPHIRE_OLD = (11, 61, 145)   # #0B3D91 Original Sapphire (Great for fills, low contrast for text)
SAPPHIRE_TEXT = (96, 165, 250) # #60A5FA WCAG AAA Readable Blue on Dark (7.4:1 contrast)
CYAN_ACCENT = (56, 189, 248)   # #38BDF8 Cyber Cyan
GOLD_ROYAL = (212, 175, 55)    # #D4AF37 Royal Gold (Primary Brand Accent)
GOLD_BRIGHT = (245, 215, 122)  # #F5D77A Luminous Gold (Headings & Highlights)
TEXT_PRIMARY = (230, 236, 247) # #E6ECF7 Ice White
TEXT_MUTED = (148, 163, 184)   # #94A3B8 Slate Muted
BORDER_SUBTLE = (35, 65, 120)  # #234178 Structural Hairline
GREEN_OK = (16, 185, 129)      # #10B981 Emerald Verified TP / Active
AMBER_WARN = (245, 158, 11)    # #F59E0B Amber Warning / Medium
RED_DANGER = (239, 68, 68)     # #EF4444 Crimson Alert / High Risk
PURPLE_AI = (168, 85, 247)     # #A855F7 AI/RAG Neural Accent


def load_fonts():
    win_fonts = Path(r"C:\Windows\Fonts")
    def f(names, size):
        for n in names:
            p = win_fonts / n
            if p.exists():
                return ImageFont.truetype(str(p), size)
        return ImageFont.load_default()

    return {
        "h1": f(["segoeuib.ttf", "arialbd.ttf"], 30),
        "h2": f(["segoeuib.ttf", "arialbd.ttf"], 22),
        "h3": f(["segoeuib.ttf", "arialbd.ttf"], 18),
        "body": f(["segoeui.ttf", "arial.ttf"], 16),
        "body_b": f(["segoeuib.ttf", "arialbd.ttf"], 16),
        "small": f(["segoeui.ttf", "arial.ttf"], 14),
        "small_b": f(["segoeuib.ttf", "arialbd.ttf"], 14),
        "mono_lg": f(["consolab.ttf", "courbd.ttf"], 18),
        "mono": f(["consola.ttf", "cour.ttf"], 15),
        "mono_b": f(["consolab.ttf", "courbd.ttf"], 15),
        "mono_sm": f(["consola.ttf", "cour.ttf"], 13),
    }


def draw_rounded_card(draw: ImageDraw.ImageDraw, box, fill=BG_CARD, outline=BORDER_SUBTLE, width=2, radius=12):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def draw_badge(draw: ImageDraw.ImageDraw, x: int, y: int, text: str, bg_color, fg_color, font) -> int:
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    pad_x, pad_y = 10, 4
    w = tw + pad_x * 2
    h = th + pad_y * 2 + 2
    draw.rounded_rectangle((x, y, x + w, y + h), radius=6, fill=bg_color)
    draw.text((x + pad_x, y + pad_y - 1), text, fill=fg_color, font=font)
    return w


def draw_progress_bar(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, pct: float, fg_color, bg_color=(10, 18, 36)):
    draw.rounded_rectangle((x, y, x + w, y + h), radius=h // 2, fill=bg_color, outline=BORDER_SUBTLE, width=1)
    fill_w = max(h, int(w * max(0.0, min(1.0, pct))))
    if pct > 0:
        draw.rounded_rectangle((x, y, x + fill_w, y + h), radius=h // 2, fill=fg_color)


def render_mockup_1_design_system(fonts, out_paths: list[Path]):
    """1. Design System 2.0: Before/After WCAG Contrast Audit, Color Hierarchy & UI Components."""
    img = Image.new("RGB", (W, H), BG_INK)
    d = ImageDraw.Draw(img)

    # Top Header Banner
    d.rectangle((0, 0, W, 76), fill=BG_NAVY)
    d.line((0, 76, W, 76), fill=GOLD_ROYAL, width=2)
    d.text((32, 16), "THMD-GURU LINUX — HỆ THỐNG THIẾT KẾ (DESIGN SYSTEM 2.0: CYBER SAPPHIRE & ROYAL GOLD)", fill=GOLD_BRIGHT, font=fonts["h2"])
    d.text((32, 46), "Phản biện & Chuẩn hóa Thị giác từ Chuyên gia Thiết kế HĐH Linux (WCAG 2.1 AAA Contrast, Semantic Tokens & Ergonomics)", fill=TEXT_PRIMARY, font=fonts["body"])
    draw_badge(d, W - 240, 24, "WCAG 2.1 AAA VERIFIED", GREEN_OK, BG_INK, fonts["small_b"])

    # Section 1 (Left Top): BEFORE vs AFTER Contrast Critique
    draw_rounded_card(d, (32, 100, 780, 490), fill=BG_NAVY, outline=GOLD_ROYAL, width=2)
    d.text((52, 118), "1. PHẢN BIỆN ĐỘ TƯƠNG PHẢN MÀU SẮC (BEFORE vs. AFTER)", fill=GOLD_BRIGHT, font=fonts["h3"])

    # Before Box (Bad contrast)
    draw_rounded_card(d, (52, 158, 760, 295), fill=(10, 15, 30), outline=RED_DANGER, width=2)
    draw_badge(d, 68, 172, "TRƯỚC KHI SỬA (LỖI TƯƠNG PHẢN 2.1:1 - FAIL WCAG)", RED_DANGER, TEXT_PRIMARY, fonts["small_b"])
    d.text((68, 208), "• Trong ThmdGuru.colorscheme & CLI cũ: Dùng trực tiếp mã #0B3D91 (RGB 11,61,145)", fill=TEXT_PRIMARY, font=fonts["body"])
    d.text((68, 232), "  làm màu chữ ANSI Blue (Color4) trên nền tối #0A0F1E -> Chữ bị chìm, gây mỏi mắt:", fill=TEXT_MUTED, font=fonts["small"])
    d.rectangle((68, 256, 740, 284), fill=(10, 15, 30), outline=BORDER_SUBTLE)
    d.text((80, 261), "root@guru-server:~# ls -la /etc/sysctl.d/91-server.conf  [Chữ #0B3D91 tối mờ]", fill=SAPPHIRE_OLD, font=fonts["mono_b"])

    # After Box (Fixed contrast)
    draw_rounded_card(d, (52, 312, 760, 470), fill=(10, 15, 30), outline=GREEN_OK, width=2)
    draw_badge(d, 68, 326, "SAU KHI CHUẨN HÓA (TƯƠNG PHẢN 7.4:1 - PASS WCAG AAA)", GREEN_OK, BG_INK, fonts["small_b"])
    d.text((68, 362), "• Tách biệt rõ: #0B3D91 chỉ dùng làm NỀN (Surface Fill/Banner), còn chữ/icon", fill=TEXT_PRIMARY, font=fonts["body"])
    d.text((68, 386), "  dùng Sky Sapphire #60A5FA (RGB 96,165,250) & Luminous Gold #F5D77A (11.8:1):", fill=TEXT_MUTED, font=fonts["small"])
    d.rectangle((68, 412, 740, 452), fill=(10, 15, 30), outline=SAPPHIRE_TEXT)
    d.text((80, 422), "root@THMD-guru-ai:~# THMD-guru-ai lab run nckh-zap-rag   [Sắc nét 7.4:1]", fill=SAPPHIRE_TEXT, font=fonts["mono_b"])

    # Section 2 (Right Top): 4-Tier Semantic Surface & Accent Token Architecture
    draw_rounded_card(d, (808, 100, 1568, 490), fill=BG_NAVY, outline=BORDER_SUBTLE, width=2)
    d.text((828, 118), "2. BẢNG MÀU NGỮ NGHĨA 4 TẦNG (SEMANTIC COLOR TOKENS)", fill=GOLD_BRIGHT, font=fonts["h3"])

    swatches = [
        ("Surface-0 (Ink)", "#0A0F1E", BG_INK, TEXT_PRIMARY, "Nền chính Terminal / IDE"),
        ("Surface-1 (Navy)", "#0C1830", BG_NAVY, TEXT_PRIMARY, "Nền cửa sổ ứng dụng / Panel"),
        ("Surface-2 (Card)", "#112244", BG_CARD, TEXT_PRIMARY, "Thẻ thông tin / Khung Module"),
        ("Brand Fill", "#0B3D91", SAPPHIRE_OLD, TEXT_PRIMARY, "Nền Header / Nút bấm chính"),
        ("Readable Blue", "#60A5FA", SAPPHIRE_TEXT, BG_INK, "Chữ CLI / Liên kết / Thư mục"),
        ("Royal Gold", "#D4AF37", GOLD_ROYAL, BG_INK, "Viền thương hiệu / Nhấn chính"),
        ("Luminous Gold", "#F5D77A", GOLD_BRIGHT, BG_INK, "Tiêu đề lớn / Con trỏ / Active"),
        ("Verified TP", "#10B981", GREEN_OK, BG_INK, "An toàn / True Positive / PASS"),
        ("Amber Warn", "#F59E0B", AMBER_WARN, BG_INK, "Cảnh báo / Medium Severity"),
        ("Crimson Risk", "#EF4444", RED_DANGER, TEXT_PRIMARY, "Lỗ hổng Critical / Blocked"),
    ]
    for idx, (name, hex_code, rgb, fg, desc) in enumerate(swatches):
        col = idx % 2
        row = idx // 2
        sx = 828 + col * 364
        sy = 158 + row * 64
        draw_rounded_card(d, (sx, sy, sx + 348, sy + 54), fill=BG_CARD, outline=BORDER_SUBTLE, width=1, radius=8)
        d.rounded_rectangle((sx + 8, sy + 8, sx + 96, sy + 46), radius=6, fill=rgb, outline=TEXT_MUTED if rgb == BG_INK else rgb)
        d.text((sx + 16, sy + 18), hex_code, fill=fg, font=fonts["mono_sm"])
        d.text((sx + 108, sy + 8), name, fill=TEXT_PRIMARY, font=fonts["body_b"])
        d.text((sx + 108, sy + 29), desc, fill=TEXT_MUTED, font=fonts["small"])

    # Section 3 (Bottom Full Width): Architectural Critique of 3 Editions (GUI & CLI Unification)
    draw_rounded_card(d, (32, 514, 1568, 968), fill=BG_NAVY, outline=GOLD_ROYAL, width=2)
    d.text((52, 534), "3. MA TRẬN CẢI TIẾN GIAO DIỆN CHO CẢ 3 PHIÊN BẢN (DESKTOP • ATTT • SERVER)", fill=GOLD_BRIGHT, font=fonts["h3"])

    cols = [
        (
            "A. THMD-GURU DESKTOP (KDE Plasma)",
            SAPPHIRE_TEXT,
            [
                "• Phản biện cũ: App 'guru-welcome' dùng Gtk.Frame",
                "  mặc định trông giống ứng dụng thập niên 2000,",
                "  thiếu thanh điều hướng và thiếu trạng thái Lab.",
                "• Giải pháp 2.0 (Xem Hình minh họa số 2):",
                "  - Áp dụng Gtk.HeaderBar + Sidebar Navigation",
                "    với CSS Dark Sapphire (#0A0F1E / #112244).",
                "  - Bổ sung Dashboard trực quan cho Phòng Lab",
                "    NCKH (ZAP + AI + RAG) & Sơ đồ 3-VM VMware.",
                "  - Thanh Top Panel hiển thị chỉ số nén RAM zram,",
                "    trạng thái GPU/Ollama và bộ gõ IBus-Unikey.",
            ],
        ),
        (
            "B. THMD-GURU ATTT (XFCE4 Tactical)",
            GREEN_OK,
            [
                "• Phản biện cũ: XFCE4 mặc định không hiển thị",
                "  trạng thái OPSEC (chuyên gia không biết máy",
                "  đang bật hay tắt ẩn danh MAC/IPv6 hay Sandbox).",
                "• Giải pháp 2.0 (Xem Hình minh họa số 3):",
                "  - Thiết kế 'Tactical OPSEC Telemetry Bar' luôn",
                "    hiển thị: [STEALTH: ON] [SANDBOX: FAIL-CLOSED]",
                "    [MITRE AUDITD: ACTIVE] [VM1: 192.168.80.10].",
                "  - Giao diện chia đôi (Split-Tiling) cho luồng",
                "    xác minh cảnh báo OWASP ZAP bằng AI + RAG,",
                "    tách màu rõ VERIFIED TP và FILTERED FP.",
            ],
        ),
        (
            "C. THMD-GURU SERVER & CLI (TUI Cockpit)",
            GOLD_BRIGHT,
            [
                "• Phản biện cũ: Lệnh CLI chỉ in chữ phẳng một màu,",
                "  khó đọc nhanh mức tải CPU/RAM và trạng thái",
                "  định tuyến giữa các phân vùng mạng VMware.",
                "• Giải pháp 2.0 (Xem Hình minh họa số 4):",
                "  - Nâng cấp 'THMD-guru-ai status' & 'tui' với",
                "    khung Box-Drawing (┌─┐│└─┘) và thanh đo",
                "    tài nguyên trực quan (Progress Bar).",
                "  - Hiển thị sơ đồ kết nối 3-VM / 4-VM VMware",
                "    và bảng kết quả Precision/Recall/F1/NDCG@5",
                "    ngay trên màn hình SSH không cần GUI.",
            ],
        ),
    ]

    for i, (title, accent, lines) in enumerate(cols):
        cx = 52 + i * 504
        cy = 576
        draw_rounded_card(d, (cx, cy, cx + 484, 944), fill=BG_CARD, outline=accent, width=2)
        d.rectangle((cx, cy, cx + 484, cy + 44), fill=SAPPHIRE_OLD)
        d.text((cx + 18, cy + 10), title, fill=GOLD_BRIGHT if accent == GOLD_BRIGHT else TEXT_PRIMARY, font=fonts["body_b"])
        ty = cy + 60
        for ln in lines:
            is_bullet = ln.startswith("•")
            d.text((cx + 18, ty), ln, fill=GOLD_BRIGHT if is_bullet else TEXT_PRIMARY, font=fonts["body_b"] if is_bullet else fonts["body"])
            ty += 28

    for p in out_paths:
        p.parent.mkdir(parents=True, exist_ok=True)
        img.save(p, "PNG")


def render_mockup_2_desktop_gui(fonts, out_paths: list[Path]):
    """2. THMD-Guru Desktop GUI: KDE Plasma Wayland + THMD-guru-ai Welcome & NCKH Studio 2.0."""
    img = Image.new("RGB", (W, H), (8, 14, 28))
    d = ImageDraw.Draw(img)

    # Background subtle geometric grid
    for gx in range(0, W, 80):
        d.line((gx, 0, gx, H), fill=(14, 26, 52), width=1)
    for gy in range(0, H, 80):
        d.line((0, gy, W, gy), fill=(14, 26, 52), width=1)

    # Top KDE Plasma Panel (Translucent Dark Bar)
    d.rectangle((0, 0, W, 38), fill=(7, 16, 34))
    d.line((0, 38, W, 38), fill=GOLD_ROYAL, width=1)
    draw_badge(d, 12, 6, "◆ THMD-GURU", GOLD_ROYAL, BG_INK, fonts["small_b"])
    d.text((135, 9), "Workspaces:  [ 1: Code & AI ]   [ 2: NCKH Lab ]   [ 3: VMware Range ]", fill=TEXT_PRIMARY, font=fonts["small_b"])
    draw_badge(d, W - 560, 6, "VM3: 192.168.80.30 (AI-RAG)", BG_CARD_ALT, CYAN_ACCENT, fonts["small_b"])
    draw_badge(d, W - 335, 6, "ZRAM: 1.8/5.5 GB", BG_CARD, GREEN_OK, fonts["small_b"])
    draw_badge(d, W - 190, 6, "VN: Unikey (VI)", SAPPHIRE_OLD, GOLD_BRIGHT, fonts["small_b"])
    d.text((W - 65, 9), "22:45", fill=TEXT_PRIMARY, font=fonts["small_b"])

    # Main Window: THMD-guru-ai Welcome & NCKH Research Studio 2.0
    win_box = (90, 68, 1510, 910)
    draw_rounded_card(d, win_box, fill=BG_INK, outline=GOLD_ROYAL, width=2, radius=14)

    # Window Titlebar (GTK HeaderBar)
    d.rounded_rectangle((90, 68, 1510, 118), radius=14, fill=BG_NAVY)
    d.rectangle((90, 100, 1510, 118), fill=BG_NAVY)
    d.line((90, 118, 1510, 118), fill=BORDER_SUBTLE, width=1)
    d.text((116, 82), "◆ THMD-guru-ai Welcome & NCKH Studio 2.0 — Global Tech Academy", fill=GOLD_BRIGHT, font=fonts["h3"])
    for idx, col in enumerate([GREEN_OK, AMBER_WARN, RED_DANGER]):
        cx = 1430 + idx * 24
        d.ellipse((cx, 86, cx + 14, 100), fill=col)

    # Left Sidebar Navigation
    d.rectangle((92, 119, 360, 908), fill=(9, 18, 38))
    d.line((360, 119, 360, 908), fill=BORDER_SUBTLE, width=1)
    d.text((112, 138), "ĐIỀU HƯỚNG HỆ THỐNG", fill=TEXT_MUTED, font=fonts["small_b"])

    nav_items = [
        ("[01] Tổng quan & Trạng thái", False),
        ("[02] Phòng Lab NCKH (ZAP+RAG)", True),
        ("[03] Sơ đồ 3-VM VMware", False),
        ("[04] Cấu hình Local LLM & GPU", False),
        ("[05] Môi trường Dev (uv/fnm)", False),
        ("[06] Kho vũ khí ATTT & Kernel", False),
    ]
    for idx, (label, active) in enumerate(nav_items):
        ny = 172 + idx * 54
        if active:
            draw_rounded_card(d, (106, ny, 348, ny + 44), fill=SAPPHIRE_OLD, outline=GOLD_ROYAL, width=2, radius=8)
            d.text((118, ny + 11), label, fill=GOLD_BRIGHT, font=fonts["small_b"])
        else:
            d.text((118, ny + 11), label, fill=TEXT_PRIMARY, font=fonts["body"])

    # Sidebar Footer Card
    draw_rounded_card(d, (108, 760, 344, 890), fill=BG_CARD, outline=BORDER_SUBTLE, width=1, radius=10)
    d.text((122, 774), "KERNEL AI TUNING", fill=GOLD_BRIGHT, font=fonts["small_b"])
    d.text((122, 798), "vm.max_map_count:", fill=TEXT_MUTED, font=fonts["small"])
    d.text((122, 818), "1,048,576 (Qdrant Ready)", fill=GREEN_OK, font=fonts["mono_b"])
    d.text((122, 844), "open-vm-tools: ACTIVE", fill=SAPPHIRE_TEXT, font=fonts["mono_sm"])
    d.text((122, 864), "MITRE Auditd : ENFORCED", fill=GREEN_OK, font=fonts["mono_sm"])

    # Main Content Area (Right of Sidebar)
    draw_rounded_card(d, (384, 136, 1486, 250), fill=SAPPHIRE_OLD, outline=GOLD_ROYAL, width=2, radius=12)
    d.text((408, 152), "ĐỀ TÀI NCKH: AI KẾT HỢP HYBRID RAG XÁC MINH & ƯU TIÊN CẢNH BÁO TỪ OWASP ZAP", fill=GOLD_BRIGHT, font=fonts["h3"])
    d.text((408, 182), "Mô hình 3 Máy ảo trên VMware (Host 16GB RAM | 6 Core) • Tự động lọc False Positive & Xếp hạng P1/P2/P3", fill=TEXT_PRIMARY, font=fonts["body"])
    draw_badge(d, 408, 212, "► Chạy Thực Nghiệm (THMD-guru-ai lab run nckh-zap-rag)", GOLD_ROYAL, BG_INK, fonts["body_b"])
    draw_badge(d, 916, 212, "❖ Xuất Báo Cáo CSV / LaTeX", BG_INK, GOLD_BRIGHT, fonts["body_b"])
    draw_badge(d, 1190, 212, "● Mở Dashboard :8000", GREEN_OK, BG_INK, fonts["body_b"])

    # 3-VM Topology Status Cards (Row 2)
    d.text((384, 268), "TRẠNG THÁI 3 MÁY ẢO TRÊN MẠNG VMWARE (VMnet2: 192.168.80.0/24 — TỔNG RAM: 10.5 / 16.0 GB)", fill=GOLD_BRIGHT, font=fonts["body_b"])

    vms = [
        ("VM 1: THMD-Guru ATTT", "192.168.80.10", "2 vCPU | 2.5 GB RAM", "OWASP ZAP Daemon :8090", "Đã gửi 10 Raw Alerts + Evidence", CYAN_ACCENT),
        ("VM 2: THMD-Guru Server", "192.168.80.20", "2 vCPU | 2.5 GB RAM", "nftables + Nginx + Targets", "DVWA, Juice Shop :3000 ONLINE", GREEN_OK),
        ("VM 3: THMD-Guru Desktop", "192.168.80.30", "2 vCPU | 5.5 GB RAM", "FastAPI + Qdrant + Ollama", "RAG Knowledge: OWASP/CWE/WSTG", PURPLE_AI),
    ]
    for idx, (vtitle, vip, vspec, vrole, vstat, vaccent) in enumerate(vms):
        vx = 384 + idx * 372
        vy = 298
        draw_rounded_card(d, (vx, vy, vx + 356, vy + 168), fill=BG_CARD, outline=vaccent, width=2, radius=10)
        d.text((vx + 16, vy + 14), vtitle, fill=TEXT_PRIMARY, font=fonts["body_b"])
        draw_badge(d, vx + 220, vy + 12, vip, BG_INK, vaccent, fonts["mono_sm"])
        d.text((vx + 16, vy + 46), f"Cấu hình : {vspec}", fill=TEXT_MUTED, font=fonts["small"])
        d.text((vx + 16, vy + 68), f"Dịch vụ  : {vrole}", fill=TEXT_PRIMARY, font=fonts["small_b"])
        d.line((vx + 16, vy + 98, vx + 340, vy + 98), fill=BORDER_SUBTLE, width=1)
        d.text((vx + 16, vy + 110), vstat, fill=GREEN_OK, font=fonts["small_b"])
        draw_badge(d, vx + 16, vy + 134, "CONNECTED (0.4ms)", (12, 45, 38), GREEN_OK, fonts["mono_sm"])

    # Quantitative Benchmark Comparison Panel (Bottom Left of Content)
    draw_rounded_card(d, (384, 486, 980, 890), fill=BG_CARD, outline=BORDER_SUBTLE, width=2, radius=10)
    d.text((404, 504), "KẾT QUẢ ĐỐI CHỨNG KHOA HỌC (ABLATION BENCHMARK)", fill=GOLD_BRIGHT, font=fonts["body_b"])

    metrics_rows = [
        ("1. Baseline: OWASP ZAP thuần", 0.50, 0.667, 0.00, 0.6453, AMBER_WARN),
        ("2. Baseline: LLM Zero-Shot (Không RAG)", 0.714, 0.833, 0.60, 0.8189, SAPPHIRE_TEXT),
        ("3. Đề xuất: THMD-guru-ai + Hybrid RAG", 1.00, 1.00, 1.00, 1.0000, GREEN_OK),
    ]
    ry = 544
    for mname, prec, f1, fprr, ndcg, col in metrics_rows:
        draw_rounded_card(d, (404, ry, 960, ry + 102), fill=BG_NAVY, outline=BORDER_SUBTLE, width=1, radius=8)
        d.text((418, ry + 10), mname, fill=TEXT_PRIMARY, font=fonts["body_b"])
        d.text((418, ry + 38), f"Precision: {prec*100:.1f}% | F1: {f1*100:.1f}% | FPRR: {fprr*100:.0f}% | NDCG@5: {ndcg:.4f}", fill=col, font=fonts["mono_sm"])
        draw_progress_bar(d, 418, ry + 68, 520, 16, f1, col)
        ry += 112

    # Right Bottom: Prioritized Alerts Table (P1 / P2 / Filtered FP)
    draw_rounded_card(d, (1000, 486, 1486, 890), fill=BG_CARD, outline=BORDER_SUBTLE, width=2, radius=10)
    d.text((1020, 504), "HÀNG ĐỢI ƯU TIÊN CẢNH BÁO (RAG VERIFIED)", fill=GOLD_BRIGHT, font=fonts["body_b"])

    queue = [
        ("P1", "ZAP-001: SQL Injection (/rest/user/login)", "CWE-89  | Score: 9.65 | VERIFIED TP", RED_DANGER),
        ("P1", "ZAP-006: SSRF Internal Loopback (:3000)", "CWE-918 | Score: 9.34 | VERIFIED TP", RED_DANGER),
        ("P1", "ZAP-003: Broken Access Control (IDOR)", "CWE-639 | Score: 9.13 | VERIFIED TP", AMBER_WARN),
        ("P2", "ZAP-008: FTP Poison Null Byte (.bak)", "CWE-200 | Score: 8.51 | VERIFIED TP", AMBER_WARN),
        ("P2", "ZAP-004: DOM XSS (search?q=<iframe...)", "CWE-79  | Score: 8.44 | VERIFIED TP", AMBER_WARN),
        ("FP", "ZAP-002: HTTP 500 JSON Type Error", "CWE-89  | Score: 4.90 | FILTERED FP", TEXT_MUTED),
        ("FP", "ZAP-005: HTML-Encoded Entity (&lt;)", "CWE-79  | Score: 4.09 | FILTERED FP", TEXT_MUTED),
    ]
    qy = 544
    for prio, title, sub, pcol in queue:
        draw_rounded_card(d, (1020, qy, 1468, qy + 44), fill=BG_NAVY, outline=BORDER_SUBTLE, width=1, radius=6)
        draw_badge(d, 1028, qy + 8, prio, pcol, BG_INK if pcol != RED_DANGER else TEXT_PRIMARY, fonts["mono_b"])
        d.text((1078, qy + 5), title, fill=TEXT_PRIMARY if prio != "FP" else TEXT_MUTED, font=fonts["small_b"])
        d.text((1078, qy + 23), sub, fill=GREEN_OK if prio != "FP" else TEXT_MUTED, font=fonts["mono_sm"])
        qy += 48

    # Bottom Dock
    draw_rounded_card(d, (470, 932, 1130, 986), fill=BG_NAVY, outline=GOLD_ROYAL, width=2, radius=16)
    d.text((500, 948), "[>_] Terminal    [●] Firefox    [◆] NCKH Studio    [▲] ZAP Proxy    [■] Podman    [⚙] Settings", fill=TEXT_PRIMARY, font=fonts["body_b"])

    for p in out_paths:
        p.parent.mkdir(parents=True, exist_ok=True)
        img.save(p, "PNG")


def render_mockup_3_attt_tactical_gui(fonts, out_paths: list[Path]):
    """3. THMD-Guru ATTT (XFCE4 Tactical Security HUD: OPSEC Bar + Split Tiling ZAP & Sandbox)."""
    img = Image.new("RGB", (W, H), BG_INK)
    d = ImageDraw.Draw(img)

    # Tactical Top HUD Bar (OPSEC & Telemetry Bar)
    d.rectangle((0, 0, W, 56), fill=(6, 13, 26))
    d.line((0, 56, W, 56), fill=GOLD_ROYAL, width=2)
    draw_badge(d, 16, 12, "◆ THMD-GURU ATTT [TACTICAL XFCE4]", SAPPHIRE_OLD, GOLD_BRIGHT, fonts["body_b"])
    draw_badge(d, 356, 14, "STEALTH: ON (MAC 02:9F:4A:81:C3:10 | IPv6 OFF)", (12, 52, 40), GREEN_OK, fonts["mono_b"])
    draw_badge(d, 818, 14, "SANDBOX: FAIL-CLOSED (Firejail)", (18, 40, 76), CYAN_ACCENT, fonts["mono_b"])
    draw_badge(d, 1140, 14, "AUDITD: MITRE ATT&CK (18 Rules)", (56, 36, 12), GOLD_BRIGHT, fonts["mono_b"])
    draw_badge(d, 1455, 14, "VM1: .80.10", RED_DANGER, TEXT_PRIMARY, fonts["mono_b"])

    # Left Tiling Window: OWASP ZAP Scanner + Evidence Extractor (VM1 -> VM2 -> VM3)
    draw_rounded_card(d, (20, 74, 790, 930), fill=BG_NAVY, outline=CYAN_ACCENT, width=2, radius=10)
    d.rectangle((20, 74, 790, 114), fill=BG_CARD)
    d.text((38, 84), "► WINDOW 1: OWASP ZAP HEADLESS SCANNER & EVIDENCE COLLECTOR (VM1: 192.168.80.10)", fill=CYAN_ACCENT, font=fonts["small_b"])

    term_left = [
        ("root@guru-vm1-scanner:~# ", GOLD_BRIGHT, "THMD-guru-ai vm-node status", TEXT_PRIMARY),
        ("", TEXT_MUTED, "[ OK ] Active Role: scanner-red | NIC: ens33 (192.168.80.10/24)", GREEN_OK),
        ("", TEXT_MUTED, "[ OK ] Target Web Server (VM2): http://192.168.80.20:3000 (OWASP Juice Shop)", SAPPHIRE_TEXT),
        ("", TEXT_MUTED, "[ OK ] AI-RAG Verifier (VM3)  : http://192.168.80.30:8000/api/verify", SAPPHIRE_TEXT),
        ("", TEXT_MUTED, "", TEXT_MUTED),
        ("root@guru-vm1-scanner:~# ", GOLD_BRIGHT, "THMD-guru-ai arsenal run zap-baseline -t http://192.168.80.20:3000", TEXT_PRIMARY),
        ("", TEXT_MUTED, "[THMD-guru-ai Sandbox] Enforcing Firejail + Seccomp-BPF isolation...", CYAN_ACCENT),
        ("", TEXT_MUTED, "[ZAP-Spider] Crawled 42 endpoints on 192.168.80.20:3000 (OpenAPI + SPA routes)", TEXT_PRIMARY),
        ("", TEXT_MUTED, "[ZAP-Active] Testing WSTG-INPV-05 (SQLi), WSTG-INPV-01 (XSS), WSTG-ATHZ-04 (IDOR)", TEXT_PRIMARY),
        ("", TEXT_MUTED, "  ├─ [RAW ALERT #01] High   | CWE-89  | POST /rest/user/login (email=' OR 1=1--)", RED_DANGER),
        ("", TEXT_MUTED, "  ├─ [RAW ALERT #02] High   | CWE-89  | GET  /api/Quantitys/invalid_int (HTTP 500)", AMBER_WARN),
        ("", TEXT_MUTED, "  ├─ [RAW ALERT #03] Medium | CWE-639 | GET  /rest/basket/2 (Cross-user Basket)", RED_DANGER),
        ("", TEXT_MUTED, "  ├─ [RAW ALERT #04] High   | CWE-79  | GET  /#/search?q=<iframe src=javascript:>", RED_DANGER),
        ("", TEXT_MUTED, "  ├─ [RAW ALERT #05] High   | CWE-79  | GET  /api/Products/search (&lt;script&gt;)", AMBER_WARN),
        ("", TEXT_MUTED, "  ├─ [RAW ALERT #06] High   | CWE-918 | POST /profile/image/url (127.0.0.1:3000)", RED_DANGER),
        ("", TEXT_MUTED, "  └─ [RAW ALERT #07..#10]   | CWE-200 / CWE-693 (4 additional alerts captured)", TEXT_MUTED),
        ("", TEXT_MUTED, "", TEXT_MUTED),
        ("root@guru-vm1-scanner:~# ", GOLD_BRIGHT, "Exporting zap_raw_alerts.json + HTTP Evidence -> VM3 (192.168.80.30)", GREEN_OK),
    ]
    ty = 132
    for pfx, pcol, txt, tcol in term_left:
        d.text((38, ty), pfx, fill=pcol, font=fonts["mono_b"])
        px_w = d.textbbox((0, 0), pfx, font=fonts["mono_b"])[2]
        d.text((38 + px_w, ty), txt, fill=tcol, font=fonts["mono"])
        ty += 28

    # Bottom Box inside Left Window: HTTP Evidence Inspector
    draw_rounded_card(d, (38, 660, 772, 912), fill=BG_INK, outline=GOLD_ROYAL, width=1, radius=8)
    d.text((54, 674), "► BẰNG CHỨNG HTTP THỰC TẾ ĐÍNH KÈM (EVIDENCE PAYLOAD SENT TO RAG):", fill=GOLD_BRIGHT, font=fonts["small_b"])
    ev_lines = [
        '{\n  "alert_id": "ZAP-002", "cwe_id": "CWE-89", "zap_risk": "High",',
        '  "url": "http://192.168.80.20:3000/api/Quantitys/invalid_int",',
        '  "attack": "1\'", "status_code": 500,',
        '  "http_evidence": "Internal Server Error: Invalid integer format in JSON parser",',
        '  "rag_wstg_rule": "WSTG-INPV-05: Exclude generic 500 without SQL driver trace",',
        '  "ai_rag_verdict": "FALSE POSITIVE (P_TP = 0.06 -> Filtered out!)"\n}',
    ]
    ey = 706
    for el in ev_lines:
        for sub_line in el.split("\n"):
            col = GREEN_OK if "FALSE POSITIVE" in sub_line else (SAPPHIRE_TEXT if "rag_wstg_rule" in sub_line else TEXT_PRIMARY)
            d.text((54, ey), sub_line, fill=col, font=fonts["mono_sm"])
            ey += 22

    # Right Tiling Window: MITRE ATT&CK Auditd & Fail-Closed Sandbox Monitor
    draw_rounded_card(d, (810, 74, 1580, 930), fill=BG_NAVY, outline=GOLD_ROYAL, width=2, radius=10)
    d.rectangle((810, 74, 1580, 114), fill=BG_CARD)
    d.text((828, 84), "► WINDOW 2: AI + HYBRID RAG VERIFICATION & MITRE ATT&CK TELEMETRY", fill=GOLD_BRIGHT, font=fonts["small_b"])

    # RAG Verification Flowchart Box inside Right Window
    draw_rounded_card(d, (828, 132, 1562, 510), fill=BG_INK, outline=BORDER_SUBTLE, width=1, radius=8)
    d.text((846, 146), "LUỒNG XÁC MINH CẢNH BÁO BẰNG AI + RAG (CHỐNG ẢO GIÁC LLM)", fill=GOLD_BRIGHT, font=fonts["body_b"])

    steps = [
        ("BƯỚC 1: Nhận Alert + Evidence từ ZAP (VM1)", "Trích xuất URL, Param, Attack Payload, HTTP Status & Response Body snippet", CYAN_ACCENT),
        ("BƯỚC 2: Truy hồi Tri thức Lai (Hybrid RAG trên Qdrant/FAISS)", "Khớp mã CWE-ID + Semantic Search tài liệu OWASP WSTG & CVSS v3.1", PURPLE_AI),
        ("BƯỚC 3: Xác minh Bằng chứng HTTP (Context-Grounded LLM)", "Loại bỏ 100% cảnh báo giả (5/5 FP bị lọc: HTML-encoded XSS, SPA 404, 500 JSON)", GREEN_OK),
        ("BƯỚC 4: Tính Điểm Ưu Tiên Động S_priority & Gán Nhãn P1/P2/P3", "S_priority = 0.35*CVSS + 0.45*(10*P_RAG) + 0.20*C_asset  -->  NDCG@5 = 1.0000", GOLD_BRIGHT),
    ]
    sy = 186
    for stitle, sdesc, scol in steps:
        draw_rounded_card(d, (846, sy, 1544, sy + 68), fill=BG_CARD, outline=scol, width=2, radius=8)
        d.text((864, sy + 10), stitle, fill=scol, font=fonts["body_b"])
        d.text((864, sy + 36), sdesc, fill=TEXT_PRIMARY, font=fonts["small"])
        sy += 78

    # Bottom Box inside Right Window: MITRE ATT&CK Kernel Auditd Live Stream
    draw_rounded_card(d, (828, 530, 1562, 912), fill=BG_INK, outline=GREEN_OK, width=1, radius=8)
    d.text((846, 546), "◆ GIÁM SÁT NHÂN LINUX THEO KHUNG MITRE ATT&CK (/etc/audit/rules.d/90-thmd-guru-mitre.rules)", fill=GREEN_OK, font=fonts["small_b"])

    mitre_logs = [
        ("[PASS] T1098 / T1136", "Identity Watch (/etc/passwd, /etc/shadow)", "0 Unauth Writes"),
        ("[PASS] T1548.003", "Sudoers Watch (/etc/sudoers, /etc/sudoers.d/)", "No NOPASSWD"),
        ("[PASS] T1055", "Process Injection Watch (arch=b64 -S ptrace)", "yama.ptrace=2"),
        ("[PASS] T1547.006", "Kernel Module Watch (init_module, finit_module)", "Locked"),
        ("[PASS] T1562.004", "Firewall Rules Watch (/etc/nftables.conf)", "Active & Logged"),
        ("[PASS] CWE-636", "THMD-guru-ai-sandbox Fail-Closed Enforcement", "Exit 126 Safe"),
    ]
    my = 584
    for mtag, mdesc, mstat in mitre_logs:
        draw_rounded_card(d, (846, my, 1544, my + 46), fill=BG_NAVY, outline=BORDER_SUBTLE, width=1, radius=6)
        draw_badge(d, 856, my + 10, mtag, (12, 52, 40), GREEN_OK, fonts["mono_sm"])
        d.text((1030, my + 13), mdesc, fill=TEXT_PRIMARY, font=fonts["small"])
        d.text((1395, my + 13), mstat, fill=GOLD_BRIGHT, font=fonts["mono_sm"])
        my += 52

    # Bottom Status Bar
    d.rectangle((0, 948, W, H), fill=BG_NAVY)
    d.line((0, 948, W, 948), fill=BORDER_SUBTLE, width=1)
    d.text((24, 964), "THMD-Guru Linux 1.0 (Genesis) — ATTT Edition   |   Hotkeys: [Super+Enter] Terminal   [Super+S] Toggle Stealth   [Super+Z] ZAP + RAG Studio", fill=TEXT_MUTED, font=fonts["small_b"])

    for p in out_paths:
        p.parent.mkdir(parents=True, exist_ok=True)
        img.save(p, "PNG")


def render_mockup_4_cli_tui_cockpit(fonts, out_paths: list[Path]):
    """4. THMD-guru-ai CLI 2.0 & Server Terminal TUI Cockpit (Standard Box-Drawing + Progress Gauges)."""
    img = Image.new("RGB", (W, H), BG_INK)
    d = ImageDraw.Draw(img)

    # Top Title Bar
    d.rectangle((0, 0, W, 64), fill=BG_NAVY)
    d.line((0, 64, W, 64), fill=GOLD_ROYAL, width=2)
    d.text((28, 16), "THMD-GURU-AI CLI 2.0 & SERVER TUI COCKPIT — THIẾT KẾ TERMINAL HIỆN ĐẠI (BOX-DRAWING & GAUGES)", fill=GOLD_BRIGHT, font=fonts["h2"])

    # Left Terminal Pane: `THMD-guru-ai info` & `THMD-guru-ai status`
    draw_rounded_card(d, (24, 84, 788, 972), fill=(7, 11, 22), outline=SAPPHIRE_TEXT, width=2, radius=10)
    d.rectangle((24, 84, 788, 122), fill=BG_CARD)
    d.text((42, 93), "TERMINAL 1 — THMD-guru-ai info & status (Thiết kế CLI mới dễ đọc, tương phản cao)", fill=SAPPHIRE_TEXT, font=fonts["small_b"])

    cli_lines = [
        ("root@guru-vm2-server:~# ", GOLD_BRIGHT, "THMD-guru-ai info", TEXT_PRIMARY),
        ("  .====================.   ", GOLD_ROYAL, "root@guru-vm2-server", GOLD_BRIGHT),
        ("  ||  _____   ____    ||   ", GOLD_ROYAL, "────────────────────────────────────────────", SAPPHIRE_TEXT),
        ("  || |_   _| / ___|   ||   ", GOLD_ROYAL, "OS       THMD-Guru Linux 1.0 (Genesis)", TEXT_PRIMARY),
        ("  ||   | |  | |  _    ||   ", GOLD_ROYAL, "Edition  Server (Cloud, NetOps & WAF)", CYAN_ACCENT),
        ("  ||   | |  | |_| |   ||   ", GOLD_ROYAL, "VM Role  vm2-web-target-waf (192.168.80.20)", GREEN_OK),
        ("  ||   |_|   \\____|   ||   ", GOLD_ROYAL, "Kernel   Linux 6.1.0-50-amd64 (BBR + fq)", TEXT_PRIMARY),
        ("   \\\\    G U R U     //    ", GOLD_ROYAL, "CPU      6 vCPU (Host 6C/12T Match 1:1)", TEXT_PRIMARY),
        ("    `\\\\==========//`     ", GOLD_ROYAL, "Memory   412.0 / 2560.0 MiB (16%)", GREEN_OK),
        ("       `\\\\____//`        ", GOLD_ROYAL, "CLI      THMD-guru-ai 1.0.0 (Genesis)", GOLD_BRIGHT),
        ("", TEXT_MUTED, "", TEXT_MUTED),
        ("root@guru-vm2-server:~# ", GOLD_BRIGHT, "THMD-guru-ai status", TEXT_PRIMARY),
        ("┌─ THMD-GURU SYSTEM TELEMETRY & KERNEL HARDENING ──────────────────────┐", SAPPHIRE_TEXT, "", TEXT_MUTED),
        ("│ CPU Load   [██░░░░░░░░░░░░░░░░░░]  12.4%   (0.24, 0.18, 0.12)        │", TEXT_PRIMARY, "", TEXT_MUTED),
        ("│ RAM Usage  [███░░░░░░░░░░░░░░░░░]  16.1%   (412 MiB / 2560 MiB)      │", GREEN_OK, "", TEXT_MUTED),
        ("│ ZRAM Swap  [█░░░░░░░░░░░░░░░░░░░]   4.0%   (zstd 50% compressed)     │", CYAN_ACCENT, "", TEXT_MUTED),
        ("│ Disk /     [████░░░░░░░░░░░░░░░░]  21.5%   (4.3 GiB / 20.0 GiB)      │", TEXT_PRIMARY, "", TEXT_MUTED),
        ("└──────────────────────────────────────────────────────────────────────┘", SAPPHIRE_TEXT, "", TEXT_MUTED),
        ("  [ OK ] kernel.kptr_restrict = 2          (KSPP Pointer Hide)", GREEN_OK, "", TEXT_MUTED),
        ("  [ OK ] net.ipv4.tcp_congestion_control = bbr (Low-Latency WAN)", GREEN_OK, "", TEXT_MUTED),
        ("  [ OK ] vm.max_map_count = 1048576        (Qdrant / LLM Ready)", GREEN_OK, "", TEXT_MUTED),
        ("  [ OK ] open-vm-tools = active            (VMware Time/Guest Sync)", GREEN_OK, "", TEXT_MUTED),
        ("  [ OK ] auditd = 90-thmd-guru-mitre.rules (MITRE ATT&CK Active)", GREEN_OK, "", TEXT_MUTED),
        ("", TEXT_MUTED, "", TEXT_MUTED),
        ("root@guru-vm2-server:~# ", GOLD_BRIGHT, "THMD-guru-ai gpu", TEXT_PRIMARY),
        ("  Adapter          : VMware SVGA II + Host-GPU Bridge (192.168.80.1:11434)", CYAN_ACCENT, "", TEXT_MUTED),
        ("  vm.max_map_count : 1048576 [OK - VectorDB & LLM mmap ready]", GREEN_OK, "", TEXT_MUTED),
    ]
    cy = 140
    for p1, c1, p2, c2 in cli_lines:
        d.text((42, cy), p1, fill=c1, font=fonts["mono_b"])
        w1 = d.textbbox((0, 0), p1, font=fonts["mono_b"])[2]
        if p2:
            d.text((42 + w1, cy), p2, fill=c2, font=fonts["mono"])
        cy += 29

    # Right Terminal Pane: `THMD-guru-ai lab run nckh-zap-rag` & `THMD-guru-ai tui`
    draw_rounded_card(d, (812, 84, 1576, 972), fill=(7, 11, 22), outline=GOLD_ROYAL, width=2, radius=10)
    d.rectangle((812, 84, 1576, 122), fill=BG_CARD)
    d.text((830, 93), "TERMINAL 2 — THMD-guru-ai lab run nckh-zap-rag (Báo cáo Thực nghiệm NCKH trên CLI)", fill=GOLD_BRIGHT, font=fonts["small_b"])

    tui_lines = [
        ("root@guru-vm3-ai-soc:~# ", GOLD_BRIGHT, "THMD-guru-ai lab run nckh-zap-rag", TEXT_PRIMARY),
        ("┌─ NCKH BENCHMARK: AI + HYBRID RAG OWASP ZAP VERIFICATION ─────────────┐", GOLD_ROYAL, "", TEXT_MUTED),
        ("│ Dataset : 10 OWASP ZAP Raw Alerts (Ground Truth: 5 TP, 5 FP)         │", TEXT_PRIMARY, "", TEXT_MUTED),
        ("│ Target  : VM2 (192.168.80.20) -> DVWA & OWASP Juice Shop             │", CYAN_ACCENT, "", TEXT_MUTED),
        ("│ RAG KB  : OWASP Top 10 + CWE + CVSS v3.1 + WSTG Exclusion Rules      │", PURPLE_AI, "", TEXT_MUTED),
        ("└──────────────────────────────────────────────────────────────────────┘", GOLD_ROYAL, "", TEXT_MUTED),
        ("Method / Model                      TP  FP  Precision  Recall     F1   FPRR  NDCG@5", GOLD_BRIGHT, "", TEXT_MUTED),
        ("───────────────────────────────────────────────────────────────────────────────────", BORDER_SUBTLE, "", TEXT_MUTED),
        ("1. Baseline: Raw OWASP ZAP           5   5     50.00%  100.0%  66.7%   0.0%  0.6453", AMBER_WARN, "", TEXT_MUTED),
        ("2. Baseline: LLM Zero-Shot (No RAG)  5   2     71.43%  100.0%  83.3%  60.0%  0.8189", SAPPHIRE_TEXT, "", TEXT_MUTED),
        ("3. Proposed: THMD-guru-ai + RAG      5   0    100.00%  100.0% 100.0% 100.0%  1.0000", GREEN_OK, "", TEXT_MUTED),
        ("", TEXT_MUTED, "", TEXT_MUTED),
        ("┌─ PRIORITIZED ALERT QUEUE (S_priority = 0.35*CVSS + 0.45*P_RAG + 0.20*Asset) ─┐", SAPPHIRE_TEXT, "", TEXT_MUTED),
        ("│ #1 [P1] ZAP-001 | CWE-89  | VERIFIED TP | S=9.65 | SQLi /rest/user/login     │", GREEN_OK, "", TEXT_MUTED),
        ("│ #2 [P1] ZAP-006 | CWE-918 | VERIFIED TP | S=9.34 | SSRF Loopback :3000       │", GREEN_OK, "", TEXT_MUTED),
        ("│ #3 [P1] ZAP-003 | CWE-639 | VERIFIED TP | S=9.13 | IDOR /rest/basket/2       │", GREEN_OK, "", TEXT_MUTED),
        ("│ #4 [P2] ZAP-008 | CWE-200 | VERIFIED TP | S=8.51 | FTP Poison Null Byte      │", GREEN_OK, "", TEXT_MUTED),
        ("│ #5 [P2] ZAP-004 | CWE-79  | VERIFIED TP | S=8.44 | DOM XSS search?q=<iframe> │", GREEN_OK, "", TEXT_MUTED),
        ("├──────────────────────────────────────────────────────────────────────────────┤", BORDER_SUBTLE, "", TEXT_MUTED),
        ("│ #6 [FP] ZAP-002 | CWE-89  | FILTERED FP | S=4.90 | HTTP 500 JSON Type Error  │", TEXT_MUTED, "", TEXT_MUTED),
        ("│ #7 [FP] ZAP-005 | CWE-79  | FILTERED FP | S=4.09 | HTML-Encoded (&lt;script) │", TEXT_MUTED, "", TEXT_MUTED),
        ("│ #8 [FP] ZAP-007 | CWE-200 | FILTERED FP | S=3.90 | Custom 404 SPA Fallback   │", TEXT_MUTED, "", TEXT_MUTED),
        ("│ #9 [FP] ZAP-010 | CWE-200 | FILTERED FP | S=3.20 | Benign MIT JS Comment     │", TEXT_MUTED, "", TEXT_MUTED),
        ("│#10 [FP] ZAP-009 | CWE-693 | FILTERED FP | S=2.17 | Static PNG Missing Header │", TEXT_MUTED, "", TEXT_MUTED),
        ("└──────────────────────────────────────────────────────────────────────────────┘", SAPPHIRE_TEXT, "", TEXT_MUTED),
        ("[ OK ] Exported CSV & LaTeX tables -> ./results/metrics_comparison.csv", GOLD_BRIGHT, "", TEXT_MUTED),
    ]
    ty = 140
    for p1, c1, p2, c2 in tui_lines:
        d.text((830, ty), p1, fill=c1, font=fonts["mono_sm"] if len(p1) > 74 else fonts["mono_b"])
        w1 = d.textbbox((0, 0), p1, font=fonts["mono_b"])[2]
        if p2:
            d.text((830 + w1, ty), p2, fill=c2, font=fonts["mono"])
        ty += 30

    for p in out_paths:
        p.parent.mkdir(parents=True, exist_ok=True)
        img.save(p, "PNG")


def main():
    root = Path(__file__).resolve().parent.parent
    artifact_dir = Path(r"C:\Users\asust\.gemini\antigravity\brain\0efdaf13-f2bc-4a66-81d1-4477922186a8")
    docs_dir = root / "docs" / "ui-mockups"
    fonts = load_fonts()

    render_mockup_1_design_system(
        fonts,
        [artifact_dir / "ui_mockup_1_design_system.png", docs_dir / "ui_mockup_1_design_system.png"],
    )
    render_mockup_2_desktop_gui(
        fonts,
        [artifact_dir / "ui_mockup_2_desktop_gui.png", docs_dir / "ui_mockup_2_desktop_gui.png"],
    )
    render_mockup_3_attt_tactical_gui(
        fonts,
        [artifact_dir / "ui_mockup_3_attt_tactical_gui.png", docs_dir / "ui_mockup_3_attt_tactical_gui.png"],
    )
    render_mockup_4_cli_tui_cockpit(
        fonts,
        [artifact_dir / "ui_mockup_4_cli_tui_cockpit.png", docs_dir / "ui_mockup_4_cli_tui_cockpit.png"],
    )
    print("[UI Mockup Generator] Successfully rendered all 4 high-resolution GUI & CLI mockups!")


if __name__ == "__main__":
    main()
