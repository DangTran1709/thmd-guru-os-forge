#!/usr/bin/env python3
"""
THMD-Guru Modular Catalog & Bundle Builder (builder/build-catalog-bundles.py)
=============================================================================
Populates the decoupled `catalog/` directory (`tools/`, `labs/`, `nckh/`),
packages each on-demand module into a deterministic `.tar.gz` archive under
`out/modules/`, and generates `catalog/index.json` with SHA-256 checksums.
"""

import gzip
import hashlib
import io
import json
import shutil
import tarfile
from pathlib import Path
from typing import Any, Dict, List

ROOT_DIR = Path(__file__).resolve().parent.parent
CATALOG_DIR = ROOT_DIR / "catalog"
OUT_MODULES_DIR = ROOT_DIR / "out" / "modules"
LEGACY_LABS_DIR = ROOT_DIR / "packages" / "guru-cli" / "labs"

MODULES_SPEC: List[Dict[str, Any]] = [
    # --- NHOM 1: TOOLS & UNG DUNG CHUYEN NGANH ---
    {
        "id": "tools/attt-web-scanner",
        "slug": "tools-attt-web-scanner",
        "category": "tools",
        "version": "1.1.0",
        "name": "Bộ công cụ Kiểm thử Web & OWASP ZAP (ATTT Web Scanner)",
        "description": "Cài đặt theo yêu cầu: OWASP ZAP, SQLMap, Nikto, Gobuster, FFUF, curl, jq, Python requests.",
        "packages": ["zaproxy", "sqlmap", "nikto", "gobuster", "ffuf", "curl", "jq", "python3-requests"],
        "roles": ["default", "vm1-zap"],
    },
    {
        "id": "tools/attt-net-recon",
        "slug": "tools-attt-net-recon",
        "category": "tools",
        "version": "1.1.0",
        "name": "Bộ công cụ Chẩn đoán & Phân tích Mạng (Network Recon)",
        "description": "Cài đặt theo yêu cầu: Nmap, Wireshark, Tshark, Tcpdump, MTR, Arp-scan, Iperf3.",
        "packages": ["nmap", "wireshark", "tshark", "tcpdump", "mtr-tiny", "arp-scan", "iperf3", "netcat-openbsd"],
        "roles": ["default"],
    },
    {
        "id": "tools/attt-blue-dfir",
        "slug": "tools-attt-blue-dfir",
        "category": "tools",
        "version": "1.1.0",
        "name": "Bộ công cụ Phòng thủ SOC & Pháp y số (Blue Team & DFIR)",
        "description": "Cài đặt theo yêu cầu: Auditd MITRE ATT&CK, Lynis, Rkhunter, YARA, Sleuthkit, Binwalk, Fail2ban.",
        "packages": ["auditd", "lynis", "rkhunter", "yara", "sleuthkit", "binwalk", "libimage-exiftool-perl", "fail2ban"],
        "roles": ["default"],
    },
    {
        "id": "tools/attt-opsec-sandbox",
        "slug": "tools-attt-opsec-sandbox",
        "category": "tools",
        "version": "1.1.0",
        "name": "Bộ công cụ Cô lập Firejail & Ẩn danh Mạng (OPSEC & Sandbox)",
        "description": "Cài đặt theo yêu cầu: Firejail Fail-Closed Sandbox, Stealth IPv6/mDNS Lockdown, Proxychains4.",
        "packages": ["firejail", "proxychains4", "macchanger", "tor"],
        "roles": ["default"],
    },
    {
        "id": "tools/server-container",
        "slug": "tools-server-container",
        "category": "tools",
        "version": "1.1.0",
        "name": "Hạ tầng Container & Microservices (Docker CE / Podman)",
        "description": "Cài đặt theo yêu cầu: Docker Engine, Docker Compose v2, Podman, Buildah & tối ưu Cgroups v2.",
        "packages": ["docker.io", "docker-compose", "podman", "buildah", "slirp4netns"],
        "roles": ["default", "vm2-target"],
    },
    {
        "id": "tools/server-web-waf",
        "slug": "tools-server-web-waf",
        "category": "tools",
        "version": "1.1.0",
        "name": "Máy chủ Web, Reverse Proxy & Tường lửa (Nginx / WAF / Cockpit)",
        "description": "Cài đặt theo yêu cầu: Nginx, Apache2, ModSecurity CRS, nftables & Cockpit Web UI (:9090).",
        "packages": ["nginx", "nftables", "cockpit", "certbot"],
        "roles": ["default", "vm2-target"],
    },
    {
        "id": "tools/ai-rag-engine",
        "slug": "tools-ai-rag-engine",
        "category": "tools",
        "version": "1.1.0",
        "name": "Hạ tầng Trí tuệ Nhân tạo & Vector DB (FastAPI / FAISS / Ollama)",
        "description": "Cài đặt theo yêu cầu: Python3 venv, FastAPI, Uvicorn, FAISS/Qdrant Vector DB, Sentence-Transformers, Ollama.",
        "packages": ["python3", "python3-venv", "python3-pip", "python3-numpy", "curl", "jq"],
        "roles": ["default", "vm3-airag"],
    },
    {
        "id": "tools/dev-workstation",
        "slug": "tools-dev-workstation",
        "category": "tools",
        "version": "1.1.0",
        "name": "Môi trường Lập trình Đa ngôn ngữ (Polyglot Dev Workstation)",
        "description": "Cài đặt theo yêu cầu: Git, Build-Essential, Python uv, Node.js fnm, Rustup, Go, Tmux, Neovim.",
        "packages": ["git", "build-essential", "golang-go", "tmux", "neovim", "curl", "unzip"],
        "roles": ["default"],
    },
    # --- NHOM 2: PHONG THI NGHIEM THUC HANH (HANDS-ON LABS) ---
    {
        "id": "lab/netops-bgp-sdn",
        "slug": "lab-netops-bgp-sdn",
        "category": "lab",
        "version": "1.1.0",
        "name": "Phòng Lab Định tuyến Doanh nghiệp BGP/OSPF & SDN (FRRouting)",
        "description": "Mô hình 2 Router FRR BGP/OSPF peering tự động trên Docker Compose.",
        "packages": ["docker.io", "docker-compose", "frr", "tcpdump"],
        "roles": ["default"],
        "legacy_lab_alias": "netops-bgp-sdn",
    },
    {
        "id": "lab/webapp-vuln-range",
        "slug": "lab-webapp-vuln-range",
        "category": "lab",
        "version": "1.1.0",
        "name": "Phòng Lab Ứng dụng Web Mục tiêu (DVWA, OWASP Juice Shop, WebGoat)",
        "description": "Triển khai nhanh cụm Web App mục tiêu có lỗ hổng hợp pháp phục vụ đào tạo Pentest & SOC.",
        "packages": ["docker.io", "docker-compose", "nginx", "curl"],
        "roles": ["default", "vm2-target"],
    },
    # --- NHOM 3: DE TAI NGHIEN CUU KHOA HOC (NCKH SUITES) ---
    {
        "id": "nckh/zap-rag-standalone",
        "slug": "nckh-zap-rag-standalone",
        "category": "nckh",
        "version": "1.1.0",
        "name": "Đề tài NCKH (Standalone): AI + Hybrid RAG Xác minh Cảnh báo OWASP ZAP",
        "description": "Bộ dữ liệu chuẩn & kịch bản thực nghiệm 3 phương pháp (Raw ZAP vs Zero-Shot LLM vs Hybrid RAG) trên 1 máy.",
        "packages": ["python3", "curl", "jq"],
        "roles": ["default", "standalone"],
        "legacy_lab_alias": "nckh-zap-rag",
    },
    {
        "id": "nckh/vmware-zap-rag-pfsense",
        "slug": "nckh-vmware-zap-rag-pfsense",
        "category": "nckh",
        "version": "1.1.0",
        "name": "Đề tài NCKH (VMware 3-VM + pfSense): Hệ thống Đánh giá AI-RAG & OWASP ZAP",
        "description": "Hỗ trợ cài phân tách từng máy ảo (--role vm1-zap | vm2-target | vm3-airag | evaluator) trên mạng 192.168.80.0/24.",
        "packages": ["python3", "curl", "jq"],
        "roles": ["all", "vm1-zap", "vm2-target", "vm3-airag", "evaluator", "pfsense"],
        "legacy_lab_alias": "vmware-zap-rag-pfsense",
    },
]


