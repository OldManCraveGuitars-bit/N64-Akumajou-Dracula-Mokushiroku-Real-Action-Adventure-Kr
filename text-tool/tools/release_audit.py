"""Independently inspect the built ROM and invariant English/audio surfaces."""
import hashlib,json,struct
from PIL import Image
from text_codec import ROOT
from translation_project import Project,read_json
from extract_rom import decompress
from native_font import encode
from n64_crc import identify,update
from prepare_logo import native_logo,ENGLISH
from build import rebuild_block

def main():
    report=read_json(ROOT/'analysis/build-report.json');manifest=read_json(ROOT/'work/manifest.json')
    original=(ROOT/'work/original.z64').read_bytes();rom=bytes(__import__('pathlib').Path(report['output']).read_bytes())
    assert hashlib.sha256(rom).hexdigest()==report['rom_sha256']
    crc_check=bytearray(rom);update(crc_check,identify(rom));assert bytes(crc_check)==rom
    assets={}
    for asset in manifest['assets']:
        start,end=struct.unpack_from('>II',rom,asset['table_offset']);flag=start>>31;start&=0x7FFFFFFF
        assert 0<=start<end<=len(rom)
        data=decompress(rom[start:end]) if flag else rom[start:end]
        begin,finish=struct.unpack_from('>II',rom,0x971C8+asset['id']*8)
        assert begin==asset['vram'] and finish-begin==len(data)
        if asset['id'] not in report['changed_assets']:assert hashlib.sha256(data).hexdigest()==asset['sha256']
        assets[asset['id']]=data
    original98=(ROOT/'work/assets'/manifest['assets'][98]['file']).read_bytes()
    assert [i for i,(a,b) in enumerate(zip(original98,assets[98])) if a!=b]==[0xA661]
    assert len(original98)==len(assets[98]) and assets[98][0xA661]==8
    original94=(ROOT/'work/assets'/manifest['assets'][94]['file']).read_bytes()
    new_logo=native_logo(assets[94]);old_logo=native_logo(original94)
    assert new_logo.tobytes()==Image.open(ROOT/'assets/logo/korean-logo-native.png').convert('RGBA').tobytes()
    assert new_logo.crop(ENGLISH).tobytes()==old_logo.crop(ENGLISH).tobytes()
    assert original94[:0xD608]==assets[94][:0xD608] and original94[0x2B608:]==assets[94][0x2B608:]
    audio_start=0x107000;audio_end=manifest['assets'][0]['start']
    assert original[audio_start:audio_end]==rom[audio_start:audio_end]
    project=Project();assert not project.validate() and not project.stats()['pending']
    glyphs={c:int(code,16) for c,code in report['glyphs'].items()}
    blocks={b['id']:b for b in read_json(ROOT/'analysis/selected-blocks.json')}
    for relocation in report['relocations']:
        block=blocks[relocation['block']];asset=manifest['assets'][int(block['source'].split('_')[1])]
        expected,_=rebuild_block(block,project,glyphs);expected.extend(b'\0\0')
        offset=relocation['new_base']-asset['vram']
        assert assets[asset['id']][offset:offset+len(expected)]==expected
    from validate_layout import main as layout_check
    assert not layout_check()
    result=dict(rom=report['output'],sha256=report['rom_sha256'],size=len(rom),cic=identify(rom),
                asset_count=len(assets),all_asset_streams_and_sizes_valid=True,
                rebuilt_text_blocks_match_project=True,translation=project.stats(),
                latin_font_pixels_preserved=True,space_width_pixels=8,
                english_logo_pixels_preserved=True,other_title_graphics_preserved=True,
                audio_region_preserved=[audio_start,audio_end],audio_sha256=hashlib.sha256(rom[audio_start:audio_end]).hexdigest(),
                n64_header_checksum_valid=True,layout_and_english_text_validation_passed=True)
    (ROOT/'analysis/release-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
