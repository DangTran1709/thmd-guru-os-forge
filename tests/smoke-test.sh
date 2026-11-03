#!/usr/bin/env bash
# THMD-Guru OS Forge — Automated Repository & Package Integrity Smoke Test
# Owner: os-forge-devops
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

echo "[THMD-Guru Smoke Test] Validating repository structure, configs, and scripts..."

REQUIRED_FILES=(
    "core/includes.chroot/etc/os-release"
    "core/includes.chroot/usr/lib/os-release"
    "core/includes.chroot/etc/sysctl.d/90-thmd-guru-base.conf"
    "core/kernel/sysctl/91-desktop.conf"
    "core/kernel/sysctl/91-server.conf"
    "core/kernel/sysctl/91-attt.conf"
    "core/package-lists/base.list.chroot"
    "core/hooks/live/0100-thmd-guru-core.hook.chroot"
    "core/bootloader/grub-pc/theme.txt"
    "core/bootloader/grub-pc/grub.cfg"
    "core/branding/thmd-guru-logo.svg"
    "core/branding/wallpaper-sapphire-gold.svg"
    "packages/guru-cli/src/guru"
    "packages/thmd-guru-branding/debian/control"
    "packages/guru-welcome/src/guru-welcome"
    "packages/guru-server-console/src/console-plugin"
    "packages/guru-sandbox/src/sandbox-plugin"
    "packages/guru-stealth/src/stealth-plugin"
    "editions/desktop/edition.conf"
    "editions/server/edition.conf"
    "editions/attt/edition.conf"
    "builder/Dockerfile"
    "builder/forge.sh"
    "builder/build-apt-repo.sh"
    "packages/thmd-guru-branding/src/ThmdGuru.profile"
    "packages/thmd-guru-branding/src/ThmdGuru.colorscheme"
    "editions/server/includes.chroot/etc/cloud/cloud.cfg.d/90_thmd_guru.cfg"
    "editions/attt/includes.chroot/etc/xdg/menus/applications-merged/thmd-guru-attt.menu"
    ".github/workflows/os-forge-ci.yml"
)

for f in "${REQUIRED_FILES[@]}"; do
    if [[ ! -f "${f}" ]]; then
        echo "[FAIL] Missing required file: ${f}" >&2
        exit 1
    fi
done
echo "[PASS] All ${#REQUIRED_FILES[@]} core & edition files present."

# Validate bash syntax of all scripts and hooks
while IFS= read -r -d '' sh_file; do
    bash -n "${sh_file}"
done < <(find core editions packages builder tests -type f \( -name "*.sh" -o -name "*.hook.chroot" -o -name "*-plugin" -o -name "guru" \) -print0)
echo "[PASS] All Bash scripts, hooks, and CLI plugins passed syntax verification (bash -n)."

# Test `guru` CLI directly
output="$("${ROOT_DIR}/packages/guru-cli/src/guru" help)"
grep -q "THMD-Guru" <<< "${output}"
echo "[PASS] guru CLI help command verified."

echo "[THMD-Guru Smoke Test] ALL CHECKS PASSED SUCCESSFULLY!"