def write_module_install_script(mod_dir: Path, spec: Dict[str, Any]) -> None:
    pkgs_str = " ".join(spec.get("packages", []))
    mod_id = spec["id"]
    script = f"""#!/bin/sh
# THMD-Guru Modular Hub - On-Demand Module Installer
# Module ID : {mod_id}
# Name      : {spec['name']}
# Version   : {spec['version']}
set -eu

ROLE="${{1:-default}}"
INSTALL_ROOT="/opt/thmd-guru/modules/{spec['slug']}"

echo "================================================================================"
echo "  [THMD-Guru Hub] Dang cai dat mo-dun: {mod_id} (v{spec['version']})"
echo "  Vai tro (Role): $ROLE | Thu muc dich: $INSTALL_ROOT"
echo "================================================================================"

if [ "$ mod_id" != "" ] 2>/dev/null || true; then :; fi
"""
    if spec["id"] == "nckh/vmware-zap-rag-pfsense":
        script += """
case "$ROLE" in
    vm1-zap|vm1)
        echo "  -> Cau hinh chuyen biet cho VM1 (192.168.80.10 - OWASP ZAP Scanner)..."
        if [ -f "$INSTALL_ROOT/common/set-static-ip.sh" ]; then
            echo "  -> San sang kich ban IP tinh: sudo bash $INSTALL_ROOT/common/set-static-ip.sh vm1"
        fi
        echo "  -> Kich ban quet ZAP & gui Alert: $INSTALL_ROOT/vm1-kali-zap/zap_scan_and_send.py"
        ;;
    vm2-target|vm2)
        echo "  -> Cau hinh chuyen biet cho VM2 (192.168.80.20 - Web Server Target)..."
        echo "  -> Docker Compose DVWA/JuiceShop/WebGoat: $INSTALL_ROOT/vm2-web-target/docker-compose.yml"
        ;;
    vm3-airag|vm3)
        echo "  -> Cau hinh chuyen biet cho VM3 (192.168.80.30 - AI-RAG Server)..."
        echo "  -> Dich vu FastAPI + Vector DB + LLM: $INSTALL_ROOT/vm3-ai-rag/app.py"
        ;;
    evaluator)
        echo "  -> Cau hinh cong cu danh gia & cham diem NCKH (Precision/Recall/F1/NDCG@5)..."
        echo "  -> Chay danh gia: python3 $INSTALL_ROOT/evaluator/evaluate.py"
        ;;
    *)
        echo "  -> Da cai dat day du bo kich ban 3-VM + pfSense tai: $INSTALL_ROOT"
        ;;
esac
"""
    elif spec["category"] == "tools":
        script += f"""
echo "  -> Danh sach goi thanh phan cua mo-dun: {pkgs_str}"
if [ "${{THMD_HUB_APT:-0}}" = "1" ] && command -v apt-get >/dev/null 2>&1 && [ "$(id -u)" -eq 0 ]; then
    echo "  -> Dang dong bo tu kho APT Debian 12 Bookworm..."
    apt-get update && apt-get install -y --no-install-recommends {pkgs_str} || true
else
    echo "  -> Da kich hoat ho so mo-dun {mod_id} trong /opt/thmd-guru/modules/{spec['slug']}"
    echo "     (De cai them goi nhi phan tu kho Debian APT, chay: sudo THMD_HUB_APT=1 THMD-guru-ai hub install {mod_id})"
fi
"""
    script += f"""
echo "[OK] Hoan tat cai dat mo-dun {mod_id} (Role: $ROLE)!"
"""
    inst_path = mod_dir / "install.sh"
    inst_path.write_text(script, encoding="utf-8", newline="\n")


