"""N64 checksum, with seed/type confirmed against the original header."""
import struct
MASK = 0xFFFFFFFF

def calculate(data, cic=6102):
    seed = {6101: 0xF8CA4DDC, 6102: 0xF8CA4DDC, 6103: 0xA3886759,
            6105: 0xDF26F436, 6106: 0x1FEA617A}[cic]
    t1 = t2 = t3 = t4 = t5 = t6 = seed
    for pos in range(0x1000, 0x101000, 4):
        d = struct.unpack_from('>I', data, pos)[0]
        if (t6+d)&MASK < t6:
            t4 = (t4+1)&MASK
        t6 = (t6+d)&MASK
        t3 ^= d
        s = d&31
        r = ((d << s) | (d >> (32-s)))&MASK
        t5 = (t5+r)&MASK
        t2 ^= r if t2 > d else t6^d
        if cic == 6105:
            t1 = (t1+(struct.unpack_from('>I', data, 0x750+(pos&0xFF))[0]^d))&MASK
        else:
            t1 = (t1+(t5^d))&MASK
    if cic == 6103:
        return ((t6^t4)+t3)&MASK, ((t5^t2)+t1)&MASK
    if cic == 6106:
        return (t6*t4+t3)&MASK, (t5*t2+t1)&MASK
    return t6^t4^t3, t5^t2^t1

def identify(data):
    expected = struct.unpack_from('>II', data, 0x10)
    for cic in (6102, 6103, 6105, 6106):
        if calculate(data, cic) == expected:
            return cic
    raise ValueError('Original N64 checksum does not match a supported CIC')

def update(data, cic):
    struct.pack_into('>II', data, 0x10, *calculate(data, cic))
