#!/usr/bin/env bash
# THMD-Guru LAB vmware-zap-rag-pfsense — đặt IP tĩnh trên VMnet2 (192.168.80.0/24, GW/DNS = pfSense 192.168.80.1)
# Dùng: sudo bash common/set-static-ip.sh <vm1|vm2|vm3> [interface]
set -euo pipefail

NODE="${1:-}"
case "$NODE" in
    vm1) IP=192.168.80.10; HN=lab-vm1-kali-zap ;;
    vm2) IP=192.168.80.20; HN=lab-vm2-web-target ;;
    vm3) IP=192.168.80.30; HN=lab-vm3-ai-rag ;;
    *) echo "Dùng: sudo bash $0 <vm1|vm2|vm3> [interface]" >&2; exit 2 ;;
esac
GW=192.168.80.1
DNS=192.168.80.1
PREFIX=24

[ "$(id -u)" -eq 0 ] || { echo "Cần chạy bằng sudo/root" >&2; exit 1; }

# Card mạng: tham số thứ 2, hoặc card đầu tiên không phải loopback
IFACE="${2:-$(ip -o link show | awk -F': ' '$2 != "lo" {print $2; exit}' | cut -d@ -f1)}"
[ -n "$IFACE" ] || { echo "Không tìm thấy card mạng" >&2; exit 1; }
echo "[LAB] $NODE -> $IFACE = $IP/$PREFIX, GW $GW, DNS $DNS, hostname $HN"

hostnamectl set-hostname "$HN" 2>/dev/null || echo "$HN" > /etc/hostname
grep -q "$HN" /etc/hosts || echo "127.0.1.1 $HN" >> /etc/hosts
# Tên miền nội bộ để dễ dùng kể cả khi tắt pfSense
for pair in "192.168.80.10 kali.thmd.lab" "192.168.80.20 target.thmd.lab" "192.168.80.30 airag.thmd.lab"; do
    grep -q "${pair#* }" /etc/hosts || echo "$pair" >> /etc/hosts
done

if command -v netplan >/dev/null 2>&1 && [ -d /etc/netplan ]; then
    # Ubuntu Server
    mkdir -p /etc/netplan/disabled
    for f in /etc/netplan/*.yaml; do [ -e "$f" ] && mv "$f" /etc/netplan/disabled/ ; done
    cat > /etc/netplan/60-thmd-lab.yaml <<EOF
network:
  version: 2
  ethernets:
    $IFACE:
      dhcp4: false
      addresses: [$IP/$PREFIX]
      routes:
        - to: default
          via: $GW
      nameservers:
        addresses: [$DNS]
        search: [thmd.lab]
EOF
    chmod 600 /etc/netplan/60-thmd-lab.yaml
    netplan apply
elif command -v nmcli >/dev/null 2>&1 && systemctl is-active --quiet NetworkManager; then
    # Kali / THMD-Guru Desktop / ATTT
    CON="thmd-lab-$IFACE"
    nmcli -t -f NAME con show | grep -qx "$CON" && nmcli con delete "$CON" >/dev/null
    nmcli con add type ethernet ifname "$IFACE" con-name "$CON" \
        ipv4.method manual ipv4.addresses "$IP/$PREFIX" ipv4.gateway "$GW" \
        ipv4.dns "$DNS" ipv4.dns-search thmd.lab ipv6.method disabled autoconnect yes >/dev/null
    nmcli con up "$CON" >/dev/null
else
    # Debian ifupdown / THMD-Guru Server / Live RAM OS
    mkdir -p /etc/network/interfaces.d
    cat > /etc/network/interfaces.d/60-thmd-lab <<EOF
auto $IFACE
iface $IFACE inet static
    address $IP/$PREFIX
    gateway $GW
    dns-nameservers $DNS
EOF
    ip link set "$IFACE" up 2>/dev/null || true
    ip addr flush dev "$IFACE" 2>/dev/null || true
    ip addr add "$IP/$PREFIX" dev "$IFACE" 2>/dev/null || true
    ip route replace default via "$GW" dev "$IFACE" 2>/dev/null || true
    echo "nameserver $DNS" > /etc/resolv.conf 2>/dev/null || true
    ifdown "$IFACE" 2>/dev/null || true
    ifup "$IFACE" 2>/dev/null || true
fi

mkdir -p /etc/thmd-guru
echo "lab80-$NODE" > /etc/thmd-guru/vm-role
ip -4 addr show "$IFACE" | awk '/inet /{print "[OK] " $2}'
if ping -c1 -W2 "$GW" >/dev/null 2>&1; then
    echo "[OK] Gateway pfSense $GW reachable"
else
    echo "[WARN] Chưa ping được pfSense $GW (pfSense đang tắt? Vẫn có thể chạy thực nghiệm nội bộ VMnet2)"
fi
