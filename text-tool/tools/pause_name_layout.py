"""Keep thin Hangul strokes at an integral scale in the pause header."""
import struct

SCALE_OFFSET=0x2CA4

def apply_pause_name_layout(overlay):
    # Only the character-name call loads this original 0.9f constant.
    assert struct.unpack_from('>I',overlay,0x4D0)[0]==0xC4202CA4
    assert struct.unpack_from('>I',overlay,SCALE_OFFSET)[0]==0x3F666666
    struct.pack_into('>I',overlay,SCALE_OFFSET,0x3F800000)
    return dict(offset=SCALE_OFFSET,original_scale=0.9,scale_x=1.0,scale_y=1.0)
