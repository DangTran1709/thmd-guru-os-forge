#!/usr/bin/env bash
# THMD-Guru OS Forge — Cross-Platform Native .deb & APT Repository Compiler
# Can build valid Debian binary packages (.deb) and APT repository indices directly
# using standard POSIX tar + gzip + ar/awk even on Windows Git Bash without dpkg-dev!
# Owner: os-forge-devops
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEBS_OUT="${ROOT_DIR}/out/debs"
REPO_OUT="${ROOT_DIR}/out/apt-repo"
WORK_ROOT="${ROOT_DIR}/build/portable-deb-work"

rm -rf "${WORK_ROOT}" "${DEBS_OUT}" "${REPO_OUT}"
mkdir -p "${DEBS_OUT}" "${REPO_OUT}/pool/main" "${REPO_OUT}/dists/genesis/main/binary-amd64" "${WORK_ROOT}"

# Write a small helper that packs debian-binary + control.tar.gz + data.tar.gz into a standard GNU ar (.deb) archive
pack_ar_deb() {
    local deb_file="$1"
    shift
    printf "!<arch>\n" > "${deb_file}"
    for member in "$@"; do
        local name size mtime
        name="$(basename "${member}")"
        size="$(wc -c < "${member}" | tr -d '[:space:]')"
        mtime="1730600000"
        printf "%-16s%-12s%-6s%-6s%-8s%-10s\x60\n" "${name}" "${mtime}" "0" "0" "100644" "${size}" >> "${deb_file}"
        cat "${member}" >> "${deb_file}"
        if (( size % 2 == 1 )); then
            printf "\n" >> "${deb_file}"
        fi
    done
}

