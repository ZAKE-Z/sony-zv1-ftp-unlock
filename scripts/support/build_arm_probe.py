"""Reproducible tiny ARM EABI ELF. No compiler or runtime dependencies."""
import struct
from pathlib import Path

MESSAGE = b'\nZV1_ARM_RAM_OK\n'

def build():
    # ARM mode instructions, also supplied as arm_probe.S.
    words = (0xe3a00001, 0xe28f1014, 0xe3a02000 | len(MESSAGE),
             0xe3a07004, 0xef000000, 0xe3a00000, 0xe3a07001, 0xef000000)
    body = struct.pack('<8I', *words) + MESSAGE
    size = 84 + len(body)
    ident = b'\x7fELF\x01\x01\x01' + bytes(9)
    header = struct.pack('<16sHHIIIIIHHHHHH', ident, 2, 40, 1,
                         0x10054, 52, 0, 0x05000200, 52, 32, 1, 0, 0, 0)
    segment = struct.pack('<8I', 1, 0, 0x10000, 0x10000, size, size, 5, 4096)
    return header + segment + body

if __name__ == '__main__':
    out = Path(__file__).with_name('arm_probe.elf')
    out.write_bytes(build())
    print(out.name, out.stat().st_size)
