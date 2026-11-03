#!/usr/bin/env python3
"""
THMD-Guru OS Forge — Portable Pure-Python Debian (.deb) & Signed APT Repository Builder
Builds standard Debian 2.0 `ar` binary packages (`debian-binary` + `control.tar.gz` + `data.tar.gz`),
generates APT Repository indices (`Packages`, `Packages.gz`, `Release`), and signs `Release.gpg`
using RSA-4096 (`build/signing-keys/MOK.key` / `thmd-guru-archive.pub`).
"""
import gzip
import hashlib
import io
import shutil
import subprocess
import tarfile
from pathlib import Path

MTIME = 1793700000


def ar_entry(name: str, data: bytes) -> bytes:
    header = f"{name:<16}{MTIME:<12}{0:<6}{0:<6}{0o100644:<8}{len(data):<10}`\n".encode("ascii")
    out = bytearray(header + data)
    if len(out) % 2 == 1:
        out.append(0x0A)
    return bytes(out)


def make_tar_gz(files: dict[str, tuple[bytes, int]]) -> bytes:
    buf = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=buf, compresslevel=9, mtime=MTIME) as gz:
        with tarfile.open(mode="w", fileobj=gz, format=tarfile.GNU_FORMAT) as tf:
            dirs_added: set[str] = set()
            for rel_path in sorted(files.keys()):
                parts = rel_path.strip("./").split("/")
                for i in range(1, len(parts)):
                    d = "./" + "/".join(parts[:i])
                    if d not in dirs_added:
                        ti = tarfile.TarInfo(name=d + "/")
                        ti.type = tarfile.DIRTYPE
                        ti.mode = 0o755
                        ti.mtime = MTIME
                        tf.addfile(ti)
                        dirs_added.add(d)
                content, mode = files[rel_path]
                norm_name = "./" + rel_path.strip("./")
                ti = tarfile.TarInfo(name=norm_name)
                ti.size = len(content)
                ti.mode = mode
                ti.mtime = MTIME
                tf.addfile(ti, io.BytesIO(content))
    return buf.getvalue()


