# kbrgb

RGB keyboard control for the Acer laptops where nothing else works: the 2025-era
Predator and Nitro models that moved their keyboard lighting to an ENE KB5130
chip (`ENEK5130` on i2c-HID). Built on a Predator Helios Neo 16S AI (PHN16S-71),
confirmed on other machines since, see [supported hardware](#supported-hardware).

One Python file, no dependencies, no kernel module. 29 software effects, the
EC's own builtin effects, per-zone static colors, a preset picker, theme sync
and boot restore. Coexists fine with
[Linuwu-Sense](https://github.com/0x7375646F/Linuwu-Sense) fan control.

```
kbrgb ff2a2a                 # all zones static red
kbrgb ff0000 00ff41 0066ff ff00ff   # per-zone colors
kbrgb storm                  # night sky with lightning strikes
kbrgb prism                  # ripple that shifts hue every sweep
kbrgb battery                # 4 zones become a live battery bar
kbrgb -b 40 -s 6 aurora      # dim, slow northern lights
kbrgb native wave            # the EC's builtin rainbow wave, zero CPU
kbrgb off
```

## Why this exists

I put Linux on this laptop and found out the keyboard RGB was unreachable.
DAMX, Linuwu-Sense, facer: they all talk to Acer's WMI interface, and on this
hardware generation the firmware accepts every call (`AE_OK`) and then does
nothing. The LEDs never change because they aren't wired to WMI anymore. The
real controller is a separate ENE KB5130 chip on i2c-HID (`ENEK5130:00`, VID
`0CF2` PID `5130`, shows up as `/dev/hidrawN`) and it only listens to 11-byte
HID feature reports.

The HID protocol was first cracked by the community, see
[cleyton1986/predator-sense](https://github.com/cleyton1986/predator-sense)
(`hid_rgb.rs`) and the Linuwu-Sense issue threads. kbrgb reimplements it in
userspace Python, puts a software animation engine on top, and can also
trigger the EC's builtin effects directly.

Along the way this repo picked up some protocol findings of its own, all
verified on real hardware (details and packet layout in
[PROTOCOL.md](https://github.com/shwetankg07/kbrgb/blob/main/PROTOCOL.md)):

1. The brightness byte goes 0 to 100 on this EC revision, not 1 to 15 like
   older tools assumed. A tool sending 15 as "max" is quietly running your
   LEDs at 15% brightness. Reported upstream and fixed in predator-sense
   v0.2.27-preview.
2. ~~The all-zones mask 0x0f misbehaves~~ Correction: `0x0f` works fine. The
   original claim was my own test artifact (the packet went out at brightness
   15), caught thanks to an independent probe report in issue #1. Full story
   in PROTOCOL.md, kept there as a warning about single-variable testing.
3. The controller has no persistent memory. Full power off and it wakes up in
   its builtin rainbow wave, which is why there's a boot restore hook.
4. The EC's native effects are triggerable. Byte 2 of the packet, which
   everyone had written down as "unknown, constant 0x02", is actually the
   effect selector. Discovered by
   [abduvaliy-engineer](https://github.com/abduvaliy-engineer) in
   [DAMX PR #213](https://github.com/PXDiv/Div-Acer-Manager-Max/pull/213),
   confirmed here on a PHN16S-71. One write and the hardware animates by
   itself, zero CPU.

## Install

**Arch, CachyOS, EndeavourOS, omarchy** (AUR):

```bash
yay -S kbrgb           # or kbrgb-git to track main
```

If it works out, an [AUR vote](https://aur.archlinux.org/packages/kbrgb) is the
one thing that helps the next Acer owner find this: AUR search ranks by votes and
popularity.

**Anywhere else** (pip):

```bash
pipx install kbrgb                        # or: uv tool install kbrgb
sudo "$(command -v kbrgb)" install-udev
```

pip cannot write a udev rule, so that second command lays it down. The
`$(command -v kbrgb)` is not decoration: pipx installs into `~/.local/bin`,
which sudo's `secure_path` excludes, so a bare `sudo kbrgb` would not be
found.

**From source** (any distro, needs Python 3.11+ and nothing else):

```bash
git clone https://github.com/shwetankg07/kbrgb
cd kbrgb
sudo ./install.sh      # installs kbrgb to /usr/local/bin + udev rule
kbrgb rainbow          # no sudo needed after install
```

All three paths get you the udev rule, which grants device access to whoever
is at the keyboard (`uaccess`), so everything runs as your normal user.
If the keyboard still wants sudo right after installing, replug it or reboot
once so the rule takes effect.

## Effects

| Calm | Motion | Drama | Functional |
|---|---|---|---|
| `breathe [C]` | `snake [C]` | `storm` | `cpuheat`, a CPU temp gauge |
| `aurora` | `meteor [C]` | `eruption` | `battery`, a live charge bar |
| `ocean` | `wave` | `supernova` | `load`, CPU left / GPU right |
| `lava` | `duel [C1 C2]` | `redalert [C]` | `netpulse`, live network meter |
| `candle` | `shadow [C]` | `shockwave [C]` | `clock`, hue follows the time |
| `ripple [C]` | `chase [C]` | `glitch [C]` | `pomo [MIN]`, pomodoro timer |
| `heartbeat [C]` | `rainbow` | `police [C1 C2]` | |
| `prism` | | `disco` / `sparkle [C..]` | |
| | | `matrix` / `fire` / `strobe [C]` | |

And five that react to your typing:

| Reactive | What it does |
|---|---|
| `typewriter [C]` | every keystroke glows the whole board, decays back |
| `keyflash [C]` | the zone under each key flashes and spills sideways |
| `wpmheat [WPM]` | typing speed as color: idle blue to red at your ceiling (default 96 WPM) |
| `zen [C]` | static color that fades out after `-s` idle seconds; any key wakes it |
| `flow [WPM]` | wpmheat + zen combined: speed heat that falls asleep when you do |

Flags: `-b N` for brightness (0 to 100), `-s N` for the cycle period in
seconds. Colors are optional RRGGBB hex. When you don't give any, effects
pull colors from the active [omarchy](https://omarchy.org) theme if there is
one, with sane fallbacks otherwise.

### Reactive effects and privacy

The reactive effects read key events from `/dev/input`, which requires your
user to be in the `input` group (`sudo usermod -aG input $USER`, then log
out and back in). Keycodes are used in-memory for timing and zone math
only — nothing is ever stored, logged, or sent anywhere. If you run keyd or
kmonad, events are read from the remapper's virtual keyboard, so these
effects keep working there too. `load` reads the NVIDIA dGPU only while
it's already awake — it will never wake a suspended card (or hang on one).

These are software effects: a tiny daemon streams frames to the controller
(~14 per second, the chip handles far more without complaint). They survive
suspend, the daemon just reopens the device if the i2c bus blips.

If you'd rather have the hardware do the work, `kbrgb native
breathe|neon|wave|zoom|meteor|twinkle [C]` switches the EC to one of its
builtin animations. Single write, zero CPU afterwards. `neon`, `wave` and
`zoom` are hardware color cycles and ignore the color argument, and for
natives `-s` means the EC speed, 0 to 10, and `-r` reverses the wave
(the direction byte only means something there). `kbrgb native list`
prints the map.

Other commands you'll actually use:

- `kbrgb demo` tours every effect, about 4 seconds each
- `kbrgb list` prints effect names, handy for scripts and pickers
- `kbrgb restore` replays the last setting. The controller forgets on power
  off, so wire this into a boot hook (examples for omarchy and plain systemd
  are in `examples/`)
- `kbrgb status` shows the device path, saved state and daemon state
- `kbrgb probe` is a guided hardware diagnostic, see below

The `examples/` directory also has a walker-based preset picker
(`kbrgb-menu`), a ready-made `presets.conf`, and omarchy hooks for theme sync.

## Troubleshooting

Colors set by other tools (DAMX, scripts) revert after a split second: that's
a kbrgb effect daemon repainting every frame. `kbrgb off` stops it. One
animation engine at a time, last writer wins.

Nothing happens at all: check the chip is there,

```bash
grep -l ENEK5130 /sys/class/hidraw/*/device/uevent
```

and that the udev rule landed. Packages put it in `/usr/lib/udev/rules.d`,
`install.sh` and `install-udev` put it in `/etc/udev/rules.d`, so check both:

```bash
ls /usr/lib/udev/rules.d /etc/udev/rules.d | grep kbrgb
```

Or just try once with sudo to rule out permissions.

## DAMX integration

If you use [DAMX](https://github.com/PXDiv/Div-Acer-Manager-Max), a patch
based on this protocol makes its Lighting tab work on ENEK5130 models, see
the PRs linked from
[Div-Acer-Manager-Max#172](https://github.com/PXDiv/Div-Acer-Manager-Max/issues/172).
Stop any kbrgb effect (`kbrgb off`) before driving colors from DAMX.

## Supported hardware

| Model | Status |
|---|---|
| Predator Helios Neo 16S AI (PHN16S-71) | ✅ confirmed (developed here + independent probe report) |
| Nitro ANV16S-41 | ✅ confirmed three times: `kbrgb probe` report by [abduvaliy-engineer](https://github.com/abduvaliy-engineer) in [DAMX #213](https://github.com/PXDiv/Div-Acer-Manager-Max/pull/213), plus two independent users (CachyOS daily driver + another) in [acer-predator-turbo#287](https://github.com/JafarAkhondali/acer-predator-turbo-and-rgb-keyboard-linux-module/issues/287) |
| Nitro 16S AI (AN16S-61) | 🤞 same chip, the whole A1-A4 protocol independently re-derived and hardware-verified by [ArnarValur](https://github.com/ArnarValur) in [predator-sense#31](https://github.com/cleyton1986/predator-sense/issues/31), including raw A3 dumps. kbrgb itself untested there, report back if you try it |
| Predator Helios Neo 16 (PHN16-73) | 🤞 same chip, static HID confirmed per predator-sense findings |
| Anything with `ENEK5130` in `/sys/class/hidraw/*/device/uevent` | probably. Please test and report! |

Check yours:

```bash
grep -l ENEK5130 /sys/class/hidraw/*/device/uevent
```

## Contributing

If kbrgb got your keyboard working, dropping a star helps the next person
with one of these laptops actually find this page. Beyond that, the most
useful things right now:

- **Testers with other ENEK5130 models.** Run `kbrgb probe`: it walks you
  through a guided diagnostic and prints a paste-ready report for a GitHub
  issue. That's all it takes to get your model documented.
- **Protocol spelunking.** The native effects are mapped (PROTOCOL.md), but
  there are open threads: the init sequence (`0xa4, 0x41-0x48`) seen in
  Acer's Windows DLL, the direction byte that seems to do nothing, and
  reading state back from the chip. A USB/i2c capture from Windows
  PredatorSense would answer all three at once.
- **New effects.** An effect is a ten-line pure function that returns 4 RGB
  tuples per frame. Go wild.

## Credits

- [cleyton1986/predator-sense](https://github.com/cleyton1986/predator-sense),
  the first working ENEK5130 HID implementation, which this builds on
- [0x7375646F/Linuwu-Sense](https://github.com/0x7375646F/Linuwu-Sense) and
  [PXDiv/Div-Linuwu-Sense](https://github.com/PXDiv/Div-Linuwu-Sense), the
  fan/platform driver ecosystem, and the issue threads where the community
  mapped this hardware
- [JafarAkhondali/acer-predator-turbo-and-rgb-keyboard-linux-module](https://github.com/JafarAkhondali/acer-predator-turbo-and-rgb-keyboard-linux-module),
  the original Acer RGB reverse engineering lineage

## License

MIT, see [LICENSE](https://github.com/shwetankg07/kbrgb/blob/main/LICENSE). The protocol facts belong to the community that
dug them up. This repo just tries to write them down properly.
