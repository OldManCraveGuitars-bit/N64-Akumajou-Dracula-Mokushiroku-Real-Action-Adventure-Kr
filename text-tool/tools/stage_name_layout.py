"""Size the single-line entrance banners for the actual Korean glyph widths."""
import struct
from native_preview import line_width

ASSET_ID=182
WIDTH_TABLE_OFFSET=0x854
ORIGINAL_WIDTHS=(64,32,80,64,64,96,48,48,48,48,80,48,80)
ACTIVE_TIME_INSTRUCTION_OFFSET=0x2E4
ACTIVE_TIME_INSTRUCTION=0x240D005A

def stage_names(project):
    rows=sorted((s for s in project.segments if s['id'].startswith('asset_182:')),key=lambda s:int(s['id'].split(':')[1],16))
    if len(rows)!=13:raise ValueError('Expected 13 entrance map names')
    result=[]
    for index,segment in enumerate(rows):
        target=project.target(segment);width=line_width(target)
        if not target or '\n' in target or not 0<width<=240:
            raise ValueError('Map name must fit one line: '+segment['id'])
        result.append(dict(index=index,id=segment['id'],target=target,original_width=ORIGINAL_WIDTHS[index],width=width))
    return result

def apply_stage_name_layout(data,project):
    assert struct.unpack_from('>13H',data,WIDTH_TABLE_OFFSET)==ORIGINAL_WIDTHS,'Unexpected original stage-width table'
    assert struct.unpack_from('>I',data,ACTIVE_TIME_INSTRUCTION_OFFSET)[0]==ACTIVE_TIME_INSTRUCTION,'Stage display timer differs from the original'
    rows=stage_names(project)
    struct.pack_into('>13H',data,WIDTH_TABLE_OFFSET,*(r['width'] for r in rows))
    return dict(asset=ASSET_ID,width_table_offset=WIDTH_TABLE_OFFSET,active_time=90,
                active_time_preserved=True,names=rows)
