#!/usr/bin/env bash
# THMD-Guru OS Forge — QEMU Boot Verification Runner (KVM & Software TCG Emulation)
# Supports both interactive GUI mode and headless automated self-test mode (--autotest).
# Owner: os-forge-devops
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ISO_PATH="${1:-${ROOT_DIR}/out/thmd-guru-desktop-1.0-genesis-amd64.iso}"
MODE="${2:-gui}"
RAM_MB="${RAM_MB:-1024}"
CPUS="${CPUS:-2}"

if [[ ! -f "${ISO_PATH}" ]]; then
    echo "Usage: bash tests/run-qemu.sh <path-to-iso> [gui|autotest]" >&2
    exit 1
fi

QEMU_BIN="qemu-system-x86_64"
QEMU_SHARE=()
WIN_TEMP_QEMU="/c/Users/${USERNAME:-asust}/AppData/Local/Temp/qemu-portable"
if [[ -x "${WIN_TEMP_QEMU}/qemu-system-x86_64.exe" ]]; then
    QEMU_BIN="${WIN_TEMP_QEMU}/qemu-system-x86_64.exe"
    QEMU_SHARE=(-L "${WIN_TEMP_QEMU}/share")
elif [[ -x "${ROOT_DIR}/build/qemu/qemu-system-x86_64.exe" ]]; then
    QEMU_BIN="${ROOT_DIR}/build/qemu/qemu-system-x86_64.exe"
    QEMU_SHARE=(-L "${ROOT_DIR}/build/qemu/share")
elif [[ -x "/c/Program Files/qemu/qemu-system-x86_64.exe" ]]; then
    QEMU_BIN="/c/Program Files/qemu/qemu-system-x86_64.exe"
fi

ACCEL_ARGS=(-accel tcg)
if [[ -e /dev/kvm ]]; then
    ACCEL_ARGS=(-enable-kvm -cpu host)
fi

if [[ "${MODE}" == "autotest" ]]; then
    echo "[THMD-Guru QEMU AutoTest] Booting Linux Kernel & Initramfs from ${ISO_PATH}..."
    exec "${QEMU_BIN}" \
        "${QEMU_SHARE[@]}" \
        "${ACCEL_ARGS[@]}" \
        -m "${RAM_MB}" \
        -smp "${CPUS}" \
        -cdrom "${ISO_PATH}" \
        -boot d \
        -display none \
        -serial stdio \
        -no-reboot
fi

echo "[THMD-Guru QEMU Runner] Booting ${ISO_PATH} (${RAM_MB}MB RAM, ${CPUS} vCPUs)..."
exec "${QEMU_BIN}" \
    "${QEMU_SHARE[@]}" \
    "${ACCEL_ARGS[@]}" \
    -m "${RAM_MB}" \
    -smp "${CPUS}" \
    -cdrom "${ISO_PATH}" \
    -boot d \
    -vga std \
    -net nic,model=e1000 \
    -net user,hostfwd=tcp::2222-:22,hostfwd=tcp::9090-:9090
