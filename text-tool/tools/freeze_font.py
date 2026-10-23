"""Freeze the reviewed native glyph pixels for reproducible builds."""
import hashlib,json
from native_font import glyph
from translation_project import Project
from text_codec import ROOT

def main():
    project=Project();characters=sorted({c for s in project.segments for c in project.target(s) if ord(c)>127})
    data=b''.join(glyph(c) for c in characters)
    folder=ROOT/'assets/font';folder.mkdir(exist_ok=True,parents=True)
    (folder/'native-glyphs.bin').write_bytes(data)
    (folder/'manifest.json').write_text(json.dumps(dict(characters=''.join(characters),glyph_bytes=98,sha256=hashlib.sha256(data).hexdigest(),source='Windows Gulim 15px, threshold 112, native 3bpp foreground 5 / shadow 1'),ensure_ascii=False,indent=2),encoding='utf-8')
    print(len(characters),'native glyphs frozen')

if __name__=='__main__':main()
