"""Decode CV64's native 3-bit glyphs for inspection."""
from pathlib import Path
import json
import struct
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]


def decode_glyph(data: bytes, bit_offset: int = 0) -> Image.Image:
    if bit_offset:
        data = ((int.from_bytes(data, "big") << bit_offset) & ((1 << (len(data) * 8)) - 1)).to_bytes(len(data), "big")
    height, width = data[:2]
    if not 0 < height <= 16 or not 0 < width <= 16:
        raise ValueError((height, width))
    bits = int.from_bytes(data[2:2 + (height * width * 3 + 7) // 8], "big")
    padding = (-height * width * 3) % 8
    values = [((bits >> (padding + (height * width - i - 1) * 3)) & 7) * 36
              for i in range(height * width)]
    im = Image.new("L", (width, height))
    im.putdata(values)
    return im


def render() -> None:
    manifest = json.loads((ROOT / "work/manifest.json").read_text())
    data = (ROOT / "work/assets" / manifest["assets"][98]["file"]).read_bytes()
    font = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 12)
    out = ROOT / "analysis"
    out.mkdir(exist_ok=True)
    for name, first, base, table, count in [
        ("latin", 2, 0xA660, 0xD760, 128),
        ("hiragana", 0x1000, 0xD960, 0xF800, 80),
        ("katakana", 0x2000, 0xF940, 0x11E00, 80),
    ]:
        atlas = Image.new("RGB", (16 * 62, ((count + 15) // 16) * 55), "#303030")
        draw = ImageDraw.Draw(atlas)
        for i in range(count):
            offset, indent = struct.unpack_from(">HH", data, table + i * 4)
            try:
                glyph = decode_glyph(data[base + offset:base + offset + 99], indent)
            except ValueError:
                continue
            x, y = i % 16 * 62, i // 16 * 55
            atlas.paste(glyph.resize((glyph.width * 2, glyph.height * 2), Image.Resampling.NEAREST), (x,y))
            draw.text((x,y+32), f"{first+i:04X}", font=font, fill="white")
        atlas.save(out / f"{name}.png")


if __name__ == "__main__":
    render()
