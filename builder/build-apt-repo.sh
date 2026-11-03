#!/usr/bin/env bash
# THMD-Guru OS Forge — Local APT Repository Indexer & Optional GPG Signer
# Owner: os-forge-devops
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEBS_DIR="${ROOT_DIR}/build/debs"
REPO_DIR="${ROOT_DIR}/out/apt-repo"

if [[ ! -d "${DEBS_DIR}" ]]; then
    echo "[APT Repo] Building .deb packages first..."
    bash "${ROOT_DIR}/builder/forge.sh" packages
fi

mkdir -p "${REPO_DIR}/pool/main" "${REPO_DIR}/dists/genesis/main/binary-amd64"
cp -f "${DEBS_DIR}/"*.deb "${REPO_DIR}/pool/main/"

cd "${REPO_DIR}"
dpkg-scanpackages --arch amd64 pool/ > dists/genesis/main/binary-amd64/Packages
gzip -9c dists/genesis/main/binary-amd64/Packages > dists/genesis/main/binary-amd64/Packages.gz

cat << EOF > dists/genesis/Release
Origin: THMD-Guru Global Tech Academy
Label: THMD-Guru Linux Official Repository
Suite: genesis
Codename: genesis
Version: 1.0
Architectures: amd64 all
Components: main
Description: Official APT repository for THMD-Guru Linux 1.0 (Genesis)
Date: $(date -Ru)
EOF

if [[ -n "${GPG_KEY_ID:-}" ]]; then
    gpg --default-key "${GPG_KEY_ID}" -abs -o dists/genesis/Release.gpg dists/genesis/Release
    gpg --default-key "${GPG_KEY_ID}" --clearsign -o dists/genesis/InRelease dists/genesis/Release
    echo "[APT Repo] Signed Release with GPG key ${GPG_KEY_ID}"
fi

echo "[APT Repo] Repository generated at ${REPO_DIR}"
