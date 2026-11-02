# PocketTerm35 patches for rpi5-uefi

Patches for [NumberOneGit/rpi5-uefi](https://github.com/NumberOneGit/rpi5-uefi)
(UEFI firmware for the Raspberry Pi 5) that make the PocketTerm35's built-in
keyboard work in UEFI and in anything running on it, such as GRUB or the UEFI
shell.

The keyboard is a USB device (an RP2040 running CircuitPython) on the Pi 5's
USB-C port. That port is a DWC2 OTG controller, which the stock firmware doesn't
drive. The keyboard also isn't a boot-protocol keyboard, which is the only kind
UEFI's keyboard driver supports.

## Patches

| Patch | Applies to | Commit |
|---|---|---|
| `patches/edk2-platforms-rpi5-dwc2-keyboard.patch` | `edk2-platforms` submodule | `4e426104a1f6` |
| `patches/edk2-usbkbd-report-protocol.patch` | `edk2` submodule | `15590903fe01` |

Both commits are the submodules of rpi5-uefi `ad501cf3aeb7`.

### edk2-platforms: DWC2 host on BCM2712, keyboard console entry

**The USB driver.** `DwUsbHostDxe` (the Pi 3/4 DWC2 driver) is added to the
RPi5 build, with 1:1 DMA (`PcdDmaDeviceOffset=0`, matching Linux's
`/axi dma-ranges`) and `-DDWC2_BCM2712`. Under `DWC2_BCM2712`:

- **Base address:** the controller is at `0x1000480000`.
- **Host mode:** UTMI+ PHY, forced host mode with the `GUSBCFG` values Linux uses
  for `dr_mode=host`, and a 50 ms settle after the mode change.
- **Register access:** `Wait4Bit` takes a `UINTN` register address. A 32-bit
  one truncates the 64-bit base.
- **Power state:** the mailbox's USB power-state reply is ignored. On BCM2712 it
  reports "off" for every device.

**The console entry.** The stock `ConIn` entry only matches boot keyboards
(`UsbClass(any, any, 3, 1, 1)`). `PlatformBm.c` adds a second short-form entry,
`UsbClass(0x1209, 0x0001, 3, 0, 0)`, which matches the PocketTerm keyboard and
connects it to the console.

### edk2: report-protocol support in UsbKbDxe for the PocketTerm keyboard

The keyboard's HID interface is subclass 0 / protocol 0, and CircuitPython
can't offer a boot keyboard on it. For this device only (VID `1209`, PID
`0001`), `UsbKbDxe`:

- accepts the interface, skips `SET_PROTOCOL`, and reads reports in report
  protocol;
- keeps report ID 1 and drops the ID byte. ID 1 is the keyboard report:
  modifiers, a reserved byte and 6 keys, the same layout as boot protocol;
- ignores report IDs 2 and 3 (mouse, media keys);
- prefixes the report ID to the LED `SET_REPORT`.

Other keyboards are unaffected.

## Building

```sh
git clone https://github.com/NumberOneGit/rpi5-uefi
cd rpi5-uefi
git checkout ad501cf3aeb7
git submodule update --init --recursive
git -C edk2 apply /path/to/patches/edk2-usbkbd-report-protocol.patch
git -C edk2-platforms apply /path/to/patches/edk2-platforms-rpi5-dwc2-keyboard.patch
./build.sh          # toolchain: see rpi5-uefi's README
```

## Booting it on the Pi 5

The Pi 5 bootloader loads at most 512 KB as `armstub`, and always loads the
kernel at `0x80000`. So `RPI_EFI.fd` is split there, and the second part goes in
as the kernel:

```sh
python3 split-fd.py RPI_EFI.fd     # -> rpi5-uefi-stub.bin, rpi5-uefi-kernel.bin
```

Copy both files to `uefi/` on the boot partition, then use these
`config.txt` lines:

```
arm_64bit=1
armstub=uefi/rpi5-uefi-stub.bin
kernel=uefi/rpi5-uefi-kernel.bin
kernel_address=0x80000
device_tree_address=0x3e0000
device_tree_end=0x400000
os_check=0
framebuffer_depth=32
framebuffer_ignore_alpha=1
disable_overscan=1
hdmi_force_hotplug=1
usb_max_current_enable=1
```

On D0 boards, `framebuffer_ignore_alpha=1` is needed, or the UEFI picture can
be fully transparent.

## License

The patches are under the license of the code they modify: edk2 and
edk2-platforms, BSD-2-Clause-Patent.
