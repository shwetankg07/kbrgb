#!/usr/bin/env bash
# kbrgb installer: script -> /usr/local/bin, udev rule -> user access.
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "run with sudo: sudo ./install.sh" >&2
  exit 1
fi

install -m 755 kbrgb /usr/local/bin/kbrgb

cat > /etc/udev/rules.d/99-kbrgb-enek5130.rules <<'EOF'
# ENE KB5130 i2c-HID keyboard RGB controller (Acer Predator/Nitro)
KERNEL=="hidraw*", SUBSYSTEMS=="hid", ATTRS{modalias}=="hid:b0018g*v00000CF2p00005130", MODE="0660", TAG+="uaccess"
EOF

udevadm control --reload-rules
udevadm trigger

echo "installed. try:  kbrgb rainbow"
