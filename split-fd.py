#!/usr/bin/env python3
"""Split RPI_EFI.fd for the Pi 5 bootloader: rpi5-uefi-stub.bin + rpi5-uefi-kernel.bin.

The Pi 5 firmware loads at most 512 KB of armstub and always loads the
"kernel" at 0x80000, on top of the rest of the FD. So the FD is cut at
0x80000: the first 512 KB goes in as armstub, the remainder as the kernel,
which then lands exactly where it belongs.
"""
import sys
src = sys.argv[1] if len(sys.argv) > 1 else "RPI_EFI.fd"
d = open(src, "rb").read()
open("rpi5-uefi-stub.bin", "wb").write(d[:0x80000])
open("rpi5-uefi-kernel.bin", "wb").write(d[0x80000:])
print(f"{src}: {len(d)} bytes -> rpi5-uefi-stub.bin + rpi5-uefi-kernel.bin")
