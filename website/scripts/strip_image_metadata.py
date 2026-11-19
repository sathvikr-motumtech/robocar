#!/usr/bin/env python3
"""Remove privacy-sensitive metadata (EXIF incl. GPS, XMP, IPTC, comments) from images.

Usage:
    python3 scripts/strip_image_metadata.py [--check] [paths...]   (default path: content/)

    --check   don't modify anything; exit 1 if any image still has metadata
              (used in CI so a photo with GPS data can never be published)

JPEG: drops APP1 (EXIF/XMP), APP13 (IPTC) and COM segments; keeps the ICC color profile.
PNG:  drops tEXt/zTXt/iTXt/eXIf/tIME chunks.
WebP: drops EXIF/XMP chunks.
Pixels are never re-encoded, so image quality is unchanged.
"""
import struct
import sys
from pathlib import Path

JPEG_DROP = {0xE1, 0xED, 0xFE}  # APP1, APP13, COM
PNG_DROP = {b"tEXt", b"zTXt", b"iTXt", b"eXIf", b"tIME"}
WEBP_DROP = {b"EXIF", b"XMP "}


def exif_orientation(app1: bytes) -> int:
    """Return the EXIF orientation (1 = normal) from an APP1 payload, or 1 if absent."""
    if not app1.startswith(b"Exif\x00\x00"):
        return 1
    t = app1[6:]
    e = ">" if t[:2] == b"MM" else "<"
    off = struct.unpack(e + "I", t[4:8])[0]
    (n,) = struct.unpack(e + "H", t[off:off + 2])
    for k in range(n):
        tag, _, _, val = struct.unpack(e + "HHIH", t[off + 2 + 12 * k: off + 12 + 12 * k])
        if tag == 0x0112:
            return val
    return 1


def strip_jpeg(data: bytes, name: str) -> tuple[bytes, list[str]]:
    out, found, i = bytearray(data[:2]), [], 2
    while i < len(data):
        if data[i] != 0xFF:
            raise ValueError(f"{name}: unexpected JPEG structure")
        marker = data[i + 1]
        if marker == 0xDA:  # start of scan: rest is image data
            out += data[i:]
            break
        (length,) = struct.unpack(">H", data[i + 2:i + 4])
        seg = data[i:i + 2 + length]
        if marker in JPEG_DROP:
            payload = seg[4:]
            label = {0xE1: "EXIF/XMP", 0xED: "IPTC", 0xFE: "comment"}[marker]
            if marker == 0xE1 and exif_orientation(payload) != 1:
                print(f"  WARNING {name}: EXIF says rotate (orientation {exif_orientation(payload)}); "
                      "after stripping it may display sideways - rotate it in Preview and re-run.")
            found.append(label)
        else:
            out += seg
        i += 2 + length
    return bytes(out), found


def strip_png(data: bytes, name: str) -> tuple[bytes, list[str]]:
    out, found, i = bytearray(data[:8]), [], 8
    while i < len(data):
        (length,) = struct.unpack(">I", data[i:i + 4])
        ctype = data[i + 4:i + 8]
        chunk = data[i:i + 12 + length]
        if ctype in PNG_DROP:
            found.append(ctype.decode())
        else:
            out += chunk
        i += 12 + length
    return bytes(out), found


def strip_webp(data: bytes, name: str) -> tuple[bytes, list[str]]:
    out, found, i = bytearray(), [], 12
    while i < len(data):
        ctype = data[i:i + 4]
        (length,) = struct.unpack("<I", data[i + 4:i + 8])
        chunk = data[i:i + 8 + length + (length & 1)]
        if ctype in WEBP_DROP:
            found.append(ctype.decode().strip())
        else:
            out += chunk
        i += len(chunk)
    if found and out[:4] == b"VP8X":  # clear the EXIF (0x08) and XMP (0x04) flags
        out[8] &= ~0x0C & 0xFF
    return b"RIFF" + struct.pack("<I", len(out) + 4) + b"WEBP" + bytes(out), found


HANDLERS = {".jpg": strip_jpeg, ".jpeg": strip_jpeg, ".png": strip_png, ".webp": strip_webp}


def main(argv):
    check = "--check" in argv
    roots = [Path(a) for a in argv if a != "--check"] or [Path("content")]
    files = [p for r in roots for p in ([r] if r.is_file() else r.rglob("*"))
             if p.suffix.lower() in HANDLERS]
    dirty = 0
    for p in sorted(files):
        data = p.read_bytes()
        cleaned, found = HANDLERS[p.suffix.lower()](data, str(p))
        if not found:
            continue
        dirty += 1
        if check:
            print(f"HAS METADATA  {p}: {', '.join(sorted(set(found)))}")
        else:
            p.write_bytes(cleaned)
            print(f"stripped      {p}: {', '.join(sorted(set(found)))}")
    if check and dirty:
        print(f"\n{dirty} image(s) contain metadata. Run: python3 scripts/strip_image_metadata.py")
        return 1
    if not dirty:
        print(f"OK: {len(files)} image(s) checked, no metadata found")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
