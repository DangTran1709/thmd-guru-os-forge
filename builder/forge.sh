#!/usr/bin/env bash
# THMD-Guru OS Forge — Master Distribution Build Orchestrator
# Builds native .deb packages, merges core + edition overlays, and runs live-build.
# Owner: os-forge-devops
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_ROOT="${BUILD_ROOT:-${ROOT_DIR}/build}"
OUT_DIR="${OUT_DIR:-${ROOT_DIR}/out}"

usage() {
    cat << 'EOF'
THMD-Guru OS Forge — Automated Linux Distribution Factory
Usage:
  bash builder/forge.sh packages             Build all THMD-Guru .deb packages
  bash builder/forge.sh stage <edition>      Assemble live-build tree without building ISO
  bash builder/forge.sh iso <edition>        Build bootable .iso for <desktop|server|attt>
  bash builder/forge.sh all                  Build all 3 editions (Desktop, Server, ATTT)
  bash builder/forge.sh clean                Remove temporary build directories
EOF
}

sync_branding_assets() {
    local pkg_brand="${ROOT_DIR}/packages/thmd-guru-branding"
    mkdir -p "${pkg_brand}/assets" "${pkg_brand}/plymouth"
    cp -f "${ROOT_DIR}/core/branding/thmd-guru-logo.svg" "${pkg_brand}/assets/"
    cp -f "${ROOT_DIR}/core/branding/wallpaper-sapphire-gold.svg" "${pkg_brand}/assets/"
    cp -rf "${ROOT_DIR}/core/branding/plymouth/thmd-guru" "${pkg_brand}/plymouth/"
}

build_packages() {
    echo "[OS Forge] Building native Debian packages (.deb)..."
    sync_branding_assets
    mkdir -p "${BUILD_ROOT}/debs"
    for pkg_dir in "${ROOT_DIR}"/packages/*; do
        [[ -d "${pkg_dir}/debian" ]] || continue
        local pkg_name
        pkg_name="$(basename "${pkg_dir}")"
        echo "  -> Packaging ${pkg_name}..."
        local tmp_pkg="${BUILD_ROOT}/pkg-work/${pkg_name}"
        rm -rf "${tmp_pkg}"
        mkdir -p "${tmp_pkg}"
        cp -rf "${pkg_dir}/." "${tmp_pkg}/"
        chmod +x "${tmp_pkg}/debian/rules" 2>/dev/null || true
        find "${tmp_pkg}" -type f -path "*/src/*" -exec chmod +x {} + 2>/dev/null || true
        (cd "${tmp_pkg}" && dpkg-buildpackage -us -uc -b)
        mv "${BUILD_ROOT}/pkg-work/"*.deb "${BUILD_ROOT}/debs/" 2>/dev/null || true
    done
    echo "[OS Forge] Packages built in ${BUILD_ROOT}/debs/"
}

stage_edition() {
    local ed="$1"
    local ed_dir="${ROOT_DIR}/editions/${ed}"
    if [[ ! -f "${ed_dir}/edition.conf" ]]; then
        echo "[ERROR] Unknown edition: ${ed} (missing ${ed_dir}/edition.conf)" >&2
        exit 1
    fi

    # shellcheck disable=SC1090
    source "${ed_dir}/edition.conf"

    local work="${BUILD_ROOT}/live-${EDITION}"
    echo "[OS Forge] Staging live-build workspace for '${EDITION}' at ${work}..."
    rm -rf "${work}"
    mkdir -p "${work}"
    cd "${work}"

    if command -v lb >/dev/null 2>&1; then
        lb config \
            --mode debian \
            --distribution bookworm \
            --architectures amd64 \
            --linux-flavours amd64 \
            --binary-images iso-hybrid \
            --apt-indices false \
            --apt-recommends true \
            --security true \
            --updates true \
            --iso-preparer "THMD-Guru OS Forge" \
            "${LB_ARGS[@]}"
    else
        mkdir -p config/{package-lists,hooks/live,includes.chroot,includes.binary,bootloaders,packages.chroot}
    fi

    # 1. Overlay Core layer
    cp -rf "${ROOT_DIR}/core/package-lists/." config/package-lists/
    cp -rf "${ROOT_DIR}/core/hooks/live/." config/hooks/live/
    cp -rf "${ROOT_DIR}/core/includes.chroot/." config/includes.chroot/
    mkdir -p config/includes.chroot/usr/share/thmd-guru/sysctl
    cp -rf "${ROOT_DIR}/core/kernel/sysctl/." config/includes.chroot/usr/share/thmd-guru/sysctl/
    mkdir -p config/bootloaders
    cp -rf "${ROOT_DIR}/core/bootloader/." config/bootloaders/

    # 2. Overlay Edition layer
    [[ -d "${ed_dir}/package-lists" ]] && cp -rf "${ed_dir}/package-lists/." config/package-lists/
    [[ -d "${ed_dir}/hooks/live" ]] && cp -rf "${ed_dir}/hooks/live/." config/hooks/live/
    [[ -d "${ed_dir}/includes.chroot" ]] && cp -rf "${ed_dir}/includes.chroot/." config/includes.chroot/
    [[ -d "${ed_dir}/includes.binary" ]] && cp -rf "${ed_dir}/includes.binary/." config/includes.binary/
    chmod +x config/hooks/live/*.hook.chroot 2>/dev/null || true

    # 3. Copy built .deb packages (Strictly isolated per edition to prevent dependency pollution)
    mkdir -p config/packages.chroot
    local -a allowed_pkgs=("guru-cli")
    case "${EDITION}" in
        desktop) allowed_pkgs+=("thmd-guru-branding" "guru-welcome") ;;
        server)  allowed_pkgs+=("guru-server-console") ;;
        attt)    allowed_pkgs+=("thmd-guru-branding" "guru-sandbox" "guru-stealth") ;;
    esac
    for pkg in "${allowed_pkgs[@]}"; do
        if [[ -f "${BUILD_ROOT}/debs/${pkg}_1.0.0_all.deb" ]]; then
            cp -f "${BUILD_ROOT}/debs/${pkg}_1.0.0_all.deb" config/packages.chroot/
        elif [[ -f "${OUT_DIR}/debs/${pkg}_1.0.0_all.deb" ]]; then
            cp -f "${OUT_DIR}/debs/${pkg}_1.0.0_all.deb" config/packages.chroot/
        fi
    done

    echo "[OS Forge] Staged edition '${EDITION}' successfully."
}

build_iso() {
    local ed="$1"
    build_packages
    stage_edition "${ed}"
    # shellcheck disable=SC1090
    source "${ROOT_DIR}/editions/${ed}/edition.conf"
    local work="${BUILD_ROOT}/live-${EDITION}"
    cd "${work}"
    echo "[OS Forge] Running lb build for ${ISO_NAME}.iso..."
    lb build
    mkdir -p "${OUT_DIR}"
    mv live-image-amd64.hybrid.iso "${OUT_DIR}/${ISO_NAME}.iso"
    sha256sum "${OUT_DIR}/${ISO_NAME}.iso" > "${OUT_DIR}/${ISO_NAME}.iso.sha256"
    echo "[OS Forge] SUCCESS: ${OUT_DIR}/${ISO_NAME}.iso"
}

cmd="${1:-help}"
shift || true

case "${cmd}" in
    packages) build_packages ;;
    stage)    stage_edition "${1:-desktop}" ;;
    iso)      build_iso "${1:-desktop}" ;;
    all)
        for e in desktop server attt; do
            build_iso "${e}"
        done
        ;;
    clean)    rm -rf "${BUILD_ROOT}" ;;
    *)        usage ;;
esac
