# -*- coding: utf-8 -*-
"""把“手机画框”页面截图的 390x844 区域裁出来（纯标准库，无需 Pillow）。

用法：python tools/crop.py 输入.png 输出.png [宽 高 左 上]
"""
import struct
import sys
import zlib
from pathlib import Path


def load_png(path):
    data = Path(path).read_bytes()
    pos, w, h, idat, bpp = 8, 0, 0, b"", 3
    while pos < len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        tag = data[pos + 4:pos + 8]
        chunk = data[pos + 8:pos + 8 + length]
        if tag == b"IHDR":
            w, h, depth, color = struct.unpack(">IIBB", chunk[:10])
            assert depth == 8 and color in (2, 6), (depth, color)
            bpp = 3 if color == 2 else 4
        elif tag == b"IDAT":
            idat += chunk
        pos += 12 + length
    raw = zlib.decompress(idat)
    stride = w * bpp
    rows, prev, i = [], bytearray(stride), 0
    for _ in range(h):
        ft = raw[i]; i += 1
        line = bytearray(raw[i:i + stride]); i += stride
        if ft == 1:
            for x in range(bpp, stride):
                line[x] = (line[x] + line[x - bpp]) & 0xFF
        elif ft == 2:
            for x in range(stride):
                line[x] = (line[x] + prev[x]) & 0xFF
        elif ft == 3:
            for x in range(stride):
                left = line[x - bpp] if x >= bpp else 0
                line[x] = (line[x] + ((left + prev[x]) >> 1)) & 0xFF
        elif ft == 4:
            for x in range(stride):
                a = line[x - bpp] if x >= bpp else 0
                b = prev[x]
                c = prev[x - bpp] if x >= bpp else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[x] = (line[x] + pr) & 0xFF
        rows.append(bytes(line))
        prev = line
    return w, h, bpp, rows


def save_png(path, w, h, rows):
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        raw += rows[y]
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)

    def chunk(tag, payload):
        return (struct.pack(">I", len(payload)) + tag + payload
                + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF))

    Path(path).write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
                           + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
                           + chunk(b"IEND", b""))


def main():
    src, dst = sys.argv[1], sys.argv[2]
    cw = int(sys.argv[3]) if len(sys.argv) > 3 else 390
    ch = int(sys.argv[4]) if len(sys.argv) > 4 else 844
    left = int(sys.argv[5]) if len(sys.argv) > 5 else 0
    top = int(sys.argv[6]) if len(sys.argv) > 6 else 0
    w, h, bpp, rows = load_png(src)
    cw, ch = min(cw, w - left), min(ch, h - top)
    out = []
    for y in range(top, top + ch):
        line = rows[y][left * bpp:(left + cw) * bpp]
        out.append(bytes(line[x * bpp:x * bpp + 3] for x in range(cw))
                   if bpp == 4 else line)
    save_png(dst, cw, ch, out)
    print(f"已裁剪 {w}x{h} -> {cw}x{ch}  {dst}")


if __name__ == "__main__":
    main()