def build_deb(pkg_name: str, version: str, desc: str, depends: str, data_files: dict[str, tuple[bytes, int]], out_dir: Path) -> Path:
    installed_kb = max(1, sum(len(v[0]) for v in data_files.values()) // 1024 + 4)
    control_txt = (
        f"Package: {pkg_name}\n"
        f"Version: {version}\n"
        f"Section: admin\n"
        f"Priority: optional\n"
        f"Architecture: all\n"
        f"Depends: {depends}\n"
        f"Installed-Size: {installed_kb}\n"
        f"Maintainer: THMD-Guru OS Forge <forge@thmd-guru.academy>\n"
        f"Description: {desc}\n"
    ).encode("utf-8")

    md5_lines = []
    for k in sorted(data_files.keys()):
        h = hashlib.md5(data_files[k][0]).hexdigest()
        md5_lines.append(f"{h}  {k.strip('./')}\n")
    md5sums_txt = "".join(md5_lines).encode("utf-8")

    control_tgz = make_tar_gz({"control": (control_txt, 0o644), "md5sums": (md5sums_txt, 0o644)})
    data_tgz = make_tar_gz(data_files)

    deb_bytes = (
        b"!<arch>\n"
        + ar_entry("debian-binary", b"2.0\n")
        + ar_entry("control.tar.gz", control_tgz)
        + ar_entry("data.tar.gz", data_tgz)
    )
    out_path = out_dir / f"{pkg_name}_{version}_all.deb"
    out_path.write_bytes(deb_bytes)
    return out_path


def main():
    root = Path(__file__).resolve().parent.parent
    debs_dir = root / "out" / "debs"
    pool_dir = root / "out" / "apt-repo" / "pool" / "main"
    dists_dir = root / "out" / "apt-repo" / "dists" / "genesis"
    bin_dir = dists_dir / "main" / "binary-amd64"
    debs_dir.mkdir(parents=True, exist_ok=True)
    pool_dir.mkdir(parents=True, exist_ok=True)
    bin_dir.mkdir(parents=True, exist_ok=True)

    guru_bytes = (root / "packages/guru-cli/src/guru").read_bytes().replace(b"\r\n", b"\n")
    guru_files: dict[str, tuple[bytes, int]] = {
        "usr/bin/guru": (guru_bytes, 0o755),
        "usr/bin/THMD-guru-ai": (guru_bytes, 0o755),
        "usr/share/bash-completion/completions/guru": (
            (root / "packages/guru-cli/completion/guru").read_bytes().replace(b"\r\n", b"\n"),
            0o644,
        ),
    }
    for lab_dir in sorted((root / "packages/guru-cli/labs").iterdir()):
        if lab_dir.is_dir():
            for lf in sorted(lab_dir.iterdir()):
                if lf.is_file():
                    mode = 0o755 if lf.suffix in (".py", ".sh") else 0o644
                    guru_files[f"usr/share/thmd-guru/labs/{lab_dir.name}/{lf.name}"] = (
                        lf.read_bytes().replace(b"\r\n", b"\n"),
                        mode,
                    )

    pkgs_spec = [
        (
            "guru-cli",
            "1.0.0",
            "THMD-Guru Linux unified command-line tool (THMD-guru-ai & guru)",
            "bash (>= 5), coreutils, procps, iproute2",
            guru_files,
        ),
        (
            "thmd-guru-branding",
            "1.0.0",
            "THMD-Guru Linux Cyber Sapphire & Royal Gold artwork and themes",
            "guru-cli",
            {
                "usr/share/thmd-guru/branding/thmd-guru-logo.svg": (
                    (root / "core/branding/thmd-guru-logo.svg").read_bytes().replace(b"\r\n", b"\n"),
                    0o644,
                ),
                "usr/share/backgrounds/thmd-guru/wallpaper-sapphire-gold.svg": (
                    (root / "core/branding/wallpaper-sapphire-gold.svg").read_bytes().replace(b"\r\n", b"\n"),
                    0o644,
                ),
            },
        ),
        (
            "guru-welcome",
            "1.0.0",
            "THMD-Guru Linux Desktop Welcome Center & NCKH Lab Provisioner",
            "guru-cli, python3",
            {
                "usr/bin/guru-welcome": (
                    (root / "packages/guru-welcome/src/guru-welcome").read_bytes().replace(b"\r\n", b"\n"),
                    0o755,
                ),
                "usr/lib/guru/commands/welcome": (
                    (root / "packages/guru-welcome/src/welcome-plugin").read_bytes().replace(b"\r\n", b"\n"),
                    0o755,
                ),
            },
        ),
        (
            "guru-server-console",
            "1.0.0",
            "THMD-Guru Linux Server Console & Hardening Inspector",
            "guru-cli",
            {
                "usr/lib/guru/commands/console": (
                    (root / "packages/guru-server-console/src/console-plugin").read_bytes().replace(b"\r\n", b"\n"),
                    0o755,
                ),
            },
        ),
        (
            "guru-sandbox",
            "1.0.0",
            "THMD-Guru Linux ATTT Fail-Closed Malware & Tool Sandbox",
            "guru-cli",
            {
                "usr/lib/guru/commands/sandbox": (
                    (root / "packages/guru-sandbox/src/sandbox-plugin").read_bytes().replace(b"\r\n", b"\n"),
                    0o755,
                ),
            },
        ),
        (
            "guru-stealth",
            "1.0.0",
            "THMD-Guru Linux ATTT L2/L3 OPSEC Stealth & MAC Spoofing Engine",
            "guru-cli",
            {
                "usr/lib/guru/commands/stealth": (
                    (root / "packages/guru-stealth/src/stealth-plugin").read_bytes().replace(b"\r\n", b"\n"),
                    0o755,
                ),
            },
        ),
    ]

    packages_entries = []
    for name, ver, desc, deps, dfiles in pkgs_spec:
        deb_p = build_deb(name, ver, desc, deps, dfiles, debs_dir)
        shutil.copy2(deb_p, pool_dir / deb_p.name)
        raw = deb_p.read_bytes()
        packages_entries.append(
            f"Package: {name}\n"
            f"Version: {ver}\n"
            f"Architecture: all\n"
            f"Maintainer: THMD-Guru OS Forge <forge@thmd-guru.academy>\n"
            f"Depends: {deps}\n"
            f"Filename: pool/main/{deb_p.name}\n"
            f"Size: {len(raw)}\n"
            f"MD5sum: {hashlib.md5(raw).hexdigest()}\n"
            f"SHA256: {hashlib.sha256(raw).hexdigest()}\n"
            f"Section: admin\n"
            f"Priority: optional\n"
            f"Description: {desc}\n\n"
        )
        print(f"[Deb Builder] Built {deb_p.name} ({len(raw):,} bytes)")

    pkgs_bytes = "".join(packages_entries).encode("utf-8")
    (bin_dir / "Packages").write_bytes(pkgs_bytes)
    pkgs_gz_buf = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=pkgs_gz_buf, compresslevel=9, mtime=MTIME) as gz:
        gz.write(pkgs_bytes)
    pkgs_gz_bytes = pkgs_gz_buf.getvalue()
    (bin_dir / "Packages.gz").write_bytes(pkgs_gz_bytes)

    release_txt = (
        "Origin: THMD-Guru Global Tech Academy\n"
        "Label: THMD-Guru Linux Official Repository\n"
        "Suite: genesis\n"
        "Codename: genesis\n"
        "Version: 1.0\n"
        "Architectures: amd64 all\n"
        "Components: main\n"
        "Description: Official APT repository for THMD-Guru Linux 1.0 (Genesis)\n"
        "SHA256:\n"
        f" {hashlib.sha256(pkgs_bytes).hexdigest()} {len(pkgs_bytes):8d} main/binary-amd64/Packages\n"
        f" {hashlib.sha256(pkgs_gz_bytes).hexdigest()} {len(pkgs_gz_bytes):8d} main/binary-amd64/Packages.gz\n"
    ).encode("utf-8")
    release_path = dists_dir / "Release"
    release_path.write_bytes(release_txt)

    priv_key = root / "build/signing-keys/MOK.key"
    pub_key = root / "build/signing-keys/thmd-guru-archive.pub"
    if priv_key.exists():
        openssl_exe = shutil.which("openssl") or r"C:\Program Files\Git\usr\bin\openssl.exe"
        subprocess.run(
            [openssl_exe, "dgst", "-sha256", "-sign", str(priv_key), "-out", str(dists_dir / "Release.gpg"), str(release_path)],
            check=True,
        )
        if pub_key.exists():
            shutil.copy2(pub_key, dists_dir / "thmd-guru-archive.pub")
        print("[APT Repo] Signed dists/genesis/Release.gpg with RSA-4096 key.")


if __name__ == "__main__":
    main()

