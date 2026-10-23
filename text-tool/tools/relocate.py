"""Relocate text pointers, rejecting ambiguous shared MIPS upper constants."""
import struct


def relocate_references(data, mapper, code_end=None):
    changes=[];issues=[]
    original=bytes(data)
    for pos in range(0,len(original)-3,4):
        old=struct.unpack_from('>I',original,pos)[0]
        new=mapper(old)
        if new is not None and new!=old:
            struct.pack_into('>I',data,pos,new)
            changes.append(dict(kind='pointer',offset=pos,old=old,new=new))
    if code_end is None:code_end=len(original)
    for pos in range(0,code_end-4,4):
        lui=struct.unpack_from('>I',original,pos)[0]
        if lui>>26!=15:continue
        reg=(lui>>16)&31;upper=(lui&65535)<<16
        for use in range(pos+4,min(pos+68,code_end),4):
            ins=struct.unpack_from('>I',original,use)[0]
            op=ins>>26;rs=(ins>>21)&31;rt=(ins>>16)&31;imm=ins&65535
            if rs==reg and op in (9,13,32,33,35,36,37):
                old=upper+(imm if op==13 or imm<0x8000 else imm-0x10000)
                new=mapper(old)
                if new is not None:
                    new_upper=(new&0xFFFF0000) if op==13 else ((new+0x8000)&0xFFFF0000)
                    if new_upper!=upper:
                        if rt!=reg or op not in (9,13):
                            issues.append(dict(lui=pos,use=use,old=old,new=new,reason='shared MIPS upper constant'))
                        else:
                            struct.pack_into('>I',data,pos,(lui&0xFFFF0000)|(new_upper>>16))
                            struct.pack_into('>I',data,use,(ins&0xFFFF0000)|(new&65535))
                            changes.append(dict(kind='mips_address',offset=use,lui=pos,old=old,new=new))
                    else:
                        struct.pack_into('>I',data,use,(ins&0xFFFF0000)|(new&65535))
                        changes.append(dict(kind='mips_address',offset=use,lui=pos,old=old,new=new))
            # A new value in reg ends this constant's live range.
            if (op in (8,9,12,13,14,15,32,33,35,36,37) and rt==reg) or (op==0 and (ins&63)==8):break
    return changes,issues
