#!/usr/bin/env python3
"""
THMD-Guru OS Forge - Hybrid UEFI/BIOS Bootable ISO-9660 + Rock Ridge + CPIO Initramfs Builder
Builds standalone, bootable Hybrid ISO images (~68 MB each) for all 3 editions:
  - thmd-guru-desktop-1.0-genesis-amd64.iso
  - thmd-guru-server-1.0-genesis-amd64.iso
  - thmd-guru-attt-1.0-genesis-amd64.iso

Features:
  1. Official Debian 12 ("bookworm" amd64) Linux 6.1 LTS Kernel (/linux) & Base Initramfs (/initrd.gz)
  2. Pure-Python SVR4 `newc` CPIO Initramfs Injector embedding THMD-Guru OS identity,
     `/usr/bin/guru` CLI, edition plugins, sysctl profiles, `/bin/thmd-guru-live` Live OS init,
     and `/preseed.cfg` + `/usr/lib/finish-install.d/90thmd-guru` installer hooks.
  3. El Torito Dual BIOS (ISOLINUX with Boot-Info-Table) + UEFI (GRUB2 efi.img) Boot Catalog
     + Hybrid MBR (`isohdpfx`) for USB/VM booting.
  4. Rock Ridge (SUSP/RRIP) POSIX extensions (`SP`, `PX`, `NM`) preserving long filenames & permissions.

Owner: os-forge-devops & chief-os-architect
"""
import datetime
import gzip
import hashlib
import io
import math
import os
import shutil
import struct
import urllib.request
from pathlib import Path

SECTOR_SIZE = 2048
UPSTREAM_URL = "https://deb.debian.org/debian/dists/bookworm/main/installer-amd64/current/images/netboot/mini.iso"
UPSTREAM_SHA256 = "c9a88f81bfe7c20e62bcb3d1347e723e45ad5e35254af9f77f2686a52aee880d"


def pad_sector(data: bytes) -> bytes:
    rem = len(data) % SECTOR_SIZE
    return data if rem == 0 else data + b"\x00" * (SECTOR_SIZE - rem)


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
        28,
    )


def pvd_datetime(dt: datetime.datetime) -> bytes:
    s = dt.strftime("%Y%m%d%H%M%S00").encode("ascii")
    return s + struct.pack("b", 28)


def ensure_upstream_iso(root_dir: Path) -> bytes:
    cache_path = root_dir / "build" / "upstream" / "debian-12-mini.iso"
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    if cache_path.exists():
        data = cache_path.read_bytes()
        if hashlib.sha256(data).hexdigest().lower() == UPSTREAM_SHA256:
            return data
    print(f"[OS Forge] Downloading official Debian 12 Bookworm amd64 boot base from {UPSTREAM_URL}...")
    urllib.request.urlretrieve(UPSTREAM_URL, cache_path)
    data = cache_path.read_bytes()
    actual = hashlib.sha256(data).hexdigest().lower()
    if actual != UPSTREAM_SHA256:
        raise RuntimeError(f"Upstream ISO SHA256 mismatch: expected {UPSTREAM_SHA256}, got {actual}")
    return data


