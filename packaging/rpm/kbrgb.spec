Name:           kbrgb
Version:        0.2.1
Release:        1%{?dist}
Summary:        RGB keyboard control for Acer Predator/Nitro laptops (ENE KB5130)

License:        MIT
URL:            https://github.com/shwetankg07/kbrgb
Source0:        %{url}/archive/refs/tags/v%{version}.tar.gz#/%{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3 >= 3.11
BuildRequires:  systemd-rpm-macros
Requires:       python3 >= 3.11

%description
Userspace control for the 4-zone keyboard RGB on 2025-era Acer Predator and
Nitro laptops, where the lighting moved to an ENE KB5130 chip on i2c-HID and
the usual Acer WMI tools silently do nothing.

One Python file, no dependencies, no kernel module: 29 software effects, the
EC's own builtin effects, per-zone static colors, a preset picker, theme sync
and boot restore.

The five reactive effects read key events from /dev/input and need your user
in the input group. Every other effect works without it.

%prep
%autosetup

%build
# Nothing to build: a single dependency-free script.

%install
install -Dpm 755 kbrgb.py %{buildroot}%{_bindir}/%{name}

# The rule text has exactly one home, kbrgb.py, so the packaged rule cannot
# drift from the one `kbrgb install-udev` writes for pip users.
install -dm 755 %{buildroot}%{_udevrulesdir}
python3 kbrgb.py install-udev --print \
  > %{buildroot}%{_udevrulesdir}/60-kbrgb-enek5130.rules
chmod 644 %{buildroot}%{_udevrulesdir}/60-kbrgb-enek5130.rules

%files
%license LICENSE
%doc README.md PROTOCOL.md examples/
%{_bindir}/%{name}
%{_udevrulesdir}/60-kbrgb-enek5130.rules

%changelog
* Sat Jul 25 2026 Shwetank Gupta <shwetankg07@gmail.com> - 0.2.1-1
- Suggest an absolute path in sudo hints, so they work for pip/pipx installs
  where the entry point sits outside sudo's secure_path

* Sat Jul 25 2026 Shwetank Gupta <shwetankg07@gmail.com> - 0.2.0-1
- First packaged release: adds --version, `kbrgb install-udev`, and the
  AUR/PyPI/COPR packaging
