"""Inventory the supplied Japanese ROM; never modify the input ROM."""
from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / "work/original.z64"


def decompress(data: bytes) -> bytes:
    end = int.from_bytes(data[1:4], "big")
    if not 4 <= end <= len(data):
        raise ValueError(f"Invalid compressed size {end:x}/{len(data):x}")
    out = bytearray()
    pos = 4
    while pos < end:
        cmd = data[pos]
        pos += 1
        if cmd < 0x80:
            back = ((cmd << 8) | data[pos]) & 0x3FF
            pos += 1
            if back == 0 or back > len(out):
                raise ValueError(f"Invalid back reference at {pos:x}")
            for _ in range(2 + (cmd >> 2)):
                out.append(out[-back])
        elif cmd < 0xA0:
            count = cmd & 0x1F
            out.extend(data[pos:pos + count])
            pos += count
        else:
            value = 0
            count = 2 + (cmd & 0x1F)
            if cmd == 0xFF:
                count = 2 + data[pos]
                pos += 1
            elif cmd < 0xE0:
                value = data[pos]
                pos += 1
            out.extend(bytes([value]) * count)
        if len(out) > 0x1000000:
            raise ValueError("Decompression limit")
    if pos != end:
        raise ValueError("Command crossed stream boundary")
    return bytes(out)


def extract() -> None:
    rom = ROM.read_bytes()
    if hashlib.sha1(rom).hexdigest()!='aa70348968589e6ba6e7091ca115fb505099cd97':
        raise ValueError('지원하는 일본판 원본 롬이 아닙니다.')
    metadata=json.loads((ROOT/'data/asset_metadata.json').read_text(encoding='utf-8'))
    table = rom.index(b"Nisitenma-Ichigo") + 16
    outdir = ROOT / "work/assets"
    outdir.mkdir(parents=True, exist_ok=True)
    records = []
    for i in range(2000):
        entry = table + i * 8
        start_word, end = struct.unpack_from(">II", rom, entry)
        if start_word == 0:
            break
        start = start_word & 0xFFFFFF
        if not (start <= end <= len(rom)):
            raise ValueError(f"Bad file entry {i}: {start_word:x}, {end:x}")
        compressed = bool(start_word & 0x80000000)
        source = rom[start:end]
        decoded = decompress(source) if compressed else source
        filename = f"{i:03d}_{start:08X}.bin"
        (outdir / filename).write_bytes(decoded)
        expected=metadata[i]
        assert expected['id']==i and expected['size']==len(decoded)
        assert expected['sha256']==hashlib.sha256(decoded).hexdigest()
        vram=struct.unpack_from('>I',rom,0x971C8+i*8)[0]
        records.append(dict(id=i, table_offset=entry, start=start, end=end,
                            compressed=compressed, size=len(decoded), file=filename,
                            sha256=hashlib.sha256(decoded).hexdigest(),vram=vram,
                            reference_name=expected['reference_name']))
    manifest = dict(rom_sha1=hashlib.sha1(rom).hexdigest(),
                    rom_sha256=hashlib.sha256(rom).hexdigest(),
                    table_offset=table, assets=records)
    (ROOT / "work/manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Extracted {len(records)} assets, {sum(r['size'] for r in records):,} bytes, table {table:08X}")
    print("Largest assets:")
    for r in sorted(records, key=lambda r: r["size"], reverse=True)[:12]:
        print(r["id"], hex(r["start"]), hex(r["size"]))


if __name__ == "__main__":
    extract()
