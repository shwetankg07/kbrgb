# kbrgb

**Linux RGB control for Acer laptops with the ENEK5130 i2c-HID keyboard controller**
(Predator Helios Neo 16S AI / PHN16S-71 — confirmed working; see [supported hardware](#supported-hardware))

29 animated effects, per-zone static colors, a preset picker, theme sync, and
boot restore — in a single dependency-free Python script. No kernel module, no
daemon manager, no conflict with [Linuwu-Sense](https://github.com/0x7375646F/Linuwu-Sense)
fan control.

```
kbrgb ff2a2a                 # all zones static red
kbrgb ff0000 00ff41 0066ff ff00ff   # per-zone colors
kbrgb storm                  # night sky with lightning strikes
kbrgb prism                  # ripple that shifts hue every sweep
kbrgb battery                # 4 zones become a live battery bar
kbrgb -b 40 -s 6 aurora      # dim, slow northern lights
kbrgb off
```

## Why this exists

On several 2025+ Acer gaming laptops, none of the existing Linux tools can
control the keyboard RGB:

- The Acer WMI gaming methods (used by Linuwu-Sense, DAMX, facer) **accept the
  RGB writes (`AE_OK`) but the LEDs never change** — on this hardware they
  simply don't reach the LED controller.
- The actual controller is a separate **ENE KB5130 chip on i2c-HID**
  (`ENEK5130:00`, VID `0CF2` PID `5130`, `/dev/hidrawN`), controlled with
  11-byte HID feature reports.

The HID protocol was discovered by the community — see
[cleyton1986/predator-sense](https://github.com/cleyton1986/predator-sense)
(`hid_rgb.rs`) and Linuwu-Sense issue #4. `kbrgb` reimplements it in
userspace Python and adds a software animation engine on top.

**New findings documented here** (verified on a real PHN16S-71, see
[PROTOCOL.md](PROTOCOL.md)):

1. The brightness byte range is **0–100** on this EC revision, not 1–15 as
   previously assumed — tools using 15 as max run the LEDs at 15% brightness.
2. The "all zones" mask `0x0f` produces dim/incorrect output on this EC —
   zones must be written individually (`0x01`, `0x02`, `0x04`, `0x08`).
3. The controller has no persistent memory: it resets to its built-in wave
   effect on full power-off (hence the boot-restore hook).

## Install

```bash
git clone https://github.com/shwetankg07/kbrgb
cd kbrgb
sudo ./install.sh      # installs kbrgb to /usr/local/bin + udev rule
kbrgb rainbow          # no sudo needed after install
```

Requirements: Python 3.11+, a `linuwu_sense` group or the bundled udev rule
(grants access via `uaccess` to the active seat). No pip packages.

## Effects

| Calm | Motion | Drama | Functional |
|---|---|---|---|
| `breathe [C]` | `snake [C]` | `storm` | `cpuheat` — temp gauge |
| `aurora` | `meteor [C]` | `eruption` | `battery` — charge bar |
| `ocean` | `wave` | `supernova` | |
| `lava` | `duel [C1 C2]` | `redalert [C]` | |
| `candle` | `shadow [C]` | `shockwave [C]` | |
| `ripple [C]` | `chase [C]` | `glitch [C]` | |
| `heartbeat [C]` | `rainbow` | `police [C1 C2]` | |
| `prism` | | `disco` / `sparkle [C..]` | |
| | | `matrix` / `fire` / `strobe [C]` | |

Flags: `-b N` brightness (0–100), `-s N` cycle period in seconds.
Effects default to colors from the active [omarchy](https://omarchy.org)
theme when available, with built-in fallbacks otherwise.

Handy commands:

- `kbrgb demo` — tour every effect, ~4 seconds each
- `kbrgb list` — effect names (for scripting/pickers)
- `kbrgb restore` — replay the last setting (the controller forgets on
  power-off; wire this into a boot hook — examples for omarchy and plain
  systemd in `examples/`)
- `kbrgb status` — device path, saved state, effect daemon state
- `kbrgb probe` — guided hardware diagnostic, see below

Animations survive suspend/resume: the effect daemon transparently reopens
the device if the i2c bus blips.

The `examples/` directory has a walker-based preset picker (`kbrgb-menu`),
a ready-made `presets.conf`, omarchy hooks for theme sync + boot restore,
and a systemd user service for non-omarchy setups.

## Supported hardware

| Model | Status |
|---|---|
| Predator Helios Neo 16S AI (PHN16S-71) | ✅ confirmed (developed here) |
| Predator Helios Neo 16 (PHN16-73) | 🤞 same chip per predator-sense findings |
| Nitro ANV16S-41 | 🤞 same chip per DAMX #213 |
| Anything with `ENEK5130` in `/sys/class/hidraw/*/device/uevent` | probably — **please test and report!** |

Check yours:

```bash
grep -l ENEK5130 /sys/class/hidraw/*/device/uevent
```

## Contributing

Yes please! Especially:

- **Testers with other ENEK5130 models** — run `kbrgb probe`: it walks you
  through a guided diagnostic and prints a paste-ready report for a GitHub
  issue. That's all it takes to get your model documented.
- **Protocol spelunking** — the EC's *native* effects (the built-in wave it
  boots with) must be triggerable somehow; the init sequence
  (`0xa4, 0x41–0x48`) from `AcerECKeyboardController.dll` is unexplored.
  A USB/i2c capture from Windows PredatorSense would crack it open.
- **New effects** — an effect is a ~10-line pure function returning 4 RGB
  tuples per frame. Go wild.

## Credits

- [cleyton1986/predator-sense](https://github.com/cleyton1986/predator-sense) —
  first working ENEK5130 HID implementation this builds on
- [0x7375646F/Linuwu-Sense](https://github.com/0x7375646F/Linuwu-Sense) and
  [PXDiv/Div-Linuwu-Sense](https://github.com/PXDiv/Div-Linuwu-Sense) — the
  fan/platform driver ecosystem, and the issue threads where the community
  mapped this hardware
- [JafarAkhondali/acer-predator-turbo-and-rgb-keyboard-linux-module](https://github.com/JafarAkhondali/acer-predator-turbo-and-rgb-keyboard-linux-module) —
  the original Acer RGB reverse-engineering lineage

## License

MIT — see [LICENSE](LICENSE). The HID protocol facts belong to the community
that dug them up; this repo just tries to document them properly.
