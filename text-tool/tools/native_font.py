"""Encode Korean glyphs in the game's existing 3-bpp native font format."""
from pathlib import Path
import struct
import hashlib,json
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont, ImageChops

FONT = Path("C:/Windows/Fonts/gulim.ttc")
KANJI_BASES = (0xF2360, 0xF8960, 0xFEF60)
KANJI_TABLES = (0xF8560, 0xFEB60, 0x104B40)


@lru_cache(maxsize=1)
def frozen_glyphs():
    folder=Path(__file__).resolve().parents[1]/'assets/font'
    if not (folder/'manifest.json').exists():return {}
    manifest=json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
    data=(folder/'native-glyphs.bin').read_bytes()
    assert hashlib.sha256(data).hexdigest()==manifest['sha256']
    assert len(data)==len(manifest['characters'])*98
    return {c:data[i*98:(i+1)*98] for i,c in enumerate(manifest['characters'])}

def glyph(character: str) -> bytes:
    cached=frozen_glyphs().get(character)
    if cached is not None:return cached
    mask = Image.new("L", (16, 16))
    draw = ImageDraw.Draw(mask)
    font = ImageFont.truetype(str(FONT), 15)
    draw.text((0, 0), character, font=font, fill=255, stroke_width=0)
    mask = mask.point(lambda p: 255 if p >= 112 else 0)
    shadow = Image.new("L", (16, 16))
    shadow.paste(mask.crop((0,0,15,15)),(1,1))
    value = 0
    for foreground, background in zip(mask.getdata(),shadow.getdata()):
        value = (value << 3) | (5 if foreground else 1 if background else 0)
    return b"\x10\x10" + value.to_bytes(96, "big")


def install_resident(rom: bytearray, characters: str) -> dict[str,int]:
    unique = sorted(set(characters))
    if len(unique) > 747:
        raise ValueError(f"Resident font capacity exceeded: {len(unique)} / 747")
    mapping = {}
    for i,character in enumerate(unique):
        bank,index=divmod(i,256)
        base=KANJI_BASES[bank]
        table=KANJI_TABLES[bank]
        offset,shift=struct.unpack_from('>HH',rom,table+index*4)
        if shift or offset != index*98:
            raise ValueError("Unexpected resident font descriptor")
        rom[base+offset:base+offset+98] = glyph(character)
        mapping[character]=0x3000+i
    return mapping


def encode(text: str, mapping: dict[str,int]) -> bytes:
    words=[]
    for char in text:
        if char in mapping: words.append(mapping[char])
        elif char == '\n': words.append(1)
        elif 0x20 <= ord(char) < 0x7E: words.append(ord(char)-0x1E)
        else: raise ValueError(f"Unmapped target character: {char!r}")
    return struct.pack('>'+str(len(words))+'H',*words)