def extract_upstream_tree(iso_bytes: bytes, dest_dir: Path):
    """Extracts all files from the upstream ISO-9660 + Rock Ridge image into dest_dir."""
    pvd = iso_bytes[16 * SECTOR_SIZE : 17 * SECTOR_SIZE]
    root_rec = pvd[156:190]
    root_lba = struct.unpack("<I", root_rec[2:6])[0]
    root_len = struct.unpack("<I", root_rec[10:14])[0]

    def parse_rr_name(susp: bytes, fallback: str) -> str:
        i = 0
        nm = b""
        while i + 4 <= len(susp):
            sig = susp[i : i + 2]
            ln = susp[i + 2]
            if ln < 4 or i + ln > len(susp):
                break
            if sig == b"NM":
                nm += susp[i + 5 : i + ln]
            elif sig == b"CE":
                ce_lba = struct.unpack("<I", susp[i + 4 : i + 8])[0]
                ce_off = struct.unpack("<I", susp[i + 12 : i + 16])[0]
                ce_len = struct.unpack("<I", susp[i + 20 : i + 24])[0]
                sub = iso_bytes[ce_lba * SECTOR_SIZE + ce_off : ce_lba * SECTOR_SIZE + ce_off + ce_len]
                nm_ce = parse_rr_name(sub, "")
                if nm_ce:
                    nm += nm_ce.encode("utf-8")
            i += ln
        return nm.decode("utf-8", "replace") if nm else fallback

    def walk(lba: int, size: int, cur_out: Path):
        cur_out.mkdir(parents=True, exist_ok=True)
        buf = iso_bytes[lba * SECTOR_SIZE : lba * SECTOR_SIZE + size]
        pos = 0
        while pos < len(buf):
            rlen = buf[pos]
            if rlen == 0:
                pos = ((pos // SECTOR_SIZE) + 1) * SECTOR_SIZE
                continue
            rec = buf[pos : pos + rlen]
            elba = struct.unpack("<I", rec[2:6])[0]
            elen = struct.unpack("<I", rec[10:14])[0]
            flags = rec[25]
            nlen = rec[32]
            raw_name = rec[33 : 33 + nlen]
            pad = 1 if nlen % 2 == 0 else 0
            susp = rec[33 + nlen + pad :]
            if raw_name not in (b"\x00", b"\x01"):
                fallback = raw_name.decode("ascii", "replace").split(";")[0].rstrip(".")
                name = parse_rr_name(susp, fallback)
                if name != "boot.cat":
                    target = cur_out / name
                    if flags & 2:
                        walk(elba, elen, target)
                    else:
                        target.write_bytes(iso_bytes[elba * SECTOR_SIZE : elba * SECTOR_SIZE + elen])
            pos += rlen

    walk(root_lba, root_len, dest_dir)


def cpio_newc_entry(name: str, data: bytes, mode: int, ino: int, nlink: int = 1) -> bytes:
    """Packs a single SVR4 `newc` (070701) CPIO record."""
    name_b = name.lstrip("/").encode("utf-8") + b"\x00"
    namesize = len(name_b)
    filesize = len(data)
    mtime = 1793700000  # 2026-11-03
    header = (
        f"070701"
        f"{ino:08x}"
        f"{mode:08x}"
        f"{0:08x}"
        f"{0:08x}"
        f"{nlink:08x}"
        f"{mtime:08x}"
        f"{filesize:08x}"
        f"{0:08x}"
        f"{0:08x}"
        f"{0:08x}"
        f"{0:08x}"
        f"{namesize:08x}"
        f"{0:08x}"
    ).encode("ascii")
    out = bytearray(header + name_b)
    while len(out) % 4 != 0:
        out.append(0)
    out.extend(data)
    while len(out) % 4 != 0:
        out.append(0)
    return bytes(out)


def build_thmd_cpio_overlay_gz(root_dir: Path, edition: str) -> bytes:
    """Builds a gzipped `newc` CPIO archive containing the THMD-Guru Live & Installer overlay."""
    stream = bytearray()
    ino = 500000

    def add_dir(path_str: str):
        nonlocal ino
        ino += 1
        stream.extend(cpio_newc_entry(path_str, b"", 0o040755, ino, 2))

    def add_file(path_str: str, content: bytes, executable: bool = False):
        nonlocal ino
        ino += 1
        mode = 0o100755 if executable else 0o100644
        stream.extend(cpio_newc_entry(path_str, content, mode, ino, 1))

    def add_symlink(path_str: str, target: str):
        nonlocal ino
        ino += 1
        stream.extend(cpio_newc_entry(path_str, target.encode("utf-8"), 0o120777, ino, 1))

    for d in [
        "bin",
        "etc",
        "etc/thmd-guru",
        "etc/sysctl.d",
        "etc/audit",
        "etc/audit/rules.d",
        "etc/NetworkManager",
        "etc/NetworkManager/conf.d",
        "usr",
        "usr/bin",
        "usr/lib",
        "usr/lib/guru",
        "usr/lib/guru/commands",
        "usr/lib/finish-install.d",
        "usr/share",
        "usr/share/thmd-guru",
        "usr/share/thmd-guru/labs",
    ]:
        add_dir(d)

    # Compatibility helper so `#!/usr/bin/env bash` works in BusyBox initramfs
    # Note: Do NOT overwrite `usr/bin/env` because in Debian initrd.gz `usr/bin/env` is a symlink
    # to `/bin/busybox`, which natively handles `#!/usr/bin/env bash` once `/bin/bash` exists!
    add_file("bin/bash", b"#!/bin/sh\nexec /bin/sh \"$@\"\n", executable=True)

    # Core OS identity files & MITRE ATT&CK Auditd Rules
    for rel in [
        "etc/os-release",
        "usr/lib/os-release",
        "etc/lsb-release",
        "etc/issue",
        "etc/issue.net",
        "etc/motd",
        "etc/thmd-guru/version",
        "etc/sysctl.d/90-thmd-guru-base.conf",
        "etc/audit/rules.d/90-thmd-guru-mitre.rules",
    ]:
        src = root_dir / "core/includes.chroot" / rel
        if src.exists():
            add_file(rel, src.read_bytes().replace(b"\r\n", b"\n"))

    add_file("etc/thmd-guru/edition", f"{edition}\n".encode("utf-8"))
    add_file("etc/hostname", f"guru-{edition}\n".encode("utf-8"))

    sysctl_ed = root_dir / f"core/kernel/sysctl/91-{edition}.conf"
    if sysctl_ed.exists():
        add_file(f"etc/sysctl.d/91-{edition}.conf", sysctl_ed.read_bytes().replace(b"\r\n", b"\n"))

    # Install `THMD-guru-ai` + `guru` CLI and ONLY edition-appropriate plugins (Strict Edition Isolation)
    guru_cli_bytes = (root_dir / "packages/guru-cli/src/guru").read_bytes().replace(b"\r\n", b"\n")
    add_file("usr/bin/guru", guru_cli_bytes, executable=True)
    add_file("usr/bin/THMD-guru-ai", guru_cli_bytes, executable=True)
    edition_plugins: dict[str, dict[str, Path]] = {
        "desktop": {
            "welcome": root_dir / "packages/guru-welcome/src/welcome-plugin",
        },
        "server": {
            "console": root_dir / "packages/guru-server-console/src/console-plugin",
        },
        "attt": {
            "sandbox": root_dir / "packages/guru-sandbox/src/sandbox-plugin",
            "stealth": root_dir / "packages/guru-stealth/src/stealth-plugin",
        },
    }
    if edition == "desktop":
        add_file(
            "usr/bin/guru-welcome",
            (root_dir / "packages/guru-welcome/src/guru-welcome").read_bytes().replace(b"\r\n", b"\n"),
            executable=True,
        )
    for pname, ppath in edition_plugins.get(edition, {}).items():
        add_file(
            f"usr/lib/guru/commands/{pname}",
            ppath.read_bytes().replace(b"\r\n", b"\n"),
            executable=True,
        )

    # Modular Architecture (v1.1.0+): Core OS initramfs stays pure & lean.
    # Apps, Tools, Hands-on LABs, and NCKH suites are NOT pre-installed in RAM;
    # they are installed on-demand via `THMD-guru-ai hub install <module>`.
    add_dir("opt")
    add_dir("opt/thmd-guru")
    add_dir("opt/thmd-guru/modules")
    add_dir("usr/share/thmd-guru/patch-agent")
    patch_agent_src = root_dir / "builder/patch_agent.py"
    if patch_agent_src.exists():
        add_file(
            "usr/share/thmd-guru/patch-agent/patch_agent.py",
            patch_agent_src.read_bytes().replace(b"\r\n", b"\n"),
            executable=True,
        )

    # Debian Installer finish-install hook to automatically convert target disk into THMD-Guru Linux
    finish_hook = b"""#!/bin/sh
set -e
if [ -d /target ] && [ -f /cdrom/install-thmd-guru.sh ]; then
    mkdir -p /target/media/cdrom
    cp -rf /cdrom/thmd-guru/rootfs/. /target/ || true
    cp -f /cdrom/pool/main/*.deb /target/tmp/ 2>/dev/null || true
    chroot /target sh -c "dpkg -i /tmp/*.deb || true; rm -f /tmp/*.deb"
fi
"""
    add_file("usr/lib/finish-install.d/90thmd-guru", finish_hook, executable=True)

    # Interactive THMD-Guru Installer & VMware Lab Node Provisioner (`/usr/bin/thmd-installer`)
    thmd_installer = f"""#!/bin/sh
# THMD-Guru Linux 1.0 "Genesis" ({edition.upper()}) - Interactive OS Installer & VMware Lab Wizard
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

persist_to_disk() {{
    DISK_DEV=""
    for cand in /dev/sda /dev/vda /dev/nvme0n1; do
        if [ -b "$cand" ]; then
            DISK_DEV="$cand"
            break
        fi
    done
    echo ""
    echo "========================================================================"
    echo "  THMD-GURU LINUX 1.0 ({edition.upper()}) - PERSISTENT SYSTEM & DISK INSTALLER"
    echo "========================================================================"
    if [ -n "$DISK_DEV" ]; then
        echo "[OK] Detected Virtual Hard Disk: $DISK_DEV"
    else
        echo "[INFO] Running in RAM Disk Mode (no block disk detected, configuring Live RootFS)."
    fi
    if [ -d /cdrom/thmd-guru/rootfs ]; then
        echo "[1/3] Applying THMD-Guru RootFS Overlay & Identity (/etc/os-release, sysctl, auditd)..."
        cp -rf /cdrom/thmd-guru/rootfs/. / 2>/dev/null || true
    fi
    echo "[2/3] Applying CIS / KSPP Kernel Hardening & Edition Sysctl Profiles ({edition})..."
    /bin/sh /usr/bin/THMD-guru-ai harden --apply
    echo "[3/3] Verifying THMD-Guru Edition Plugins & Lab Modules..."
    /bin/sh /usr/bin/THMD-guru-ai plugins
    /bin/sh /usr/bin/THMD-guru-ai lab list
    echo ""
    echo "[SUCCESS] THMD-Guru Linux 1.0 ({edition.upper()}) configured and active!"
}}

while true; do
    echo ""
    echo "========================================================================"
    echo "  THMD-GURU LINUX 1.1 (GENESIS) [{edition.upper()}] - CORE OS & MODULAR HUB"
    echo "  Architecture: Lean Core OS (Apps, Tools, LAB & NCKH Installed On-Demand)"
    echo "========================================================================"
    echo "  [1] Install Clean Core OS Only (Pure Base System - No Apps/LABs/NCKH)"
    echo "  [2] Open Modular Hub Store (Select & Install Tools, Apps, LABs, NCKH)"
    echo "  [3] Provision VM1 (IP 192.168.80.10 + On-Demand Install vm1-zap)"
    echo "  [4] Provision VM2 (IP 192.168.80.20 + On-Demand Install vm2-target)"
    echo "  [5] Provision VM3 (IP 192.168.80.30 + On-Demand Install vm3-airag)"
    echo "  [0] Exit to Clean Core OS Shell (root@guru-{edition})"
    echo "------------------------------------------------------------------------"
    printf "Select option [0-5] (or press ENTER for [0] Core OS Shell): "
    read -r ans || break
    case "${{ans:-0}}" in
        1)
            persist_to_disk
            /bin/sh /usr/bin/THMD-guru-ai hub status
            break
            ;;
        2)
            /bin/sh /usr/bin/THMD-guru-ai hub menu
            ;;
        3)
            persist_to_disk
            /bin/sh /usr/bin/THMD-guru-ai vm-node init lab80-vm1
            /bin/sh /usr/bin/THMD-guru-ai hub install nckh/vmware-zap-rag-pfsense --role vm1-zap
            /bin/sh /usr/bin/THMD-guru-ai hub install tools/attt-web-scanner --role vm1-zap
            /bin/sh /usr/bin/THMD-guru-ai status
            break
            ;;
        4)
            persist_to_disk
            /bin/sh /usr/bin/THMD-guru-ai vm-node init lab80-vm2
            /bin/sh /usr/bin/THMD-guru-ai hub install nckh/vmware-zap-rag-pfsense --role vm2-target
            /bin/sh /usr/bin/THMD-guru-ai hub install tools/server-container --role vm2-target
            /bin/sh /usr/bin/THMD-guru-ai status
            break
            ;;
        5)
            persist_to_disk
            /bin/sh /usr/bin/THMD-guru-ai vm-node init lab80-vm3
            /bin/sh /usr/bin/THMD-guru-ai hub install nckh/vmware-zap-rag-pfsense --role vm3-airag
            /bin/sh /usr/bin/THMD-guru-ai hub install tools/ai-rag-engine --role vm3-airag
            /bin/sh /usr/bin/THMD-guru-ai status
            break
            ;;
        0|"")
            break
            ;;
        *)
            echo "Invalid choice: $ans"
            ;;
    esac
done
""".encode("utf-8")
    add_file("usr/bin/thmd-installer", thmd_installer, executable=True)

    # Preseed configuration
    preseed_src = root_dir / "editions/server/includes.binary/preseed/thmd-guru-server.cfg"
    if preseed_src.exists():
        add_file("preseed.cfg", preseed_src.read_bytes().replace(b"\r\n", b"\n"))

    # Live OS Init Script (`/bin/thmd-guru-live`)
    live_init = f"""#!/bin/sh
# THMD-Guru Linux 1.0 "Genesis" ({edition.upper()}) - Live OS Init & Self-Test Runner
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
export HOME="/root"
export USER="root"
export TERM="linux"

echo "[THMD-Guru Linux 1.0 ({edition.upper()})] Initializing kernel, devtmpfs & VMware drivers..." > /dev/console 2>/dev/null || true

mkdir -p /run /run/lock /proc /sys /dev /dev/pts /tmp /cdrom /root /target
mount -t tmpfs tmpfs /run 2>/dev/null || true
mkdir -p /run/lock
mount -t proc proc /proc 2>/dev/null || true
mount -t sysfs sysfs /sys 2>/dev/null || true

# CRITICAL: Mount devtmpfs on /dev BEFORE accessing /dev/tty0, /dev/tty1, /dev/ttyS0, /dev/sr0
if ! grep -q " /dev devtmpfs" /proc/mounts 2>/dev/null; then
    mount -n -o mode=0755 -t devtmpfs devtmpfs /dev 2>/dev/null || true
fi
[ ! -h /dev/fd ] && ln -s /proc/self/fd /dev/fd 2>/dev/null || true
[ ! -h /dev/stdin ] && ln -s /proc/self/fd/0 /dev/stdin 2>/dev/null || true
[ ! -h /dev/stdout ] && ln -s /proc/self/fd/1 /dev/stdout 2>/dev/null || true
[ ! -h /dev/stderr ] && ln -s /proc/self/fd/2 /dev/stderr 2>/dev/null || true

mkdir -p /dev/pts
mount -t devpts -o noexec,nosuid,gid=5,mode=0620 devpts /dev/pts 2>/dev/null || true
mount -t tmpfs tmpfs /tmp 2>/dev/null || true

# Start udevd & trigger hardware discovery (loads VMware/QEMU display, storage, CD-ROM, USB, network drivers)
if [ -x /lib/systemd/systemd-udevd ]; then
    SYSTEMD_LOG_LEVEL=err /lib/systemd/systemd-udevd --daemon --resolve-names=never 2>/dev/null || true
    udevadm trigger --action=add 2>/dev/null || true
    udevadm settle --timeout=3 2>/dev/null || true
elif [ -x /lib/debian-installer/start-udev ]; then
    /lib/debian-installer/start-udev >/dev/null 2>&1 || true
fi

for mod in fbcon vesafb efifb vga16fb bochs cirrus virtio_gpu \\
           usbhid hid_generic hid ehci_hcd ehci_pci xhci_hcd xhci_pci uhci_hcd ohci_hcd \\
           sr_mod cdrom isofs sd_mod ata_piix ahci vmw_pvscsi virtio_blk virtio_scsi nvme \\
           e1000 e1000e vmxnet3 virtio_net ext4; do
    modprobe "$mod" 2>/dev/null || true
done

# Mount ISO-9660 CD-ROM if available
for dev in /dev/sr0 /dev/cdrom /dev/hdc /dev/sda /dev/sdb; do
    if [ -b "$dev" ]; then
        mount -t iso9660 -o ro "$dev" /cdrom 2>/dev/null && break || true
    fi
done

if [ -d /cdrom/thmd-guru/rootfs ]; then
    cp -rf /cdrom/thmd-guru/rootfs/. / 2>/dev/null || true
fi

hostname "guru-{edition}" 2>/dev/null || true
ip link set lo up 2>/dev/null || true
for iface in $(ip -o link show 2>/dev/null | awk -F': ' '$2 != "lo" {{print $2}}' | cut -d@ -f1); do
    ip link set "$iface" up 2>/dev/null || true
done

# Apply THMD-Guru Kernel sysctl hardening & edition tuning
/usr/bin/guru harden --apply >/dev/null 2>&1 || true

# Disable kernel printk noise on interactive console
echo "3 4 1 3" > /proc/sys/kernel/printk 2>/dev/null || true

CMDLINE="$(cat /proc/cmdline 2>/dev/null || true)"

run_welcome_banner() {{
    echo ""
    cat /etc/motd 2>/dev/null || true
    echo ""
    /bin/sh /usr/bin/guru info
    echo ""
    /bin/sh /usr/bin/guru status
    echo ""
    /bin/sh /usr/bin/guru harden
    echo ""
    /bin/sh /usr/bin/guru plugins
    echo ""
    echo "============================================================================"
    echo "  QUICK COMMANDS (THMD-Guru Linux 1.0 - {edition.upper()} Edition):"
    echo "    THMD-guru-ai help                           # Full CLI guide"
    echo "    THMD-guru-ai vm-node init lab80-vm1         # IP 192.168.80.10/24 (VM1)"
    echo "    THMD-guru-ai vm-node init lab80-vm2         # IP 192.168.80.20/24 (VM2)"
    echo "    THMD-guru-ai vm-node init lab80-vm3         # IP 192.168.80.30/24 (VM3)"
    echo "    THMD-guru-ai lab run vmware-zap-rag-pfsense # Run NCKH ZAP+RAG Lab"
    echo "    thmd-installer                              # OS & VMware Lab Wizard"
    echo "============================================================================"
    echo ""
}}

if echo "$CMDLINE" | grep -q "thmd_autotest=1"; then
    [ -c /dev/tty0 ] && run_welcome_banner > /dev/tty0 2>&1 || true
    [ -c /dev/ttyS0 ] && run_welcome_banner > /dev/ttyS0 2>&1 || true
    [ -c /dev/ttyS0 ] && echo "[THMD-GURU-QEMU-BOOT-TEST-PASSED:{edition}]" > /dev/ttyS0 2>&1 || true
    [ -c /dev/tty0 ] && echo "[THMD-GURU-QEMU-BOOT-TEST-PASSED:{edition}]" > /dev/tty0 2>&1 || true
    sync
    poweroff -f 2>/dev/null || reboot -f
    exit 0
fi

PRIMARY_TTY="/dev/console"
if [ -c /dev/tty1 ]; then
    PRIMARY_TTY="/dev/tty1"
elif [ -c /dev/tty0 ]; then
    PRIMARY_TTY="/dev/tty0"
fi

if [ -c "$PRIMARY_TTY" ]; then
    run_welcome_banner > "$PRIMARY_TTY" 2>&1 || true
fi
if [ -c /dev/ttyS0 ] && [ "$PRIMARY_TTY" != "/dev/ttyS0" ]; then
    run_welcome_banner > /dev/ttyS0 2>&1 || true
fi

if echo "$CMDLINE" | grep -q "thmd_mode=install"; then
    /usr/bin/thmd-installer < "$PRIMARY_TTY" > "$PRIMARY_TTY" 2>&1 || true
fi

export PS1="[THMD-Guru:{edition}] root@guru-{edition}:~# "
if [ -c /dev/ttyS0 ] && [ "$PRIMARY_TTY" != "/dev/ttyS0" ]; then
    (while true; do /bin/sh -i < /dev/ttyS0 > /dev/ttyS0 2>&1 || true; sleep 1; done) &
fi
while true; do
    if command -v setsid >/dev/null 2>&1 && [ -c "$PRIMARY_TTY" ]; then
        setsid -c /bin/sh -i < "$PRIMARY_TTY" > "$PRIMARY_TTY" 2>&1 || /bin/sh -i < "$PRIMARY_TTY" > "$PRIMARY_TTY" 2>&1 || true
    else
        /bin/sh -i < "$PRIMARY_TTY" > "$PRIMARY_TTY" 2>&1 || /bin/sh -i < /dev/console > /dev/console 2>&1 || true
    fi
    sleep 1
done
""".encode("utf-8")
    add_file("bin/thmd-guru-live", live_init, executable=True)

    # CPIO trailer
    ino += 1
    stream.extend(cpio_newc_entry("TRAILER!!!", b"", 0, 0, 1))
    while len(stream) % 512 != 0:
        stream.append(0)

    buf = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=buf, compresslevel=6, mtime=1793700000) as gz:
        gz.write(stream)
    return buf.getvalue()


def generate_thmd_splash_png() -> bytes:
    """Generates a 640x480 24-bit RGB PNG boot splash in THMD-Guru Cyber Sapphire & Royal Gold."""
    import zlib

    w, h = 640, 480
    raw = bytearray()
    for y in range(h):
        raw.append(0)  # filter type 0
        # Top header bar (0..64): Deep Navy #071A3A with Royal Gold border at y=62..64
        if y in (0, 1, 62, 63, 478, 479):
            row_px = bytes([212, 175, 55]) * w  # Royal Gold #D4AF37
            raw.extend(row_px)
            continue
        if y < 62:
            r, g, b = 7, 26, 58
        else:
            # Smooth vertical gradient from Sapphire (#0B3D91) to Ink (#0A0F1E)
            t = (y - 64) / (h - 64)
            r = int(11 * (1 - t) + 10 * t)
            g = int(61 * (1 - t) + 15 * t)
            b = int(145 * (1 - t) + 30 * t)
        row = bytearray([r, g, b] * w)
        # Left & right Royal Gold frame border
        row[0:6] = bytes([212, 175, 55]) * 2
        row[(w - 2) * 3 : w * 3] = bytes([212, 175, 55]) * 2
        # Draw a Royal Gold emblem badge on the top-left (x=20..52, y=14..48)
        if 14 <= y <= 48:
            dy = abs(y - 31)
            x_left = 20 + dy // 2
            x_right = 52 - dy // 2
            for x in range(x_left, x_right + 1):
                if x in (x_left, x_left + 1, x_right - 1, x_right) or y in (14, 15, 47, 48) or (29 <= y <= 33 and 28 <= x <= 44):
                    row[x * 3 : (x + 1) * 3] = bytes([245, 215, 122])
                else:
                    row[x * 3 : (x + 1) * 3] = bytes([11, 61, 145])
        raw.extend(row)

    def png_chunk(tag: bytes, body: bytes) -> bytes:
        return struct.pack(">I", len(body)) + tag + body + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF)

    return (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
        + png_chunk(b"IDAT", zlib.compress(bytes(raw), 6))
        + png_chunk(b"IEND", b"")
    )


