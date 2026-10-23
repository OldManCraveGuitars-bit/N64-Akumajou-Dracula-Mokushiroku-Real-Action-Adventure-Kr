"""Render the exact 3bpp glyph pixels used by the ROM builder."""
from functools import lru_cache
import struct
from PIL import Image
from text_codec import ROOT
from translation_project import read_json
from font_atlas import decode_glyph
from native_font import glyph

@lru_cache(maxsize=1)
def latin_data():
    asset=read_json(ROOT/'work/manifest.json')['assets'][98]
    return (ROOT/'work/assets'/asset['file']).read_bytes()

@lru_cache(maxsize=2048)
def character_image(char):
    if char==' ':return Image.new('RGBA',(8,16))
    if 0x21<=ord(char)<0x7E:
        data=latin_data();index=ord(char)-0x20
        offset,shift=struct.unpack_from('>HH',data,0xD760+index*4)
        mask=decode_glyph(data[0xA660+offset:0xA660+offset+101],shift)
    else:mask=decode_glyph(glyph(char))
    result=Image.new('RGBA',mask.size)
    colors={0:(0,0,0,0),1:(20,15,23,255),2:(60,50,60,255),3:(90,80,90,255),4:(160,150,160,255),5:(243,231,189,255),6:(255,245,214,255),7:(255,255,255,255)}
    result.putdata([colors[min(7,p//36)] for p in mask.getdata()])
    return result

def line_width(text):return sum(character_image(c).width for c in text)

def render(text):
    lines=text.split('\n')
    widths=[line_width(s) for s in lines]
    image=Image.new('RGBA',(max(320,max(widths,default=0)+16),max(96,len(lines)*20+16)),(22,18,28,255))
    for row,line in enumerate(lines):
        x=8
        for char in line:
            im=character_image(char);image.alpha_composite(im,(x,8+row*20));x+=im.width
    return image.convert('RGB'),widths
