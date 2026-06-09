#!/usr/bin/env python3
"""Convert a binary PPM (P6) to PNG using only the stdlib."""
import struct
import sys
import zlib

def read_ppm(path):
    with open(path, "rb") as f:
        data = f.read()
    # header: P6 <w> <h> <maxval>\n then raw RGB
    parts = data.split(b"\n", 3)
    assert parts[0] == b"P6"
    w, h = map(int, parts[1].split())
    return w, h, parts[3]

def write_png(path, w, h, rgb):
    def chunk(tag, payload):
        return (struct.pack(">I", len(payload)) + tag + payload
                + struct.pack(">I", zlib.crc32(tag + payload)))
    raw = b"".join(b"\x00" + rgb[y * w * 3:(y + 1) * w * 3] for y in range(h))
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)))
        f.write(chunk(b"IDAT", zlib.compress(raw, 9)))
        f.write(chunk(b"IEND", b""))

if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    w, h, rgb = read_ppm(src)
    write_png(dst, w, h, rgb)
    print(f"wrote {dst} ({w}x{h})")
