"""Build the Korean translation candidate reproducibly.

Original ROM is immutable. Runtime QA is tracked separately from compilation.
"""
from __future__ import annotations
import hashlib
import json
import struct
from text_codec import ROOT
from translation_project import Project,read_json
from native_font import install_resident,encode
from lzkn64 import compress
from relocate import relocate_references
from n64_crc import identify,update
from stage_name_layout import apply_stage_name_layout


def rebuild_block(block,project,glyph_map):
    spans={int(s['id'].split(':')[1],16):s for s in project.segments if s['id'].startswith(block['source']+':')}
    words=block['words'];out=bytearray();mapping={};i=0
    while i<len(words):
        source_offset=block['offset']+i*2
        span=spans.get(source_offset)
        if span:
            target=project.target(span)
            if not target:raise ValueError(f"Untranslated span {span['id']}")
            payload=encode(target,glyph_map)
            for j in range(len(span['words'])):
                mapping[i*2+j*2]=len(out)+min(j*2,max(0,len(payload)-2))
            out.extend(payload);i+=len(span['words'])
        else:
            mapping[i*2]=len(out);out.extend(struct.pack('>H',words[i]));i+=1
    original_controls=[w for w in words if w>=0xA000]
    new_words=struct.unpack('>'+str(len(out)//2)+'H',out)
    assert [w for w in new_words if w>=0xA000]==original_controls,'Text control words changed'
    return out,mapping


def main():
    project=Project();errors=project.validate()
    if errors:raise ValueError(errors)
    if project.stats()['pending']:raise ValueError('Translation catalog is incomplete')
    manifest=read_json(ROOT/'work/manifest.json');blocks=read_json(ROOT/'analysis/selected-blocks.json')
    original=(ROOT/'work/original.z64').read_bytes()
    assert hashlib.sha1(original).hexdigest()=='aa70348968589e6ba6e7091ca115fb505099cd97'
    rom=bytearray(original);cic=identify(rom)
    characters=''.join(c for s in project.segments for c in project.target(s) if ord(c)>0x7E)
    characters=characters.replace('\n','')
    glyph_map=install_resident(rom,characters)
    assets={a['id']:bytearray((ROOT/'work/assets'/a['file']).read_bytes()) for a in manifest['assets']}
    stage_layout=apply_stage_name_layout(assets[182],project)
    changed=set();report=[];issues=[]
    for block in [b for b in blocks if b['source']!='rom']:
        asset_id=int(block['source'].split('_')[1]);asset=manifest['assets'][asset_id];data=assets[asset_id]
        expected=struct.pack('>'+str(len(block['words']))+'H',*block['words'])
        assert bytes(data[block['offset']:block['end']])==expected
        payload,offset_map=rebuild_block(block,project,glyph_map)
        payload.extend(b'\x00\x00')
        while len(data)%16:data.append(0)
        new_offset=len(data)
        old_base=asset['vram']+block['offset'];old_end=asset['vram']+block['end'];new_base=asset['vram']+new_offset
        def mapper(value):
            if old_base<=value<old_end:
                delta=value-old_base
                if delta%2:raise ValueError('Odd text pointer')
                return new_base+offset_map[delta]
            return None
        refs,problems=relocate_references(data,mapper,block['offset'])
        for ref in block.get('branch_address_refs',[]):
            high=struct.unpack_from('>I',data,ref['lui'])[0]
            low=struct.unpack_from('>I',data,ref['use'])[0]
            assert high>>26==15 and (high>>16)&31==ref['register']
            assert low>>26==9 and (low>>21)&31==ref['register'] and (low>>16)&31==ref['register']
            old=((high&65535)<<16)+(low&65535 if low&65535<0x8000 else (low&65535)-0x10000)
            assert old==old_base
            struct.pack_into('>I',data,ref['lui'],high&0xFFFF0000|((new_base+0x8000)>>16))
            struct.pack_into('>I',data,ref['use'],low&0xFFFF0000|(new_base&65535))
            refs.append(dict(kind='branch_delay_mips_address',offset=ref['use'],lui=ref['lui'],old=old,new=new_base))
        if 'external_pointer' in block:
            pointer_offset=block['external_pointer']
            assert struct.unpack_from('>I',rom,pointer_offset)[0]==old_base
            struct.pack_into('>I',rom,pointer_offset,new_base)
            refs.append(dict(kind='map_pool',rom_offset=pointer_offset,old=old_base,new=new_base))
        if not refs:problems.append(dict(reason='no incoming reference',block=block['id']))
        issues.extend(dict(source=block['source'],**p) for p in problems)
        data.extend(payload);changed.add(asset_id)
        report.append(dict(block=block['id'],old_base=old_base,new_base=new_base,old_size=len(expected),new_size=len(payload),references=refs))
    # Allocate common text in resident kanji slots not used by the Korean font.
    common_start=0xFEF60+max(0,len(glyph_map)-512)*98
    common_start=(common_start+15)&~15
    cursor=common_start;resident=[]
    for block in [b for b in blocks if b['source']=='rom']:
        payload,offset_map=rebuild_block(block,project,glyph_map)
        payload.extend(b'\x00\x00')
        resident.append(dict(old_base=0x8007D0A0+block['offset'],old_end=0x8007D0A0+block['end'],
                             new_base=0x8007D0A0+cursor,mapping=offset_map,block=block['id']))
        rom[cursor:cursor+len(payload)]=payload;cursor+=len(payload)
    if cursor>0x104B40:raise ValueError(f'Resident text exceeds font reserve: {cursor:08X}')
    def resident_mapper(value):
        for item in resident:
            if item['old_base']<=value<item['old_end']:
                relative=value-item['old_base']
                if relative%2:raise ValueError('Odd resident text pointer')
                return item['new_base']+item['mapping'][relative]
        return None
    # Scan original code/data surfaces; exclude the newly written translated payload.
    prefix=rom[:common_start]
    refs,problems=relocate_references(prefix,resident_mapper,min(common_start,0xF1E80))
    rom[:common_start]=prefix
    issues.extend(dict(source='rom',**p) for p in problems)
    resident_refs=[dict(source='rom',**r) for r in refs]
    suffix_start=0x104F00
    suffix=rom[suffix_start:manifest['assets'][0]['start']]
    refs,problems=relocate_references(suffix,resident_mapper,0)
    rom[suffix_start:manifest['assets'][0]['start']]=suffix
    issues.extend(dict(source='rom_suffix',**p) for p in problems)
    resident_refs.extend(dict(source='rom_suffix',offset=r['offset']+suffix_start,old=r['old'],new=r['new'],kind=r['kind']) for r in refs)
    for asset_id,data in assets.items():
        refs,problems=relocate_references(data,resident_mapper)
        if refs:changed.add(asset_id)
        resident_refs.extend(dict(source=f'asset_{asset_id:03d}',**r) for r in refs)
        issues.extend(dict(source=f'asset_{asset_id:03d}',**p) for p in problems)
    assets[98][0xA661]=8;changed.add(98)
    logo_path=ROOT/'assets/logo/korean-logo-native.png'
    if logo_path.exists():
        from PIL import Image,ImageOps
        from prepare_logo import native_logo,ENGLISH
        logo=Image.open(logo_path).convert('RGBA')
        assert logo.size==(320,96)
        assert logo.crop(ENGLISH).tobytes()==native_logo(assets[94]).crop(ENGLISH).tobytes(),'English logo pixels changed'
        for n in range(30):
            x=n%10*32;y=n//10*32
            tile=ImageOps.flip(logo.crop((x,y,x+32,y+32)))
            pos=0xD608+n*4096
            assets[94][pos:pos+4096]=tile.tobytes()
        changed.add(94)
    # The game also embeds typed (virtual-start, virtual-end, file-ID, flags)
    # loader records. Allocation uses these records, independently of the
    # central size table. Growing a file without updating them corrupts heaps.
    allocation_records=[]
    surfaces=[('rom',rom)]+[(f'asset_{i:03d}',data) for i,data in assets.items()]
    for surface,data in surfaces:
        limit=min(len(data),manifest['assets'][0]['start']) if surface=='rom' else manifest['assets'][int(surface.split('_')[1])]['size']
        for pos in range(0,limit-11,4):
            start,end,file_id=struct.unpack_from('>IIH',data,pos)
            if not 1<=file_id<=len(manifest['assets']):continue
            loaded=manifest['assets'][file_id-1]
            if loaded['vram']!=start or end!=start+loaded['size']:continue
            if file_id-1 not in changed:continue
            new_end=start+len(assets[file_id-1])
            if new_end==end:continue
            struct.pack_into('>I',data,pos+4,new_end)
            allocation_records.append(dict(source=surface,offset=pos,file_id=file_id,old_end=end,new_end=new_end))
            if surface!='rom':changed.add(int(surface.split('_')[1]))
    report_path=ROOT/'analysis/build-report.json'
    metadata=dict(status='private candidate; runtime QA in progress',
                  catalog=project.stats(),resident_text_start=common_start,resident_text_end=cursor,
                  glyphs={c:f'{v:04X}' for c,v in glyph_map.items()},relocations=report,
                  resident_references=resident_refs,allocation_records=allocation_records,issues=issues,
                  stage_name_layout=stage_layout)
    report_path.write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
    if issues:raise ValueError(f"{len(issues)} unresolved relocations; see {report_path}")
    for asset_id in sorted(changed):
        data=assets[asset_id]
        while len(rom)%16:rom.append(0)
        start=len(rom);rom.extend(compress(data))
        struct.pack_into('>II',rom,manifest['assets'][asset_id]['table_offset'],start|0x80000000,len(rom))
        struct.pack_into('>I',rom,0x971C8+asset_id*8+4,manifest['assets'][asset_id]['vram']+len(data))
    if len(rom)>0x1000000:raise ValueError('Candidate exceeds 16 MiB address audit boundary')
    rom.extend(bytes(0x1000000-len(rom)));update(rom,cic)
    dest=ROOT/'work/korean-candidate-v008.z64';dest.write_bytes(rom)
    metadata.update(rom_sha256=hashlib.sha256(rom).hexdigest(),changed_assets=sorted(changed),output=str(dest),cic=cic)
    report_path.write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(output=str(dest),changed_assets=len(changed),catalog=project.stats(),resident_bytes=cursor-common_start),ensure_ascii=False,indent=2))


if __name__=='__main__':main()
