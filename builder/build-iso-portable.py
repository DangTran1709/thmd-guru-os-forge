#!/usr/bin/env python3
"""
THMD-Guru OS Forge — Pure-Python ISO-9660 (ECMA-119) Builder & OEM Installer Generator
Builds real, mountable ISO-9660 images for all 3 editions (Desktop, Server, ATTT)
directly on Windows/Linux/macOS without requiring root or hardware virtualization.
Each ISO includes:
  - /boot/grub/ (GRUB2 bootloader menu & Cyber Sapphire/Gold theme)
  - /pool/ & /dists/ (Compiled THMD-Guru .deb packages & APT repository)
  - /preseed/ (Automated Debian Installer preseed configuration)
  - /thmd-guru/ (Complete edition rootfs overlay, sysctl profiles, hooks, package lists, MOK keys)
  - /install-thmd-guru.sh (1-command installer that converts any Debian 12 system or VM into THMD-Guru Linux)
Owner: os-forge-devops
"""
import datetime
import hashlib
import math
import os
import shutil
import struct
import sys
from pathlib import Path

SECTOR_SIZE = 2048


def pad_sector(data: bytes) -> bytes:
    rem = len(data) % SECTOR_SIZE
    if rem == 0:
        return data
    return data + b"\x00" * (SECTOR_SIZE - rem)


def str_a(text: str, length: int) -> bytes:
    b = text.upper().encode("ascii", errors="replace")[:length]
    return b + b" " * (length - len(b))


def both_16(val: int) -> bytes:
    return struct.pack("<H", val) + struct.pack(">H", val)


def both_32(val: int) -> bytes:
    return struct.pack("<I", val) + struct.pack(">I", val)


def dir_datetime(dt: datetime.datetime) -> bytes:
    return struct.pack(
        "BBBBBBB",
        dt.year - 1900,
        dt.month,
        dt.day,
        dt.hour,
        dt.minute,
        dt.second,
        28,  # +07:00 in 15-min intervals
    )


def pvd_datetime(dt: datetime.datetime) -> bytes:
    s = dt.strftime("%Y%m%d%H%M%S00").encode("ascii")
    return s + struct.pack("b", 28)


def iso_clean_name(name: str, is_dir: bool) -> str:
    allowed = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"
    up = name.upper().replace("-", "_")
    if is_dir:
        cleaned = "".join(c if c in allowed else "_" for c in up)[:30]
        return cleaned or "DIR"
    if "." in up:
        stem, ext = up.rsplit(".", 1)
    else:
        stem, ext = up, ""
    stem_c = "".join(c if c in allowed else "_" for c in stem)[:24] or "FILE"
    ext_c = "".join(c if c in allowed else "_" for c in ext)[:6]
    return f"{stem_c}.{ext_c};1" if ext_c else f"{stem_c}.;1"


class IsoNode:
    def __init__(self, name: str, is_dir: bool, src_path: Path | None = None):
        self.name = name
        self.is_dir = is_dir
        self.src_path = src_path
        self.children: list[IsoNode] = []
        self.parent: IsoNode | None = None
        self.iso_name = ""
        self.lba = 0
        self.size = 0
        self.dir_record_bytes = b""


def make_dir_record(iso_ident: bytes, lba: int, size: int, is_dir: bool, dt: datetime.datetime) -> bytes:
    flags = 0x02 if is_dir else 0x00
    name_len = len(iso_ident)
    rec_len = 33 + name_len + (1 if name_len % 2 == 0 else 0)
    buf = bytearray(rec_len)
    buf[0] = rec_len
    buf[1] = 0
    buf[2:10] = both_32(lba)
    buf[10:18] = both_32(size)
    buf[18:25] = dir_datetime(dt)
    buf[25] = flags
    buf[26] = 0
    buf[27] = 0
    buf[28:32] = both_16(1)
    buf[32] = name_len
    buf[33 : 33 + name_len] = iso_ident
    return bytes(buf)


