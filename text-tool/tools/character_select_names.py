"""Center translated shared menu names beneath the two portraits.

Text uses the original menu-ID path, shared with pause/file screens.
Only the name X/Y positions change in the selection overlay.
"""
import struct
from native_preview import line_width

NAME_IDS=('rom:0F21A8','rom:0F21BC')
PATCHES=(dict(position=0x74C,original_x=70,center=112,y_position=0x750),
         dict(position=0x834,original_x=185,center=210,y_position=0x838))

def install_names(rom,overlay,project,glyph_map,cursor):
    report=[]
    for key,patch in zip(NAME_IDS,PATCHES):
        text=project.target(project.by_id[key]);width=line_width(text)
        if not text or '\n' in text or width>96:
            raise ValueError('Character name exceeds its single-line field: '+key)
        new_x=patch['center']-width//2
        assert struct.unpack_from('>I',overlay,patch['position'])[0]==0x24050000|patch['original_x']
        struct.pack_into('>I',overlay,patch['position'],0x24050000|new_x)
        assert struct.unpack_from('>I',overlay,patch['y_position'])[0]==0x240600AA
        struct.pack_into('>I',overlay,patch['y_position'],0x240600AE)
        report.append(dict(id=key,target=text,width=width,text_x=new_x,text_y=174,patch_offsets=patch))
    return cursor,report