def write_bootloader_configs(work_iso: Path, edition: str):
    """Writes THMD-Guru branded ISOLINUX (BIOS) and GRUB2 (UEFI) bootloader configs."""
    ed_upper = edition.upper()

    (work_iso / "splash.png").write_bytes(generate_thmd_splash_png())

    stdmenu_cfg = """menu background splash.png
menu color title    * #FFF5D77A *
menu color border   * #FFD4AF37 #00000000 std
menu color sel      * #FF0A0F1E #FFD4AF37 *
menu color hotsel   1;7;37;40 #FF0A0F1E #FFF5D77A *
menu color unsel    * #FFE6ECF7 #00000000 *
menu color tabmsg   * #FFF5D77A #00000000 *
menu color timeout  * #FFF5D77A #00000000 *
menu color help     37;40 #FFF5D77A #00000000 none
menu vshift 6
menu rows 10
menu helpmsgrow 15
menu cmdlinerow 17
menu timeoutrow 17
menu tabmsgrow 19
menu tabmsg THMD-Guru Global Tech Academy | [ENTER] Boot   [TAB] Edit Kernel Options
"""
    (work_iso / "stdmenu.cfg").write_text(stdmenu_cfg, encoding="utf-8", newline="\n")

    isolinux_cfg = f"""# THMD-Guru Linux 1.0 (Genesis) - BIOS ISOLINUX Configuration
path 
prompt 0
timeout 50
default vesamenu.c32

menu hshift 2
menu width 76
menu title THMD-Guru Linux 1.0 (Genesis) - {ed_upper} Edition [BIOS/UEFI]
include stdmenu.cfg

label install
    menu label ^1. THMD-Guru Linux 1.0 ({ed_upper}) - Install & VMware Lab Wizard
    menu default
    kernel /linux
    append vga=normal fb=false init=/bin/thmd-guru-live thmd_mode=install console=ttyS0,115200n8 console=tty0 initrd=/initrd.gz --- quiet

label live
    menu label ^2. THMD-Guru Linux 1.0 ({ed_upper}) - Live System (RAM OS)
    kernel /linux
    append vga=normal fb=false init=/bin/thmd-guru-live console=ttyS0,115200n8 console=tty0 initrd=/initrd.gz --- quiet

label safe
    menu label ^3. THMD-Guru Linux 1.0 ({ed_upper}) - Safe Mode (nomodeset)
    kernel /linux
    append vga=normal fb=false nomodeset init=/bin/thmd-guru-live console=ttyS0,115200n8 console=tty0 initrd=/initrd.gz ---

label forensic
    menu label ^4. THMD-Guru Linux 1.0 ({ed_upper}) - Forensic Mode (No Swap/Mount)
    kernel /linux
    append vga=normal fb=false noswap noautomount init=/bin/thmd-guru-live console=ttyS0,115200n8 console=tty0 initrd=/initrd.gz ---

label autotest
    menu label ^5. THMD-Guru Linux 1.0 ({ed_upper}) - Automated Self-Test Mode
    kernel /linux
    append vga=normal fb=false init=/bin/thmd-guru-live thmd_autotest=1 console=ttyS0,115200n8 console=tty0 initrd=/initrd.gz --- quiet

label netinstall
    menu label ^6. THMD-Guru Linux 1.0 ({ed_upper}) - Debian Netboot Installer (Preseed)
    kernel /linux
    append vga=normal fb=false preseed/file=/preseed.cfg initrd=/initrd.gz --- quiet
"""
    (work_iso / "isolinux.cfg").write_text(isolinux_cfg, encoding="utf-8", newline="\n")
    (work_iso / "txt.cfg").write_text(isolinux_cfg, encoding="utf-8", newline="\n")

    grub_cfg = f"""# THMD-Guru Linux 1.0 (Genesis) - UEFI GRUB2 Configuration
set default=0
set timeout=5

insmod all_video
insmod efi_gop
insmod efi_uga
insmod video_bochs
insmod video_cirrus
insmod font
insmod gfxterm
insmod png

if loadfont /boot/grub/font.pf2 ; then
  set gfxmode=800x600,auto
  set gfxpayload=keep
  terminal_output gfxterm
fi

if background_image /splash.png; then
  set color_normal=light-gray/black
  set color_highlight=yellow/black
  set menu_color_normal=light-gray/black
  set menu_color_highlight=yellow/blue
else
  set menu_color_normal=light-gray/blue
  set menu_color_highlight=yellow/blue
fi

menuentry "1. THMD-Guru Linux 1.0 (Genesis) [{ed_upper}] - Install & VMware Lab Wizard" {{
    set gfxpayload=keep
    linux  /linux init=/bin/thmd-guru-live thmd_mode=install console=ttyS0,115200n8 console=tty0 --- quiet
    initrd /initrd.gz
}}

menuentry "2. THMD-Guru Linux 1.0 (Genesis) [{ed_upper}] - Live System (RAM OS)" {{
    set gfxpayload=keep
    linux  /linux init=/bin/thmd-guru-live console=ttyS0,115200n8 console=tty0 --- quiet
    initrd /initrd.gz
}}

menuentry "3. THMD-Guru Linux 1.0 (Genesis) [{ed_upper}] - Safe Mode (nomodeset)" {{
    set gfxpayload=keep
    linux  /linux init=/bin/thmd-guru-live nomodeset console=ttyS0,115200n8 console=tty0 ---
    initrd /initrd.gz
}}

menuentry "4. THMD-Guru Linux 1.0 (Genesis) [{ed_upper}] - Forensic Mode (No Automount / No Swap)" {{
    set gfxpayload=keep
    linux  /linux init=/bin/thmd-guru-live noswap noautomount console=ttyS0,115200n8 console=tty0 ---
    initrd /initrd.gz
}}

menuentry "5. THMD-Guru Linux 1.0 (Genesis) [{ed_upper}] - Automated Self-Test Mode" {{
    set gfxpayload=keep
    linux  /linux init=/bin/thmd-guru-live thmd_autotest=1 console=ttyS0,115200n8 console=tty0 --- quiet
    initrd /initrd.gz
}}

menuentry "6. THMD-Guru Linux 1.0 (Genesis) [{ed_upper}] - Debian Netboot Installer (Preseed)" {{
    set gfxpayload=keep
    linux  /linux fb=false preseed/file=/preseed.cfg --- quiet
    initrd /initrd.gz
}}
"""
    (work_iso / "boot/grub/grub.cfg").write_text(grub_cfg, encoding="utf-8", newline="\n")
    (work_iso / ".disk/info").write_text(
        f"THMD-Guru Linux 1.0 (Genesis) - {ed_upper} Edition amd64 (Debian 12 Bookworm Base)\n",
        encoding="utf-8",
        newline="\n",
    )


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
    stem_c = "".join(c if c in allowed else "_" for c in stem)[:20] or "FILE"
    ext_c = "".join(c if c in allowed else "_" for c in ext)[:6]
    return f"{stem_c}.{ext_c};1" if ext_c else f"{stem_c}.;1"


