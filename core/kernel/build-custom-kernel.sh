#!/usr/bin/env bash
# THMD-Guru Linux — Optional Custom Kernel Builder (bindeb-pkg)
# Owner: chief-os-architect
set -euo pipefail

KERNEL_VER="${KERNEL_VER:-6.6.62}"
JOBS="${JOBS:-$(nproc)}"
WORKDIR="${WORKDIR:-/tmp/thmd-guru-kernel-build}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[THMD-Guru Kernel Forge] Building Linux ${KERNEL_VER}-thmd-guru..."
mkdir -p "${WORKDIR}"
cd "${WORKDIR}"

if [[ ! -f "linux-${KERNEL_VER}.tar.xz" ]]; then
    curl -fLO "https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-${KERNEL_VER}.tar.xz"
fi

rm -rf "linux-${KERNEL_VER}"
tar -xf "linux-${KERNEL_VER}.tar.xz"
cd "linux-${KERNEL_VER}"

if [[ -f "/boot/config-$(uname -r)" ]]; then
    cp "/boot/config-$(uname -r)" .config
else
    make defconfig
fi

./scripts/kconfig/merge_config.sh -m .config "${SCRIPT_DIR}/config-fragments/thmd-guru-hardened.config"
scripts/config --disable SYSTEM_TRUSTED_KEYS
scripts/config --disable SYSTEM_REVOCATION_KEYS

make -j"${JOBS}" bindeb-pkg LOCALVERSION=-thmd-guru KDEB_PKGVERSION="$(make kernelversion)-1thmdguru1"
echo "[THMD-Guru Kernel Forge] Done! .deb packages generated in ${WORKDIR}"