def build_iso9660(source_dir: Path, out_iso: Path, volume_id: str, app_id: str):
    now = datetime.datetime(2026, 11, 3, 17, 0, 0)
    root = IsoNode("", True, source_dir)
    root.parent = root

    all_dirs: list[IsoNode] = [root]
    all_files: list[IsoNode] = []

    def walk_tree(dir_node: IsoNode, fs_path: Path):
        used_names: set[str] = set()
        entries = sorted(fs_path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        for entry in entries:
            is_d = entry.is_dir()
            node = IsoNode(entry.name, is_d, entry)
            node.parent = dir_node
            cand = iso_clean_name(entry.name, is_d)
            idx = 1
            while cand in used_names:
                idx += 1
                if is_d:
                    cand = f"{cand[:26]}_{idx}"
                else:
                    base, rest = cand.split(".", 1)
                    cand = f"{base[:20]}_{idx}.{rest}"
            used_names.add(cand)
            node.iso_name = cand
            dir_node.children.append(node)
            if is_d:
                all_dirs.append(node)
                walk_tree(node, entry)
            else:
                node.size = entry.stat().st_size
                all_files.append(node)

    walk_tree(root, source_dir)

    # First pass: estimate directory sizes (1 or more sectors)
    cur_lba = 20  # 0..15 system area, 16 PVD, 17 Terminator, 18 L-Path, 19 M-Path
    for d in all_dirs:
        # Calculate directory sectors needed
        est_bytes = 68 + sum(40 + len(c.iso_name) for c in d.children)
        sectors = max(1, math.ceil(est_bytes / SECTOR_SIZE))
        d.size = sectors * SECTOR_SIZE
        d.lba = cur_lba
        cur_lba += sectors

    for f in all_files:
        f.lba = cur_lba
        sectors = max(1, math.ceil(f.size / SECTOR_SIZE)) if f.size > 0 else 0
        cur_lba += sectors

    total_sectors = cur_lba

    # Build directory sector payloads without cross-sector record spanning
    for d in all_dirs:
        sectors_out = bytearray()
        cur_sec = bytearray()

        def append_rec(rec: bytes):
            nonlocal cur_sec, sectors_out
            if len(cur_sec) + len(rec) > SECTOR_SIZE:
                sectors_out.extend(cur_sec + b"\x00" * (SECTOR_SIZE - len(cur_sec)))
                cur_sec = bytearray()
            cur_sec.extend(rec)

        append_rec(make_dir_record(b"\x00", d.lba, d.size, True, now))
        parent_node = d.parent or d
        append_rec(make_dir_record(b"\x01", parent_node.lba, parent_node.size, True, now))
        for c in d.children:
            append_rec(make_dir_record(c.iso_name.encode("ascii"), c.lba, c.size, c.is_dir, now))

        if len(cur_sec) > 0 or len(sectors_out) == 0:
            sectors_out.extend(cur_sec + b"\x00" * (SECTOR_SIZE - len(cur_sec)))
        while len(sectors_out) < d.size:
            sectors_out.extend(b"\x00" * SECTOR_SIZE)
        d.dir_record_bytes = bytes(sectors_out[: d.size])

    # Build Path Tables (L-table and M-table)
    dir_index_map = {id(d): i + 1 for i, d in enumerate(all_dirs)}
    l_path = bytearray()
    m_path = bytearray()
    for d in all_dirs:
        ident = b"\x00" if d is root else d.iso_name.encode("ascii")
        nlen = len(ident)
        parent_idx = dir_index_map[id(d.parent or root)]
        l_path.extend(struct.pack("<BBIH", nlen, 0, d.lba, parent_idx) + ident)
        m_path.extend(struct.pack(">BBIH", nlen, 0, d.lba, parent_idx) + ident)
        if nlen % 2 == 1:
            l_path.append(0)
            m_path.append(0)

    path_table_size = len(l_path)

    # Primary Volume Descriptor (Sector 16)
    pvd = bytearray(SECTOR_SIZE)
    pvd[0] = 1
    pvd[1:6] = b"CD001"
    pvd[6] = 1
    pvd[8:40] = str_a("LINUX", 32)
    pvd[40:72] = str_a(volume_id, 32)
    pvd[80:88] = both_32(total_sectors)
    pvd[120:124] = both_16(1)
    pvd[124:128] = both_16(1)
    pvd[128:132] = both_16(SECTOR_SIZE)
    pvd[132:140] = both_32(path_table_size)
    pvd[140:144] = struct.pack("<I", 18)
    pvd[144:148] = struct.pack("<I", 0)
    pvd[148:152] = struct.pack(">I", 19)
    pvd[152:156] = struct.pack(">I", 0)
    root_rec = make_dir_record(b"\x00", root.lba, root.size, True, now)
    pvd[156 : 156 + len(root_rec)] = root_rec
    pvd[190:318] = str_a("THMD_GURU_LINUX_1_0_GENESIS", 128)
    pvd[318:446] = str_a("THMD_GURU_GLOBAL_TECH_ACADEMY", 128)
    pvd[446:574] = str_a("THMD_GURU_OS_FORGE", 128)
    pvd[574:702] = str_a(app_id, 128)
    pvd[813:830] = pvd_datetime(now)
    pvd[830:847] = pvd_datetime(now)
    pvd[847:864] = b"0000000000000000\x00"
    pvd[864:881] = pvd_datetime(now)
    pvd[881] = 1

    # Volume Descriptor Set Terminator (Sector 17)
    vdst = bytearray(SECTOR_SIZE)
    vdst[0] = 255
    vdst[1:6] = b"CD001"
    vdst[6] = 1

    out_iso.parent.mkdir(parents=True, exist_ok=True)
    with open(out_iso, "wb") as fp:
        fp.write(b"\x00" * (16 * SECTOR_SIZE))
        fp.write(pvd)
        fp.write(vdst)
        fp.write(pad_sector(bytes(l_path)))
        fp.write(pad_sector(bytes(m_path)))
        for d in all_dirs:
            fp.write(d.dir_record_bytes)
        for f in all_files:
            if f.size > 0 and f.src_path is not None:
                data = f.src_path.read_bytes()
                fp.write(pad_sector(data))


def stage_and_build_edition(root_dir: Path, edition: str, vol_id: str, app_id: str, iso_filename: str):
    work_iso = root_dir / "build" / f"iso-tree-{edition}"
    if work_iso.exists():
        shutil.rmtree(work_iso)
    work_iso.mkdir(parents=True, exist_ok=True)

    # 1. Bootloader & GRUB
    grub_dir = work_iso / "boot" / "grub"
    grub_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(root_dir / "core/bootloader/grub-pc/grub.cfg", grub_dir / "grub.cfg")
    shutil.copy2(root_dir / "core/bootloader/grub-pc/theme.txt", grub_dir / "theme.txt")

    # 2. APT Repo & Built .deb Packages
    if (root_dir / "out/apt-repo/pool").exists():
        shutil.copytree(root_dir / "out/apt-repo/pool", work_iso / "pool")
        shutil.copytree(root_dir / "out/apt-repo/dists", work_iso / "dists")

    # 3. Edition Overlay & Core Configs
    payload = work_iso / "thmd-guru"
    shutil.copytree(root_dir / "core/includes.chroot", payload / "rootfs")
    (payload / "rootfs/usr/share/thmd-guru/sysctl").mkdir(parents=True, exist_ok=True)
    for f in (root_dir / "core/kernel/sysctl").glob("*.conf"):
        shutil.copy2(f, payload / "rootfs/usr/share/thmd-guru/sysctl" / f.name)

    ed_dir = root_dir / "editions" / edition
    if (ed_dir / "includes.chroot").exists():
        shutil.copytree(ed_dir / "includes.chroot", payload / "rootfs", dirs_exist_ok=True)
    if (ed_dir / "includes.binary").exists():
        shutil.copytree(ed_dir / "includes.binary", work_iso, dirs_exist_ok=True)

    (payload / "hooks").mkdir(parents=True, exist_ok=True)
    for h in (root_dir / "core/hooks/live").glob("*.chroot"):
        shutil.copy2(h, payload / "hooks" / h.name)
    for h in (ed_dir / "hooks/live").glob("*.chroot"):
        shutil.copy2(h, payload / "hooks" / h.name)

    (payload / "package-lists").mkdir(parents=True, exist_ok=True)
    shutil.copy2(root_dir / "core/package-lists/base.list.chroot", payload / "package-lists/base.list")
    for plist in (ed_dir / "package-lists").glob("*.chroot"):
        shutil.copy2(plist, payload / "package-lists" / plist.name)

    # 4. Copy Secure Boot MOK public certificates if generated
    if (root_dir / "build/signing-keys/MOK.crt").exists():
        (payload / "secureboot").mkdir(parents=True, exist_ok=True)
        shutil.copy2(root_dir / "build/signing-keys/MOK.crt", payload / "secureboot/MOK.crt")
        shutil.copy2(root_dir / "build/signing-keys/MOK.der", payload / "secureboot/MOK.der")

    # 5. Write 1-Command In-Place / Netinst Transformation Installer
    installer_sh = work_iso / "install-thmd-guru.sh"
    installer_sh.write_text(
        f"""#!/usr/bin/env bash
# THMD-Guru Linux 1.0 (Genesis) — Edition: {edition.upper()}
# Automated In-Place & OEM ISO Installer for Debian 12 (Bookworm)
set -euo pipefail

ISO_ROOT="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
echo "===================================================================="
echo "  THMD-GURU LINUX 1.0 (GENESIS) — {edition.upper()} EDITION INSTALLER"
echo "  THMD-Guru Global Tech Academy — Learn Deep. Build Real. Secure Everything."
echo "===================================================================="

if [[ "$(id -u)" -ne 0 ]]; then
    echo "[ERROR] Vui long chay voi quyen root: sudo bash ${{ISO_ROOT}}/install-thmd-guru.sh" >&2
    exit 1
fi

echo "[1/4] Applying THMD-Guru RootFS Overlay & Identity..."
cp -rf "${{ISO_ROOT}}/thmd-guru/rootfs/." /

echo "[2/4] Installing THMD-Guru Native Debian Packages (.deb)..."
dpkg -i "${{ISO_ROOT}}"/pool/main/*.deb || apt-get install -f -y

echo "[3/4] Installing Edition Packages (${edition})..."
if [[ "${{SKIP_APT_PACKAGES:-0}}" != "1" ]]; then
    apt-get update
    grep -vE '^(#|$)' "${{ISO_ROOT}}"/thmd-guru/package-lists/* | xargs -r apt-get install -y --no-install-recommends
fi

echo "[4/4] Running THMD-Guru Core & Edition Configuration Hooks..."
for hook in "${{ISO_ROOT}}"/thmd-guru/hooks/*.chroot; do
    bash "${{hook}}"
done

echo "[SUCCESS] He dieu hanh THMD-Guru Linux 1.0 ({edition}) da duoc cai dat hoan tat!"
""",
        encoding="utf-8",
        newline="\n",
    )

    out_iso = root_dir / "out" / f"{iso_filename}.iso"
    build_iso9660(work_iso, out_iso, vol_id, app_id)
    sha256 = hashlib.sha256(out_iso.read_bytes()).hexdigest()
    (root_dir / "out" / f"{iso_filename}.iso.sha256").write_text(
        f"{sha256}  {iso_filename}.iso\n", encoding="utf-8", newline="\n"
    )
    shutil.rmtree(work_iso)
    print(f"[ISO Builder] Generated {out_iso.name} ({out_iso.stat().st_size:,} bytes) | SHA256: {sha256[:16]}...")


def main():
    root_dir = Path(__file__).resolve().parent.parent
    editions = [
        ("desktop", "THMD_GURU_DESK_1_0", "THMD-Guru Linux Desktop", "thmd-guru-desktop-1.0-genesis-amd64"),
        ("server", "THMD_GURU_SRV_1_0", "THMD-Guru Linux Server", "thmd-guru-server-1.0-genesis-amd64"),
        ("attt", "THMD_GURU_ATTT_1_0", "THMD-Guru Linux ATTT", "thmd-guru-attt-1.0-genesis-amd64"),
    ]
    for ed, vol, app, fname in editions:
        stage_and_build_edition(root_dir, ed, vol, app, fname)


if __name__ == "__main__":
    main()