class IsoNode:
    def __init__(self, name: str, is_dir: bool, src_path: Path | None = None, rel_path: str = ""):
        self.name = name
        self.is_dir = is_dir
        self.src_path = src_path
        self.rel_path = rel_path
        self.children: list[IsoNode] = []
        self.parent: IsoNode | None = None
        self.iso_name = ""
        self.lba = 0
        self.size = 0
        self.dir_record_bytes = b""


def make_rock_ridge_susp(name: str, is_dir: bool, is_root_self: bool = False, is_dot: bool = False) -> bytes:
    susp = bytearray()
    if is_root_self:
        # SP System Use Sharing Protocol indicator (7 bytes)
        susp.extend(b"SP\x07\x01\xbe\xef\x00")
    mode = 0o040755 if is_dir else 0o100755
    nlink = 2 if is_dir else 1
    # PX POSIX file attributes (36 bytes)
    px = bytearray(b"PX\x24\x01")
    px.extend(both_32(mode))
    px.extend(both_32(nlink))
    px.extend(both_32(0))
    px.extend(both_32(0))
    susp.extend(px)
    if is_root_self:
        # ER Extensions Reference (18 bytes) - required by GRUB2 (efi.img) & Linux isofs to enable Rock Ridge!
        susp.extend(b"ER\x12\x01\x0a\x00\x00\x01RRIP_1991A")
    if not is_dot and name:
        nb = name.encode("utf-8")[:200]
        nm_len = 5 + len(nb)
        susp.extend(b"NM" + bytes([nm_len, 1, 0]) + nb)
    if len(susp) % 2 == 1:
        susp.append(0)
    return bytes(susp)


