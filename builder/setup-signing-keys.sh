#!/usr/bin/env bash
# THMD-Guru OS Forge — GPG Repository & UEFI Secure Boot MOK Key Generator
# Owner: chief-os-architect & os-forge-devops
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
KEYS_DIR="${KEYS_DIR:-${ROOT_DIR}/build/signing-keys}"
mkdir -p "${KEYS_DIR}"

echo "[THMD-Guru Keygen] Generating UEFI Secure Boot MOK X.509 keypair..."
if command -v openssl >/dev/null 2>&1; then
    (
        cd "${KEYS_DIR}"
        MSYS_NO_PATHCONV=1 openssl req -new -x509 -newkey rsa:4096 -nodes -days 3650 \
            -subj "/CN=THMD-Guru Global Tech Academy Secure Boot Signing Key/O=THMD-Guru Global Tech Academy" \
            -keyout "MOK.key" \
            -out "MOK.crt" 2>/dev/null
        openssl x509 -in "MOK.crt" -outform DER -out "MOK.der" 2>/dev/null
        chmod 0600 "MOK.key"
    )
    echo "[THMD-Guru Keygen] Created UEFI Secure Boot MOK keypair:"
    echo "  • Private Key : ${KEYS_DIR}/MOK.key"
    echo "  • Public Cert : ${KEYS_DIR}/MOK.crt (PEM) / ${KEYS_DIR}/MOK.der (Enroll via mokutil --import)"
fi

echo "[THMD-Guru Keygen] Done."
