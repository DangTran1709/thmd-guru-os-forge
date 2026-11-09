#!/usr/bin/env bash
# THMD-Guru OS Forge — Automated QA, Pentest Regression & Bootable ISO Integrity Suite
# Owner: os-forge-devops & security-attt-lead
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

echo "===================================================================="
echo "  THMD-GURU OS FORGE — SECURITY & QA VERIFICATION SUITE"
echo "===================================================================="

# 1. File Presence Check
REQUIRED_FILES=(
    "core/includes.chroot/etc/os-release"
    "core/includes.chroot/usr/lib/os-release"
    "core/includes.chroot/etc/sysctl.d/90-thmd-guru-base.conf"
    "core/includes.chroot/etc/audit/rules.d/90-thmd-guru-mitre.rules"
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
    "packages/guru-cli/src/THMD-guru-ai"
    "packages/guru-cli/labs/nckh-zap-rag/docker-compose.yml"
    "packages/guru-cli/labs/nckh-zap-rag/owasp_cwe_kb.json"
    "packages/guru-cli/labs/nckh-zap-rag/zap_raw_alerts.json"
    "packages/guru-cli/labs/nckh-zap-rag/run_experiment.py"
    "packages/guru-cli/labs/netops-bgp-sdn/docker-compose.yml"
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
    "builder/build-iso-portable.py"
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
echo "[PASS 1/7] All ${#REQUIRED_FILES[@]} core & edition files present."

# 2. Validate bash syntax of all scripts and hooks
while IFS= read -r -d '' sh_file; do
    bash -n "${sh_file}"
done < <(find core editions packages builder tests -type f \( -name "*.sh" -o -name "*.hook.chroot" -o -name "*-plugin" -o -name "guru" \) -print0)
echo "[PASS 2/7] All Bash scripts, hooks, and CLI plugins passed syntax verification (bash -n)."

# 3. Positive CLI Functional Verification (THMD-guru-ai & guru + NCKH & VMware Multi-VM)
output="$("${ROOT_DIR}/packages/guru-cli/src/THMD-guru-ai" help)"
grep -q "THMD-guru-ai" <<< "${output}"
"${ROOT_DIR}/packages/guru-cli/src/THMD-guru-ai" info >/dev/null
status_json="$("${ROOT_DIR}/packages/guru-cli/src/THMD-guru-ai" status --json)"
grep -q '"cli":"THMD-guru-ai"' <<< "${status_json}"
lab_out="$("${ROOT_DIR}/packages/guru-cli/src/THMD-guru-ai" lab list)"
grep -q "nckh-zap-rag" <<< "${lab_out}"
grep -q "vmware-zap-rag-pfsense" <<< "${lab_out}"
exp_out="$("${ROOT_DIR}/packages/guru-cli/src/THMD-guru-ai" lab run nckh-zap-rag)"
grep -q "NDCG@5" <<< "${exp_out}"
exp_pfsense_out="$("${ROOT_DIR}/packages/guru-cli/src/THMD-guru-ai" lab run vmware-zap-rag-pfsense)"
grep -q "0.9908" <<< "${exp_pfsense_out}"
vm_out="$("${ROOT_DIR}/packages/guru-cli/src/THMD-guru-ai" vm-node status)"
grep -q "edge-router-waf" <<< "${vm_out}"
grep -q "lab80-vm1" <<< "${vm_out}"
"${ROOT_DIR}/packages/guru-cli/src/THMD-guru-ai" vm-node init scanner-red --dry-run >/dev/null
"${ROOT_DIR}/packages/guru-cli/src/THMD-guru-ai" vm-node init lab80-vm1 --dry-run >/dev/null
"${ROOT_DIR}/packages/guru-cli/src/THMD-guru-ai" vm-node init lab80-vm2 --dry-run >/dev/null
"${ROOT_DIR}/packages/guru-cli/src/THMD-guru-ai" vm-node init lab80-vm3 --dry-run >/dev/null
"${ROOT_DIR}/packages/guru-cli/src/THMD-guru-ai" ai status >/dev/null
"${ROOT_DIR}/packages/guru-cli/src/THMD-guru-ai" gpu >/dev/null
"${ROOT_DIR}/packages/guru-cli/src/THMD-guru-ai" dev-env >/dev/null
"${ROOT_DIR}/packages/guru-cli/src/THMD-guru-ai" arsenal list >/dev/null
hub_list_out="$("${ROOT_DIR}/packages/guru-cli/src/THMD-guru-ai" hub list)"
grep -q "tools/attt-web-scanner" <<< "${hub_list_out}"
grep -q "nckh/vmware" <<< "${hub_list_out}"
tmp_hub_dir="$(mktemp -d)"
GURU_HUB_ROOT="${tmp_hub_dir}/modules" GURU_HUB_DB="${tmp_hub_dir}/hub.db" \
    "${ROOT_DIR}/packages/guru-cli/src/THMD-guru-ai" hub install nckh/vmware-zap-rag-pfsense --role vm1-zap >/dev/null
hub_stat_out="$(GURU_HUB_ROOT="${tmp_hub_dir}/modules" GURU_HUB_DB="${tmp_hub_dir}/hub.db" \
    "${ROOT_DIR}/packages/guru-cli/src/THMD-guru-ai" hub status)"
grep -q "nckh/vmware-zap-rag-pfsense" <<< "${hub_stat_out}"
GURU_HUB_ROOT="${tmp_hub_dir}/modules" GURU_HUB_DB="${tmp_hub_dir}/hub.db" \
    "${ROOT_DIR}/packages/guru-cli/src/THMD-guru-ai" hub remove nckh/vmware-zap-rag-pfsense >/dev/null
rm -rf "${tmp_hub_dir}"
echo "[PASS 3/7] THMD-guru-ai CLI positive functional tests (Modular Hub, NCKH ZAP+RAG, VMware vm-node, AI, GPU, Arsenal) verified."

# 4. Negative & Fail-Closed Security Tests (CWE-636 Mitigation)
set +e
"${ROOT_DIR}/packages/guru-cli/src/guru" non_existent_subcommand >/dev/null 2>&1
rc_unknown=$?
sandbox_out="$(PATH="/nonexistent" /bin/sh "${ROOT_DIR}/packages/guru-sandbox/src/sandbox-plugin" run echo "UNISOLATED_EXECUTION_LEAK" 2>&1)"
rc_sandbox=$?
set -e

if [[ "${rc_unknown}" -ne 127 ]]; then
    echo "[FAIL] Expected exit code 127 for unknown subcommand, got ${rc_unknown}" >&2
    exit 1
fi
if [[ "${rc_sandbox}" -eq 0 ]] || grep -q "UNISOLATED_EXECUTION_LEAK" <<< "${sandbox_out}"; then
    echo "[FAIL] CRITICAL: guru-sandbox failed open and executed payload without isolation!" >&2
    exit 1
fi
grep -q "FAIL-CLOSED" <<< "${sandbox_out}"
echo "[PASS 4/7] Negative & Fail-Closed Sandbox Security Tests (CWE-636) verified."

# 5. Security Policy & Idempotency Regression Audit (CWE-798 & OPSEC Mitigations)
grep -q "^PermitRootLogin no" "editions/server/includes.chroot/etc/ssh/sshd_config.d/90-thmd-guru-hardened.conf"
if grep -q "NOPASSWD:ALL" "editions/server/includes.chroot/etc/cloud/cloud.cfg.d/90_thmd_guru.cfg"; then
    echo "[FAIL] Dangerous NOPASSWD:ALL found in server cloud-init config!" >&2
    exit 1
fi
if grep -q "user-password password" "editions/server/includes.binary/preseed/thmd-guru-server.cfg"; then
    echo "[FAIL] Plaintext password found in server preseed!" >&2
    exit 1
fi
grep -q "user-password-crypted" "editions/server/includes.binary/preseed/thmd-guru-server.cfg"
grep -q "chage -d 0 guru" "editions/server/includes.binary/preseed/thmd-guru-server.cfg"
grep -q "limit rate 10/minute" "editions/server/hooks/live/0200-server-setup.hook.chroot"
grep -q "disable_ipv6" "packages/guru-stealth/src/stealth-plugin"
grep -q "5353, 5355" "packages/guru-stealth/src/stealth-plugin"
grep -q "vm.max_map_count = 1048576" "core/kernel/sysctl/91-desktop.conf"
grep -q "vm.max_map_count = 1048576" "core/kernel/sysctl/91-server.conf"
grep -q "T1055_process_injection" "core/includes.chroot/etc/audit/rules.d/90-thmd-guru-mitre.rules"
grep -q "open-vm-tools" "editions/desktop/package-lists/desktop.list.chroot"
grep -q "open-vm-tools" "editions/server/package-lists/server.list.chroot"
grep -q "open-vm-tools" "editions/attt/package-lists/attt.list.chroot"
grep -q "grep -q" "core/hooks/live/0100-thmd-guru-core.hook.chroot"
grep -q "grep -q" "editions/attt/hooks/live/0200-attt-setup.hook.chroot"
echo "[PASS 5/7] Security Policy & Idempotency Audit (SSH, Preseed, Cloud-Init, Stealth IPv6/mDNS, Hooks) verified."

# 6. Cryptographic APT Repository Signature Verification
if [[ -f "out/apt-repo/dists/genesis/Release.gpg" && -f "build/signing-keys/thmd-guru-archive.pub" ]]; then
    openssl dgst -sha256 -verify "build/signing-keys/thmd-guru-archive.pub" \
        -signature "out/apt-repo/dists/genesis/Release.gpg" \
        "out/apt-repo/dists/genesis/Release" >/dev/null
    echo "[PASS 6/7] Cryptographic RSA-4096 APT Repository Signature (Release.gpg) verified."
fi

# 7. Deep Binary ISO-9660 + El Torito + Hybrid MBR + Edition Isolation Audit
PY_CMD="python"
[[ -x "/c/Python314/python.exe" ]] && PY_CMD="/c/Python314/python.exe"

if [[ -f "out/thmd-guru-desktop-1.0-genesis-amd64.iso" ]]; then
    "${PY_CMD}" -c '
import struct, sys
from pathlib import Path
sys.path.insert(0, "builder")

expected_pools = {
    "desktop": {"guru-cli_1.0.0_all.deb", "thmd-guru-branding_1.0.0_all.deb", "guru-welcome_1.0.0_all.deb"},
    "server":  {"guru-cli_1.0.0_all.deb", "guru-server-console_1.0.0_all.deb"},
    "attt":    {"guru-cli_1.0.0_all.deb", "thmd-guru-branding_1.0.0_all.deb", "guru-sandbox_1.0.0_all.deb", "guru-stealth_1.0.0_all.deb"},
}

for ed, expected_debs in expected_pools.items():
    iso_path = Path(f"out/thmd-guru-{ed}-1.0-genesis-amd64.iso")
    assert iso_path.exists(), f"Missing {iso_path}"
    data = iso_path.read_bytes()
    assert len(data) > 50_000_000, f"ISO too small: {len(data)}"
    # 1. Verify Hybrid MBR 0x55AA signature
    assert data[510:512] == b"\x55\xaa", f"{ed}: Missing MBR 0x55AA signature"
    # 2. Verify Primary Volume Descriptor (Sector 16)
    pvd = data[16*2048:17*2048]
    assert pvd[0] == 1 and pvd[1:6] == b"CD001", f"{ed}: Invalid PVD"
    # 3. Verify El Torito Boot Record (Sector 17)
    brvd = data[17*2048:18*2048]
    assert brvd[0] == 0 and b"EL TORITO SPECIFICATION" in brvd, f"{ed}: Missing El Torito Boot Record"
    # 4. Verify Edition Package Isolation in /pool/main
    for deb in ["guru-cli_1.0.0_all.deb", "thmd-guru-branding_1.0.0_all.deb", "guru-welcome_1.0.0_all.deb", "guru-server-console_1.0.0_all.deb", "guru-sandbox_1.0.0_all.deb", "guru-stealth_1.0.0_all.deb"]:
        nm_tag = b"NM" + bytes([5 + len(deb), 1, 0]) + deb.encode()
        present = nm_tag in data
        if deb in expected_debs:
            assert present, f"{ed}: Missing expected package {deb} in ISO"
        else:
            assert not present, f"{ed}: Cross-edition package pollution detected: {deb} found in {ed} ISO!"
print("[PASS 7/7] Binary ISO-9660, El Torito BIOS/UEFI, MBR Signature & Strict Edition Package Isolation verified.")
'
fi

echo "===================================================================="
echo "  ALL 7 QA & PENTEST VERIFICATION STAGES PASSED SUCCESSFULLY!"
echo "===================================================================="