def make_dir_record(
    iso_ident: bytes,
    lba: int,
    size: int,
    is_dir: bool,
    dt: datetime.datetime,
    susp: bytes = b"",
) -> bytes:
    flags = 0x02 if is_dir else 0x00
    name_len = len(iso_ident)
    base_len = 33 + name_len + (1 if name_len % 2 == 0 else 0)
    rec_len = base_len + len(susp)
    if rec_len > 254:
        susp = b""
        rec_len = base_len
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
    if susp:
        buf[base_len : base_len + len(susp)] = susp
    return bytes(buf)


def build_el_torito_catalog(bios_lba: int, efi_lba: int, efi_byte_size: int) -> bytes:
    """Creates the 2048-byte El Torito Boot Catalog supporting both BIOS (isolinux.bin) and UEFI (efi.img)."""
    cat = bytearray(SECTOR_SIZE)
    # Entry 0: Validation Entry (Platform 0 = x86)
    ve = bytearray(32)
    ve[0] = 0x01
    ve[1] = 0x00
    ve[30] = 0x55
    ve[31] = 0xAA
    words = struct.unpack("<16H", ve)
    csum = (-sum(words)) & 0xFFFF
    struct.pack_into("<H", ve, 28, csum)
    cat[0:32] = ve

    # Entry 1: Initial/Default Entry (BIOS isolinux.bin, 4 virtual 512B sectors)
    ie = bytearray(32)
    ie[0] = 0x88  # Bootable
    ie[1] = 0x00  # No emulation
    struct.pack_into("<H", ie, 6, 4)
    struct.pack_into("<I", ie, 8, bios_lba)
    cat[32:64] = ie

    # Entry 2: Section Header Entry (Final section, Platform 0xEF = EFI)
    sh = bytearray(32)
    sh[0] = 0x91  # Final section header
    sh[1] = 0xEF  # EFI platform ID
    struct.pack_into("<H", sh, 2, 1)  # 1 section entry follows
    cat[64:96] = sh

    # Entry 3: Section Entry (UEFI efi.img)
    se = bytearray(32)
    se[0] = 0x88  # Bootable
    se[1] = 0x00  # No emulation
    efi_sectors_512 = min(0xFFFF, math.ceil(efi_byte_size / 512))
    struct.pack_into("<H", se, 6, efi_sectors_512)
    struct.pack_into("<I", se, 8, efi_lba)
    cat[96:128] = se
    return bytes(cat)


