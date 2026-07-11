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

## Static zone color — feature report `0xa4`

11-byte HID feature report via `HIDIOCSFEATURE` (`ioctl 0xC00B4806`):

| Offset | Value | Meaning |
|---|---|---|
| 0 | `0xa4` | report ID |
| 1 | `0x21` | command: static zone color |
| 2 | `0x02` | unknown, constant |
| 3 | `0..100` | **brightness percent** (see finding 1) |
| 4 | `0x00` | unknown |
| 5 | `0x00` | unknown |
| 6 | R | red 0–255 |
| 7 | G | green 0–255 |
| 8 | B | blue 0–255 |
| 9 | mask | zone select: `0x01` `0x02` `0x04` `0x08` (see finding 2) |
| 10 | `0x00` | unknown |

## Findings on this EC revision

1. **Brightness byte is 0–100.** predator-sense maps its UI to 1–15
   (`hid_rgb.rs` comment: "Protocol brightness range is 0x01-0x0f"), which on
   this EC yields 15% brightness. Verified: identical packet with byte 3 =
   `15` vs `100` → clearly different LED output, `100` ≈ full. Values > 100
   untested (deliberately).
2. **Zone mask `0x0f` ("all zones") misbehaves** — output is dim/incorrect.
   Individual masks `0x01/0x02/0x04/0x08` (one write per zone) work exactly
   as expected, including four different colors simultaneously.
3. **No transitions, no persistence.** Writes apply instantly (no EC-side
   fade). The controller loses all state on full power-off and boots into
   its built-in color wave. Reapply on boot (see `examples/omarchy/`).
4. **Write rate**: sustained ~50–80 feature reports/sec is handled fine
   (that's how the animation engine works). No flicker, no i2c errors.
5. The Fn brightness keys adjust a global EC gain that any subsequent
   `0xa4` write overrides. While an animation streams frames, Fn changes
   appear for a split second and are then clobbered — use the tool's own
   brightness instead.

## Open questions

- **Native effects**: the EC clearly has onboard animations (its boot wave).
  Command bytes other than `0x21`, and the init sequence `0xa4, 0x41–0x48`
  seen in decompiled `AcerECKeyboardController.dll`, are unexplored. A HID
  capture from Windows PredatorSense while switching effects would settle it.
- **GET report**: reading feature report `0xa4` back (state query) untested.
- Byte 2 (`0x02`) and bytes 4/5/10 semantics unknown.
- Whether the 0–100 brightness and `0x0f` behavior are common to all
  ENEK5130 firmwares or specific to this revision — **needs testers**.
