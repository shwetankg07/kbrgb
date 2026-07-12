# ENEK5130 keyboard RGB protocol notes

Verified by direct testing on an **Acer Predator Helios Neo 16S AI
(PHN16S-71)**, BIOS V1.26, 2026-07-11. Corrections/additions from other
models very welcome — open an issue.

## Device

- ENE KB5130 controller, i2c-HID bus (`0018`), VID `0x0CF2`, PID `0x5130`
- Appears as `ENEK5130:00 0CF2:5130` in `/sys/class/hidraw/*/device/uevent`
- The internal keyboard itself is a separate i2c-HID device (`1025:174B`);
  RGB goes through the ENE chip only
- The Acer WMI gaming interface (method 20 / four-zone) **accepts writes but
  does not reach this controller** — `AE_OK` is returned, LEDs never change.
  Brightness-only WMI calls do flash the LEDs briefly before being overridden.

## The `0xa4` feature report

11-byte HID feature report via `HIDIOCSFEATURE` (`ioctl 0xC00B4806`):

| Offset | Value | Meaning |
|---|---|---|
| 0 | `0xa4` | report ID |
| 1 | `0x21` | command: lighting |
| 2 | mode | **effect selector** — `0x02` = static; see the native effects table below |
| 3 | `0..100` | **brightness percent** (see finding 1) |
| 4 | speed | effect speed for dynamic modes (`0..10` tested); ignored for static |
| 5 | direction | direction for dynamic modes — appears ignored on hardware tested so far |
| 6 | R | red 0–255 (ignored by some native effects, see table) |
| 7 | G | green 0–255 |
| 8 | B | blue 0–255 |
| 9 | mask | zone select: `0x01` `0x02` `0x04` `0x08`, `0x0f` = all (see finding 2) |
| 10 | `0x00` | unknown |

Bytes 2/4/5 were documented here as "unknown, constant" until
[abduvaliy-hbai](https://github.com/abduvaliy-hbai) mapped them while working
on [DAMX PR #213](https://github.com/PXDiv/Div-Acer-Manager-Max/pull/213):
byte 2 selects the effect (`0x02` just means "static"), byte 4 is the speed,
byte 5 is a direction field. The native effects section below is documented
here with his permission.

## EC-native effects (mode byte)

The controller has onboard animations (the rainbow wave it boots with is
one). Writing a single `0xa4` report with one of these mode bytes starts
the effect and the hardware loops it on its own — no further writes, no
host-side frame streaming.

Confirmed safe values, as observed on both machines tested:

| mode | ANV16S-41 (abduvaliy-hbai) | PHN16S-71 (this repo) | RGB bytes |
|---|---|---|---|
| `0x02` | static | static | used |
| `0x04` | breathing | breathing fade | used |
| `0x05` | neon | all zones cycle the color wheel together | ignored |
| `0x07` | shifting / slide | **the boot rainbow wave**, flowing across zones | ignored |
| `0x09` | wave | **center-out bounce that cycles hue** (closest to PredatorSense "Zoom") | ignored |
| `0x0a` | meteor (snake-like) | snake-like sweep | used |
| `0x0b` | twinkling (random) | random sparkle | used |

Note the `0x07`/`0x09` rows: the two machines' reports describe them
differently (possibly firmware variance, possibly just how the same motion
reads on a 4-zone strip). Map by observed behavior on your model, not by
name. Interesting consequence: `0x09` may be the "Zoom" byte that PR #213
couldn't find — on the PHN16S-71 it is unmistakably a center-out pulse.

**Hostile values — do not send:**

| mode | behavior |
|---|---|
| `0x01`, `0x03` | lights off / black state |
| `0x06` | short flash, then reverts to the previous effect |
| `0x08` | glitchy/unstable |
| `0x0c` | freezes the current lighting until another effect is written |

Speed byte: PR #213 used `0..9` for breathing/neon and `1..10` for the
rest; `4`–`5` verified mid-speed on the PHN16S-71. Direction byte: values
`1` and `2` looked identical in PR #213's testing and ours — either the
firmware ignores it or direction lives in an unidentified byte.

A `0x02` static write cleanly reclaims control from any native effect
(verified) — that is also the safe way out if you ever hit `0x0c`.

## Findings on this EC revision

1. **Brightness byte is 0–100.** Verified: identical packet with byte 3 =
   `15` vs `100` → clearly different LED output, `100` ≈ full. Values > 100
   untested (deliberately). Earlier predator-sense versions mapped their UI
   to 1–15; after this was reported upstream
   ([predator-sense#12](https://github.com/cleyton1986/predator-sense/issues/12)),
   the maintainer confirmed `0x64` (100) was the working value in the
   original PHN16-73 capture all along and shipped the fix in
   **v0.2.27-preview**. Whether 100 = full also holds on the PHN16-73 EC
   remains unconfirmed until someone tests that machine.
2. **Correction (2026-07-12): zone mask `0x0f` works.** An earlier version
   of this document claimed the all-zones mask produced dim/incorrect
   output. That was a test artifact: the original experiment sent the
   `0x0f` packet with brightness byte 15, before the 0-100 range was
   understood, so the "broken mask" was really just 15% brightness. An
   independent probe on a second PHN16S-71 (kbrgb issue #1) showed `0x0f`
   working at brightness 100, and a retest on the original machine
   confirmed it. `0x0f` sets all four zones in one write and is safe.
   Individual masks `0x01/0x02/0x04/0x08` also work as documented,
   including four different colors simultaneously. (predator-sense removed
   its unused `ZONE_ALL` constant based on the earlier claim; a correction
   has been posted there.)
3. **No transitions, no persistence.** Writes apply instantly (no EC-side
   fade). The controller loses all state on full power-off and boots into
   its built-in color wave. Reapply on boot (see `examples/omarchy/`).
4. **Write rate**: sustained ~50–80 feature reports/sec is handled fine
   (that's how the animation engine works). No flicker, no i2c errors.
5. The Fn brightness keys adjust a global EC gain that any subsequent
   `0xa4` write overrides. While an animation streams frames, Fn changes
   appear for a split second and are then clobbered — use the tool's own
   brightness instead.
6. **Use `ioctl HIDIOCSFEATURE`, not `write()`.** On the PHN16-73,
   `write()` to the hidraw node works exactly once after boot and is then
   silently ignored; the feature-report ioctl works every time (reported by
   papodesysadmin in the
   [DAMX PR #213](https://github.com/PXDiv/Div-Acer-Manager-Max/pull/213)
   thread). `write()` has not been observed to
   misbehave on the PHN16S-71, but there is no reason to risk it — every
   packet in this document is an ioctl.

## Open questions

- **Init sequence**: `0xa4, 0x41–0x48` seen in decompiled
  `AcerECKeyboardController.dll` remains unexplored (the native effects
  above don't need it). A HID capture from Windows PredatorSense would
  settle what it does.
- **`0x07` vs `0x09`**: do these effects genuinely differ between the
  ANV16S-41 and PHN16S-71 firmwares, or do the same animations just read
  differently to different eyes? A video from each model would settle it.
- **Direction**: byte 5 appears inert. Is direction encoded elsewhere, or
  unsupported by this EC generation?
- **GET report**: reading feature report `0xa4` back (state query) untested.
- Byte 10 semantics unknown; mode bytes above `0x0c` unprobed (deliberately).
- Whether the 0–100 brightness and `0x0f` behavior are common to all
  ENEK5130 firmwares or specific to this revision — **needs testers**.