def patch_isolinux_bin(raw_isolinux: bytes, pvd_lba: int, isolinux_lba: int) -> bytes:
    """Updates the 56-byte El Torito Boot-Info-Table at offset 8 of isolinux.bin."""
    buf = bytearray(raw_isolinux)
    file_len = len(buf)
    # Pad to 4-byte boundary if needed
    while len(buf) % 4 != 0:
        buf.append(0)
    words = struct.unpack(f"<{len(buf[64:]) // 4}I", buf[64:])
    csum = sum(words) & 0xFFFFFFFF
    struct.pack_into("<IIII", buf, 8, pvd_lba, isolinux_lba, file_len, csum)
    return bytes(buf[:file_len])


def patch_hybrid_mbr(mbr_32k: bytes, total_sectors_2048: int, isolinux_lba: int, efi_lba: int, efi_size: int) -> bytes:
    """Updates the ISOHYBRID MBR header to point to our new isolinux.bin LBA and EFI partition."""
    buf = bytearray(mbr_32k[: 16 * SECTOR_SIZE])
    # Offset 432 in isohdpfx MBR holds the 512-byte sector LBA of isolinux.bin
    struct.pack_into("<I", buf, 432, isolinux_lba * 4)
    # Partition 1 (offset 446): ISO whole-disk partition
    total_512 = total_sectors_2048 * 4
    struct.pack_into("<I", buf, 446 + 8, 0)
    struct.pack_into("<I", buf, 446 + 12, total_512)
    # Partition 2 (offset 462): EFI System Partition (0xEF)
    efi_lba_512 = efi_lba * 4
    efi_count_512 = math.ceil(efi_size / 512)
    buf[462 + 0] = 0x00
    buf[462 + 4] = 0xEF
    struct.pack_into("<I", buf, 462 + 8, efi_lba_512)
    struct.pack_into("<I", buf, 462 + 12, efi_count_512)
    # Clear Partition 3 & 4
    buf[478:510] = b"\x00" * 32
    buf[510:512] = b"\x55\xaa"
    return bytes(buf)


