# THMD-Guru OS Forge — Engineering Contract (shared by all agents)

## Decisions (approved)
- Upstream base: **Debian 12 "bookworm"** (amd64), built with **live-build** (`lb config/build`).
- Kernel: Debian `linux-image-amd64` + per-edition `sysctl.d` profiles (no from-source kernel in v1).
- Desktop edition: **KDE Plasma** (Wayland default, SDDM), installer **Calamares**.
- ATTT edition: **XFCE4** (LightDM), Live + Calamares installer.
- Server edition: headless, Debian Installer (preseed) + cloud-init, Cockpit.
- Version: `1.0 "Genesis"`. Distro ID: `thmd-guru`, ID_LIKE=`debian`.
- Brand: **Cyber Sapphire & Royal Gold**, dark mode.
  - Sapphire `#0B3D91`, Deep Navy `#071A3A`, Royal Gold `#D4AF37`, Light Gold `#F5D77A`, Ink `#0A0F1E`, Text `#E6ECF7`.
  - Slogan: "Learn Deep. Build Real. Secure Everything."
  - Org: THMD-Guru Global Tech Academy.

## Directory ownership (ONLY write inside your own area)
| Path | Owner |
|---|---|
| `core/kernel/`, `core/bootloader/`, `core/includes.chroot/`, `core/hooks/`, `core/package-lists/` | chief-os-architect |
| `core/branding/`, `packages/thmd-guru-branding/`, `packages/guru-welcome/`, `editions/desktop/` | desktop-ux-lead |
| `editions/server/`, `packages/guru-server-console/` | server-infra-lead |
| `editions/attt/`, `packages/guru-stealth/`, `packages/guru-sandbox/` | security-attt-lead |
| `builder/`, `tests/`, `packages/guru-cli/`, `README.md`, `Makefile` | os-forge-devops |
| `docs/<your-agent-name>.md` | each agent documents own area |

## Edition layout (live-build overlay convention)
Each `editions/<ed>/` mirrors a live-build `config/` tree:
```
editions/<ed>/
  edition.conf                # bash vars: EDITION, LB_ARGS (extra lb config flags), ISO_NAME
  package-lists/*.list.chroot
  hooks/live/*.hook.chroot    # numbered, executable bash, `set -e`
  includes.chroot/...         # files copied into rootfs
  includes.binary/...         # files on ISO (e.g. preseed)
  bootloaders/                # optional per-edition overrides
```
The builder assembles: `core/*` → then `editions/<ed>/*` overlaid on top → `lb build`.
Core's live-build pieces live at `core/package-lists`, `core/hooks/live`, `core/includes.chroot`, `core/bootloader` (grub-pc/grub-efi/isolinux theme dirs as live-build expects under `config/bootloaders/`).

## Shared CLI: `guru`
Installed at `/usr/bin/guru` (package `guru-cli`, bash). Subcommands are plugins: `/usr/lib/guru/commands/<name>` (executable). Edition-specific packages drop their own plugin there (e.g. `stealth`, `sandbox`, `console`, `welcome`). Edition identity read from `/etc/thmd-guru/edition` (`desktop|server|attt`).

## Packages
Each `packages/<name>/` is a native Debian source package (`debian/` dir with control, rules (dh), changelog, compat via `debhelper-compat (= 13)`), `Architecture: all` unless needed. Builder runs `dpkg-buildpackage -us -uc -b` and drops .debs into `config/packages.chroot/`.

## Rules
- Scripts: bash with `set -euo pipefail`, LF line endings, shellcheck-clean where practical.
- No secrets, no proprietary binaries. Tools not in Debian repos: write an installer script, don't vendor binaries.
- Security tools in ATTT: for authorized testing/education only; include a legal notice.
