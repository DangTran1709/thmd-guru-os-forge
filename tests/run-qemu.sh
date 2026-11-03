#!/usr/bin/env bash
# THMD-Guru OS Forge — QEMU/KVM Boot Verification Runner
# Owner: os-forge-devops
set -euo pipefail

ISO_PATH="${1:-out/thmd-guru-desktop-1.0-genesis-amd64.iso}"
RAM_MB="${RAM_MB:-4096}"
CPUS="${CPUS:-4}"

if [[ ! -f "${ISO_PATH}" ]]; then
    echo "Usage: bash tests/run-qemu.sh <path-to-iso>" >&2
    exit 1
fi

ACCEL_ARGS=()
if [[ -e /dev/kvm ]]; then
    ACCEL_ARGS=(-enable-kvm -cpu host)
fi

echo "[THMD-Guru QEMU Runner] Booting ${ISO_PATH} (${RAM_MB}MB RAM, ${CPUS} vCPUs)..."
exec qemu-system-x86_64 \
    "${ACCEL_ARGS[@]}" \
    -m "${RAM_MB}" \
    -smp "${CPUS}" \
    -cdrom "${ISO_PATH}" \
    -boot d \
    -vga virtio \
    -display default,show-cursor=on \
    -net nic,model=virtio \
    -net user,hostfwd=tcp::2222-:22,hostfwd=tcp::9090-:9090