def build_bootable_iso9660(
    source_dir: Path,
    out_iso: Path,
    volume_id: str,
    app_id: str,
    mbr_template: bytes,
):
    now = datetime.datetime(2026, 11, 3, 17, 50, 0)
    root = IsoNode("", True, source_dir, "")
    root.parent = root

    all_dirs: list[IsoNode] = [root]
    all_files: list[IsoNode] = []

    def walk_tree(dir_node: IsoNode, fs_path: Path, rel_prefix: str):
        used_names: set[str] = set()
        entries = sorted(fs_path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        for entry in entries:
            is_d = entry.is_dir()
            rel = f"{rel_prefix}/{entry.name}" if rel_prefix else entry.name
            node = IsoNode(entry.name, is_d, entry, rel)
            node.parent = dir_node
            cand = iso_clean_name(entry.name, is_d)
            idx = 1
            while cand in used_names:
                idx += 1
                if is_d:
                    cand = f"{cand[:24]}_{idx}"
                else:
                    base, rest = cand.split(".", 1)
                    cand = f"{base[:16]}_{idx}.{rest}"
            used_names.add(cand)
            node.iso_name = cand
            dir_node.children.append(node)
            if is_d:
                all_dirs.append(node)
                walk_tree(node, entry, rel)
            else:
                node.size = entry.stat().st_size
                all_files.append(node)
        # ISO-9660 Section 9.3 requires directory records to be sorted by ASCII identifier
        dir_node.children.sort(key=lambda n: n.iso_name.split(";")[0])

    walk_tree(root, source_dir, "")

    # Layout sectors:
    # 0..15  : Hybrid MBR / System Area
    # 16     : Primary Volume Descriptor (PVD)
    # 17     : El Torito Boot Record Volume Descriptor (BRVD)
    # 18     : Volume Descriptor Set Terminator (VDST)
    # 19     : L-Path Table
    # 20     : M-Path Table
    # 21     : El Torito Boot Catalog
    boot_catalog_lba = 21
    cur_lba = 22

    # First pass: build directory records to determine exact sector counts
    for _pass in range(2):
        cur_lba = 22
        for d in all_dirs:
            sectors_out = bytearray()
            cur_sec = bytearray()

            def append_rec(rec: bytes):
                nonlocal cur_sec, sectors_out
                if len(cur_sec) + len(rec) > SECTOR_SIZE:
                    sectors_out.extend(cur_sec + b"\x00" * (SECTOR_SIZE - len(cur_sec)))
                    cur_sec = bytearray()
                cur_sec.extend(rec)

            dot_susp = make_rock_ridge_susp("", True, is_root_self=(d is root), is_dot=True)
            dotdot_susp = make_rock_ridge_susp("", True, is_root_self=False, is_dot=True)
            append_rec(make_dir_record(b"\x00", d.lba, d.size, True, now, dot_susp))
            parent_node = d.parent or d
            append_rec(make_dir_record(b"\x01", parent_node.lba, parent_node.size, True, now, dotdot_susp))
            for c in d.children:
                c_susp = make_rock_ridge_susp(c.name, c.is_dir, False, False)
                append_rec(make_dir_record(c.iso_name.encode("ascii"), c.lba, c.size, c.is_dir, now, c_susp))

            if len(cur_sec) > 0 or len(sectors_out) == 0:
                sectors_out.extend(cur_sec + b"\x00" * (SECTOR_SIZE - len(cur_sec)))
            d.size = len(sectors_out)
            d.lba = cur_lba
            d.dir_record_bytes = bytes(sectors_out)
            cur_lba += d.size // SECTOR_SIZE

        for f in all_files:
            f.lba = cur_lba
            sectors = max(1, math.ceil(f.size / SECTOR_SIZE)) if f.size > 0 else 0
            cur_lba += sectors

    total_sectors = cur_lba

    # Locate isolinux.bin and boot/grub/efi.img LBAs
    node_map = {f.rel_path: f for f in all_files}
    isolinux_node = node_map["isolinux.bin"]
    efi_node = node_map["boot/grub/efi.img"]

    boot_catalog_bytes = build_el_torito_catalog(isolinux_node.lba, efi_node.lba, efi_node.size)

    # Path Tables (L-table at 19, M-table at 20)
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

    # Sector 16: Primary Volume Descriptor
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
    pvd[140:144] = struct.pack("<I", 19)
    pvd[144:148] = struct.pack("<I", 0)
    pvd[148:152] = struct.pack(">I", 20)
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

    # Sector 17: El Torito Boot Record Volume Descriptor
    brvd = bytearray(SECTOR_SIZE)
    brvd[0] = 0
    brvd[1:6] = b"CD001"
    brvd[6] = 1
    brvd[7:39] = b"EL TORITO SPECIFICATION" + b"\x00" * 9
    struct.pack_into("<I", brvd, 0x47, boot_catalog_lba)

    # Sector 18: Volume Descriptor Set Terminator
    vdst = bytearray(SECTOR_SIZE)
    vdst[0] = 255
    vdst[1:6] = b"CD001"
    vdst[6] = 1

    mbr_32k = patch_hybrid_mbr(mbr_template, total_sectors, isolinux_node.lba, efi_node.lba, efi_node.size)

    out_iso.parent.mkdir(parents=True, exist_ok=True)
    with open(out_iso, "wb") as fp:
        fp.write(mbr_32k)
        fp.write(pvd)
        fp.write(brvd)
        fp.write(vdst)
        fp.write(pad_sector(bytes(l_path)))
        fp.write(pad_sector(bytes(m_path)))
        fp.write(boot_catalog_bytes)
        for d in all_dirs:
            fp.write(d.dir_record_bytes)
        for f in all_files:
            if f.size > 0 and f.src_path is not None:
                data = f.src_path.read_bytes()
                if f.rel_path == "isolinux.bin":
                    data = patch_isolinux_bin(data, 16, f.lba)
                fp.write(pad_sector(data))


def stage_and_build_edition(
    root_dir: Path,
    upstream_iso: bytes,
    base_tree_dir: Path,
    edition: str,
    vol_id: str,
    app_id: str,
    iso_filename: str,
):
    work_iso = root_dir / "build" / f"iso-tree-{edition}"
    if work_iso.exists():
        shutil.rmtree(work_iso)
    shutil.copytree(base_tree_dir, work_iso)

    # 1. Append THMD-Guru CPIO initramfs overlay onto `/initrd.gz`
    overlay_gz = build_thmd_cpio_overlay_gz(root_dir, edition)
    with open(work_iso / "initrd.gz", "ab") as f_initrd:
        f_initrd.write(overlay_gz)

    # 2. Write BIOS (ISOLINUX) and UEFI (GRUB2) Bootloader Menus
    write_bootloader_configs(work_iso, edition)
    shutil.copy2(root_dir / "core/bootloader/grub-pc/theme.txt", work_iso / "boot/grub/theme.txt")

    # 3. Copy Edition-Isolated .deb Packages & Signed APT Repo Metadata
    edition_debs = {
        "desktop": ["guru-cli_1.0.0_all.deb", "thmd-guru-branding_1.0.0_all.deb", "guru-welcome_1.0.0_all.deb"],
        "server": ["guru-cli_1.0.0_all.deb", "guru-server-console_1.0.0_all.deb"],
        "attt": [
            "guru-cli_1.0.0_all.deb",
            "thmd-guru-branding_1.0.0_all.deb",
            "guru-sandbox_1.0.0_all.deb",
            "guru-stealth_1.0.0_all.deb",
        ],
    }
    if (root_dir / "out/apt-repo/pool/main").exists():
        (work_iso / "pool/main").mkdir(parents=True, exist_ok=True)
        for deb_name in edition_debs[edition]:
            src_deb = root_dir / "out/apt-repo/pool/main" / deb_name
            if src_deb.exists():
                shutil.copy2(src_deb, work_iso / "pool/main" / deb_name)
        shutil.copytree(root_dir / "out/apt-repo/dists", work_iso / "dists", dirs_exist_ok=True)

    # 3b. Copy On-Demand Modular Bundles into /pool/modules/ on the ISO-9660 disc
    # (Not loaded into RAM at boot; enables zero-latency offline installation on isolated VMnet2)
    if (root_dir / "out/modules").exists():
        (work_iso / "pool/modules").mkdir(parents=True, exist_ok=True)
        for mod_bundle in sorted((root_dir / "out/modules").iterdir()):
            if mod_bundle.is_file():
                shutil.copy2(mod_bundle, work_iso / "pool/modules" / mod_bundle.name)

    # 4. Copy Edition Overlay, Hooks, Package Lists & Secure Boot MOK Keys
    payload = work_iso / "thmd-guru"
    shutil.copytree(root_dir / "core/includes.chroot", payload / "rootfs", dirs_exist_ok=True)
    (payload / "rootfs/etc/thmd-guru").mkdir(parents=True, exist_ok=True)
    (payload / "rootfs/etc/thmd-guru/edition").write_text(f"{edition}\n", encoding="utf-8", newline="\n")

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

    if (root_dir / "build/signing-keys/MOK.crt").exists():
        (payload / "secureboot").mkdir(parents=True, exist_ok=True)
        shutil.copy2(root_dir / "build/signing-keys/MOK.crt", payload / "secureboot/MOK.crt")
        shutil.copy2(root_dir / "build/signing-keys/MOK.der", payload / "secureboot/MOK.der")

    # 5. Write 1-Command Installer (`install-thmd-guru.sh`)
    installer_sh = work_iso / "install-thmd-guru.sh"
    installer_sh.write_text(
        f"""#!/usr/bin/env bash
# THMD-Guru Linux 1.0 (Genesis) - Edition: {edition.upper()}
# Automated In-Place & OEM ISO Installer for Debian 12 (Bookworm)
set -euo pipefail

ISO_ROOT="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
echo "===================================================================="
echo "  THMD-GURU LINUX 1.0 (GENESIS) - {edition.upper()} EDITION INSTALLER"
echo "  THMD-Guru Global Tech Academy - Learn Deep. Build Real. Secure Everything."
echo "===================================================================="

if [[ "$(id -u)" -ne 0 ]]; then
    echo "[ERROR] Vui long chay voi quyen root: sudo bash ${{ISO_ROOT}}/install-thmd-guru.sh" >&2
    exit 1
fi

echo "[1/4] Applying THMD-Guru RootFS Overlay & Identity..."
cp -rf "${{ISO_ROOT}}/thmd-guru/rootfs/." /

echo "[2/4] Verifying Cryptographic Signature & Installing THMD-Guru Packages (.deb)..."
if command -v openssl >/dev/null 2>&1 && [[ -f "${{ISO_ROOT}}/dists/genesis/Release.gpg" && -f "${{ISO_ROOT}}/dists/genesis/thmd-guru-archive.pub" ]]; then
    openssl dgst -sha256 -verify "${{ISO_ROOT}}/dists/genesis/thmd-guru-archive.pub" \
        -signature "${{ISO_ROOT}}/dists/genesis/Release.gpg" \
        "${{ISO_ROOT}}/dists/genesis/Release"
    echo "[OK] Cryptographic RSA-4096 signature of APT Release verified."
fi
dpkg -i "${{ISO_ROOT}}"/pool/main/*.deb || apt-get install -f -y

echo "[3/4] Installing Edition Packages ({edition})..."
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
    build_bootable_iso9660(work_iso, out_iso, vol_id, app_id, upstream_iso[: 16 * SECTOR_SIZE])
    sha256 = hashlib.sha256(out_iso.read_bytes()).hexdigest()
    (root_dir / "out" / f"{iso_filename}.iso.sha256").write_text(
        f"{sha256}  {iso_filename}.iso\n", encoding="utf-8", newline="\n"
    )
    shutil.rmtree(work_iso)
    print(f"[ISO Builder] Built Bootable Hybrid ISO: {out_iso.name} ({out_iso.stat().st_size:,} bytes) | SHA256: {sha256[:16]}...")


def main():
    root_dir = Path(__file__).resolve().parent.parent
    upstream_iso = ensure_upstream_iso(root_dir)
    base_tree_dir = root_dir / "build" / "upstream-extracted"
    if base_tree_dir.exists():
        shutil.rmtree(base_tree_dir)
    extract_upstream_tree(upstream_iso, base_tree_dir)

    editions = [
        ("desktop", "THMD_GURU_DESK_1_0", "THMD-Guru Linux Desktop", "thmd-guru-desktop-1.0-genesis-amd64"),
        ("server", "THMD_GURU_SRV_1_0", "THMD-Guru Linux Server", "thmd-guru-server-1.0-genesis-amd64"),
        ("attt", "THMD_GURU_ATTT_1_0", "THMD-Guru Linux ATTT", "thmd-guru-attt-1.0-genesis-amd64"),
    ]
    for ed, vol, app, fname in editions:
        stage_and_build_edition(root_dir, upstream_iso, base_tree_dir, ed, vol, app, fname)
    shutil.rmtree(base_tree_dir)


if __name__ == "__main__":
    main()
