# THMD-Guru OS Forge — Automated Debian 12 (Bookworm) ISO Build Environment
# Owner: os-forge-devops

FROM debian:bookworm

ENV DEBIAN_FRONTEND=noninteractive \
    LC_ALL=C.UTF-8 \
    LANG=C.UTF-8

RUN apt-get update && apt-get install -y --no-install-recommends \
    live-build \
    debootstrap \
    debhelper \
    dpkg-dev \
    build-essential \
    fakeroot \
    xorriso \
    isolinux \
    syslinux-common \
    syslinux-efi \
    grub-pc-bin \
    grub-efi-amd64-bin \
    mtools \
    dosfstools \
    squashfs-tools \
    ca-certificates \
    curl \
    git \
    rsync \
    lintian \
    shellcheck \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
ENTRYPOINT ["/bin/bash", "builder/forge.sh"]