def populate_catalog_tree() -> None:
    CATALOG_DIR.mkdir(parents=True, exist_ok=True)
    OUT_MODULES_DIR.mkdir(parents=True, exist_ok=True)

    for spec in MODULES_SPEC:
        rel_parts = spec["id"].split("/")
        mod_dir = CATALOG_DIR.joinpath(*rel_parts)
        mod_dir.mkdir(parents=True, exist_ok=True)

        # Copy existing lab/nckh files if mapped from legacy_lab_alias
        legacy_alias = spec.get("legacy_lab_alias")
        if legacy_alias and (LEGACY_LABS_DIR / legacy_alias).exists():
            src_dir = LEGACY_LABS_DIR / legacy_alias
            for item in src_dir.rglob("*"):
                rel = item.relative_to(src_dir)
                target = mod_dir / rel
                if item.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, target)

        # If webapp-vuln-range, copy vm2-web-target docker-compose.yml
        if spec["id"] == "lab/webapp-vuln-range":
            vm2_src = LEGACY_LABS_DIR / "vmware-zap-rag-pfsense" / "vm2-web-target"
            if vm2_src.exists():
                for item in vm2_src.rglob("*"):
                    if item.is_file():
                        target = mod_dir / item.relative_to(vm2_src)
                        target.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(item, target)

        # Write module manifest.json and install.sh
        (mod_dir / "manifest.json").write_text(
            json.dumps(spec, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        write_module_install_script(mod_dir, spec)


def create_deterministic_tar_gz(src_dir: Path, out_tar_gz: Path) -> str:
    buf = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=buf, compresslevel=6, mtime=1793700000) as gz:
        with tarfile.open(mode="w", fileobj=gz, format=tarfile.USTAR_FORMAT) as tf:
            for item in sorted(src_dir.rglob("*")):
                if item.is_file():
                    rel = item.relative_to(src_dir).as_posix()
                    data = item.read_bytes()
                    if rel.endswith((".sh", ".py", ".yml", ".yaml", ".json", ".md", ".conf", ".txt")):
                        data = data.replace(b"\r\n", b"\n")
                    ti = tarfile.TarInfo(name=rel)
                    ti.size = len(data)
                    ti.mtime = 1793700000
                    ti.uid = 0
                    ti.gid = 0
                    ti.uname = "root"
                    ti.gname = "root"
                    ti.mode = 0o755 if rel.endswith((".sh", ".py")) else 0o644
                    tf.addfile(ti, io.BytesIO(data))
    raw_bytes = buf.getvalue()
    out_tar_gz.write_bytes(raw_bytes)
    return hashlib.sha256(raw_bytes).hexdigest()


def build_all_bundles() -> Dict[str, Any]:
    populate_catalog_tree()
    catalog_entries: List[Dict[str, Any]] = []

    for spec in MODULES_SPEC:
        rel_parts = spec["id"].split("/")
        mod_dir = CATALOG_DIR.joinpath(*rel_parts)
        bundle_fname = f"{spec['slug']}.tar.gz"
        bundle_path = OUT_MODULES_DIR / bundle_fname
        sha256_hex = create_deterministic_tar_gz(mod_dir, bundle_path)
        size_bytes = bundle_path.stat().st_size

        entry = {
            **spec,
            "bundle_file": bundle_fname,
            "size_bytes": size_bytes,
            "sha256": sha256_hex,
            "download_url": f"https://github.com/DangTran1709/thmd-guru-os-forge/releases/download/v1.1.0-genesis/{bundle_fname}",
        }
        catalog_entries.append(entry)
        print(f"[Catalog Builder] Packaged {spec['id']:30s} -> {bundle_fname} ({size_bytes:,} bytes | SHA256: {sha256_hex[:12]}...)")

    index_doc = {
        "schema_version": "1.0",
        "catalog_version": "1.1.0",
        "os_compatibility": "THMD-Guru Linux >= 1.0.0 (Debian 12 Bookworm Kernel 6.1 LTS)",
        "repository": "https://github.com/DangTran1709/thmd-guru-os-forge",
        "total_modules": len(catalog_entries),
        "modules": catalog_entries,
    }
    index_json_bytes = (json.dumps(index_doc, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    (CATALOG_DIR / "index.json").write_bytes(index_json_bytes)
    (OUT_MODULES_DIR / "catalog-index.json").write_bytes(index_json_bytes)
    print(f"[Catalog Builder] Wrote catalog/index.json with {len(catalog_entries)} on-demand modules.")
    return index_doc


if __name__ == "__main__":
    build_all_bundles()