build_one_deb() {
    local pkg="$1"
    local ver="$2"
    local section="$3"
    local deps="$4"
    local desc="$5"
    local stage_dir="${WORK_ROOT}/${pkg}/data"
    local ctrl_dir="${WORK_ROOT}/${pkg}/control"
    mkdir -p "${stage_dir}/usr/share/doc/${pkg}" "${ctrl_dir}"

    cp -f "${ROOT_DIR}/packages/${pkg}/debian/copyright" "${stage_dir}/usr/share/doc/${pkg}/copyright"
    gzip -9nc "${ROOT_DIR}/packages/${pkg}/debian/changelog" > "${stage_dir}/usr/share/doc/${pkg}/changelog.gz"

    case "${pkg}" in
        guru-cli)
            mkdir -p "${stage_dir}/usr/bin" "${stage_dir}/usr/lib/guru/commands" \
                     "${stage_dir}/usr/share/bash-completion/completions" \
                     "${stage_dir}/usr/share/man/man1" "${stage_dir}/usr/share/thmd-guru/labs"
            cp -f "${ROOT_DIR}/packages/guru-cli/src/guru" "${stage_dir}/usr/bin/guru"
            chmod 0755 "${stage_dir}/usr/bin/guru"
            cp -f "${ROOT_DIR}/packages/guru-cli/completion/guru" "${stage_dir}/usr/share/bash-completion/completions/guru"
            gzip -9nc "${ROOT_DIR}/packages/guru-cli/man/guru.1" > "${stage_dir}/usr/share/man/man1/guru.1.gz"
            cp -rf "${ROOT_DIR}/packages/guru-cli/labs/." "${stage_dir}/usr/share/thmd-guru/labs/"
            ;;
        thmd-guru-branding)
            mkdir -p "${stage_dir}/usr/share/color-schemes" "${stage_dir}/usr/share/konsole" \
                     "${stage_dir}/etc/sddm.conf.d" "${stage_dir}/usr/share/sddm/themes/breeze" \
                     "${stage_dir}/usr/share/pixmaps" "${stage_dir}/usr/share/backgrounds/thmd-guru" \
                     "${stage_dir}/usr/share/plymouth/themes/thmd-guru"
            cp -f "${ROOT_DIR}/packages/thmd-guru-branding/src/ThmdGuruSapphire.colors" "${stage_dir}/usr/share/color-schemes/"
            cp -f "${ROOT_DIR}/packages/thmd-guru-branding/src/ThmdGuru.profile" "${stage_dir}/usr/share/konsole/"
            cp -f "${ROOT_DIR}/packages/thmd-guru-branding/src/ThmdGuru.colorscheme" "${stage_dir}/usr/share/konsole/"
            cp -f "${ROOT_DIR}/packages/thmd-guru-branding/src/sddm-thmd-guru.conf" "${stage_dir}/etc/sddm.conf.d/"
            cp -f "${ROOT_DIR}/packages/thmd-guru-branding/src/theme.conf.user" "${stage_dir}/usr/share/sddm/themes/breeze/"
            cp -f "${ROOT_DIR}/core/branding/thmd-guru-logo.svg" "${stage_dir}/usr/share/pixmaps/"
            cp -f "${ROOT_DIR}/core/branding/wallpaper-sapphire-gold.svg" "${stage_dir}/usr/share/backgrounds/thmd-guru/"
            cp -rf "${ROOT_DIR}/core/branding/plymouth/thmd-guru/." "${stage_dir}/usr/share/plymouth/themes/thmd-guru/"
            cp -f "${ROOT_DIR}/packages/thmd-guru-branding/debian/postinst" "${ctrl_dir}/postinst"
            chmod 0755 "${ctrl_dir}/postinst"
            ;;
        guru-welcome)
            mkdir -p "${stage_dir}/usr/bin" "${stage_dir}/usr/lib/guru/commands" \
                     "${stage_dir}/usr/share/applications" "${stage_dir}/etc/xdg/autostart"
            cp -f "${ROOT_DIR}/packages/guru-welcome/src/guru-welcome" "${stage_dir}/usr/bin/guru-welcome"
            cp -f "${ROOT_DIR}/packages/guru-welcome/src/welcome-plugin" "${stage_dir}/usr/lib/guru/commands/welcome"
            chmod 0755 "${stage_dir}/usr/bin/guru-welcome" "${stage_dir}/usr/lib/guru/commands/welcome"
            cp -f "${ROOT_DIR}/packages/guru-welcome/src/guru-welcome.desktop" "${stage_dir}/usr/share/applications/"
            cp -f "${ROOT_DIR}/packages/guru-welcome/src/guru-welcome.desktop" "${stage_dir}/etc/xdg/autostart/"
            ;;
        guru-server-console)
            mkdir -p "${stage_dir}/usr/lib/guru/commands"
            cp -f "${ROOT_DIR}/packages/guru-server-console/src/console-plugin" "${stage_dir}/usr/lib/guru/commands/console"
            chmod 0755 "${stage_dir}/usr/lib/guru/commands/console"
            ;;
        guru-sandbox)
            mkdir -p "${stage_dir}/usr/lib/guru/commands"
            cp -f "${ROOT_DIR}/packages/guru-sandbox/src/sandbox-plugin" "${stage_dir}/usr/lib/guru/commands/sandbox"
            chmod 0755 "${stage_dir}/usr/lib/guru/commands/sandbox"
            ;;
        guru-stealth)
            mkdir -p "${stage_dir}/usr/lib/guru/commands"
            cp -f "${ROOT_DIR}/packages/guru-stealth/src/stealth-plugin" "${stage_dir}/usr/lib/guru/commands/stealth"
            chmod 0755 "${stage_dir}/usr/lib/guru/commands/stealth"
            ;;
    esac

    local inst_kb
    inst_kb="$(du -sk "${stage_dir}" | awk '{print $1}')"
    cat << EOF > "${ctrl_dir}/control"
