#!/usr/bin/env bash
# kbrgb installer: script -> /usr/local/bin, udev rule -> user access.
#
# This is the git-clone install. On Arch, Fedora or with pip, prefer the
# packages: see the Install section of README.md.
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "run with sudo: sudo ./install.sh" >&2
  exit 1
fi

cd "$(dirname "$0")"

install -m 755 kbrgb.py /usr/local/bin/kbrgb

# The rule text lives in kbrgb.py so there is exactly one copy of it, shared
# by this installer, the AUR package, the RPM and `pipx install kbrgb`.
# install-udev writes it, drops the pre-0.x rule name and reloads udev.
/usr/local/bin/kbrgb install-udev

echo "installed. try:  kbrgb rainbow"
