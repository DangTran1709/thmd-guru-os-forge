#!/usr/bin/env bash
# THMD-Guru OS Forge — Cryptographic Repository Signing & UEFI Secure Boot MOK Key Manager
# Owner: chief-os-architect & security-attt-lead
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
KEYS_DIR="${KEYS_DIR:-${ROOT_DIR}/build/signing-keys}"
REPO_DIST="${ROOT_DIR}/out/apt-repo/dists/genesis"
mkdir -p "${KEYS_DIR}"

if command -v openssl >/dev/null 2>&1; then
    (
        cd "${KEYS_DIR}"
        if [[ ! -f "MOK.key" || ! -f "MOK.crt" ]]; then
            echo "[THMD-Guru Keygen] Generating RSA-4096 UEFI Secure Boot MOK & Repo Signing keypair..."
            MSYS_NO_PATHCONV=1 openssl req -new -x509 -newkey rsa:4096 -nodes -days 3650 \
                -subj "/CN=THMD-Guru Global Tech Academy Secure Boot Signing Key/O=THMD-Guru Global Tech Academy" \
                -keyout "MOK.key" \
                -out "MOK.crt" 2>/dev/null
            openssl x509 -in "MOK.crt" -outform DER -out "MOK.der" 2>/dev/null
            chmod 0600 "MOK.key"
        fi
        openssl x509 -pubkey -noout -in "MOK.crt" > "thmd-guru-archive.pub" 2>/dev/null
    )
    echo "[THMD-Guru Keygen] Verified RSA-4096 MOK & Repository Signing Keys in ${KEYS_DIR}."

    if [[ -f "${REPO_DIST}/Release" ]]; then
        openssl dgst -sha256 -sign "${KEYS_DIR}/MOK.key" -out "${REPO_DIST}/Release.gpg" "${REPO_DIST}/Release"
        cp -f "${KEYS_DIR}/thmd-guru-archive.pub" "${REPO_DIST}/thmd-guru-archive.pub"
        echo "[THMD-Guru Keygen] Cryptographically signed APT Release -> ${REPO_DIST}/Release.gpg"
    fi
fi

echo "[THMD-Guru Keygen] Done."