Package: ${pkg}
Version: ${ver}
Section: ${section}
Priority: optional
Architecture: all
Depends: ${deps}
Installed-Size: ${inst_kb}
Maintainer: THMD-Guru Global Tech Academy <engineering@thmd-guru.academy>
Homepage: https://thmd-guru.academy
Description: ${desc}
EOF

    (cd "${stage_dir}" && find . -type f -exec md5sum {} + | sed 's| \./| |' > "${ctrl_dir}/md5sums")

    printf "2.0\n" > "${WORK_ROOT}/${pkg}/debian-binary"
    (cd "${ctrl_dir}" && tar --owner=0 --group=0 -czf "${WORK_ROOT}/${pkg}/control.tar.gz" .)
    (cd "${stage_dir}" && tar --owner=0 --group=0 -czf "${WORK_ROOT}/${pkg}/data.tar.gz" .)

    local out_deb="${DEBS_OUT}/${pkg}_${ver}_all.deb"
    pack_ar_deb "${out_deb}" \
        "${WORK_ROOT}/${pkg}/debian-binary" \
        "${WORK_ROOT}/${pkg}/control.tar.gz" \
        "${WORK_ROOT}/${pkg}/data.tar.gz"

    cp -f "${out_deb}" "${REPO_OUT}/pool/main/"
    local size sha256 md5
    size="$(wc -c < "${out_deb}" | tr -d '[:space:]')"
    sha256="$(sha256sum "${out_deb}" | awk '{print $1}')"
    md5="$(md5sum "${out_deb}" | awk '{print $1}')"

    cat << EOF >> "${REPO_OUT}/dists/genesis/main/binary-amd64/Packages"
Package: ${pkg}
Version: ${ver}
Architecture: all
Maintainer: THMD-Guru Global Tech Academy <engineering@thmd-guru.academy>
Installed-Size: ${inst_kb}
Depends: ${deps}
Filename: pool/main/${pkg}_${ver}_all.deb
Size: ${size}
MD5sum: ${md5}
SHA256: ${sha256}
Section: ${section}
Priority: optional
Description: ${desc}

EOF
    echo "[Portable DEB Builder] Built ${pkg}_${ver}_all.deb (${size} bytes)"
}

build_one_deb "guru-cli" "1.0.0" "admin" "bash, coreutils, procps" "Unified system, security, and academy lab CLI for THMD-Guru Linux"
build_one_deb "thmd-guru-branding" "1.0.0" "misc" "plymouth" "Official Cyber Sapphire and Royal Gold brand assets for THMD-Guru Linux"
build_one_deb "guru-welcome" "1.0.0" "misc" "python3, python3-gi, gir1.2-gtk-3.0, policykit-1" "Welcome Center and Academy Lab Provisioner for THMD-Guru Linux"
build_one_deb "guru-server-console" "1.0.0" "admin" "bash" "Server operations console plugin for THMD-Guru Linux Server"
build_one_deb "guru-sandbox" "1.0.0" "security" "bash, firejail, bubblewrap" "Application sandboxing plugin for THMD-Guru Linux ATTT"
build_one_deb "guru-stealth" "1.0.0" "security" "bash, network-manager, nftables" "Network privacy and stealth lockdown plugin for THMD-Guru Linux ATTT"

gzip -9nc "${REPO_OUT}/dists/genesis/main/binary-amd64/Packages" > "${REPO_OUT}/dists/genesis/main/binary-amd64/Packages.gz"

pkg_raw_size="$(wc -c < "${REPO_OUT}/dists/genesis/main/binary-amd64/Packages" | tr -d '[:space:]')"
pkg_gz_size="$(wc -c < "${REPO_OUT}/dists/genesis/main/binary-amd64/Packages.gz" | tr -d '[:space:]')"
pkg_raw_sha="$(sha256sum "${REPO_OUT}/dists/genesis/main/binary-amd64/Packages" | awk '{print $1}')"
pkg_gz_sha="$(sha256sum "${REPO_OUT}/dists/genesis/main/binary-amd64/Packages.gz" | awk '{print $1}')"

cat << EOF > "${REPO_OUT}/dists/genesis/Release"
Origin: THMD-Guru Global Tech Academy
Label: THMD-Guru Linux Official Repository
Suite: genesis
Codename: genesis
Version: 1.0
Architectures: amd64 all
Components: main
Description: Official APT repository for THMD-Guru Linux 1.0 (Genesis)
Date: $(date -Ru)
SHA256:
 ${pkg_raw_sha} ${pkg_raw_size} main/binary-amd64/Packages
 ${pkg_gz_sha} ${pkg_gz_size} main/binary-amd64/Packages.gz
EOF

rm -rf "${WORK_ROOT}"
echo "[Portable DEB Builder] All 6 .deb packages and APT repository generated in ${ROOT_DIR}/out/ !"
