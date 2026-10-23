"""Small, auditable encoder for Konami's LZKN64 stream format."""
from collections import defaultdict, deque
from extract_rom import decompress


def compress(data: bytes) -> bytes:
    data=bytes(data)
    stream=bytearray(4)
    literals=bytearray()
    positions=defaultdict(deque)

    def flush():
        while literals:
            n=min(31,len(literals))
            stream.append(0x80+n);stream.extend(literals[:n]);del literals[:n]

    pos=0
    while pos<len(data):
        run=1
        limit=257 if data[pos]==0 else 33
        while run<limit and pos+run<len(data) and data[pos+run]==data[pos]:run+=1
        best_length=0;best_back=0
        key=data[pos:pos+3]
        candidates=positions[key]
        while candidates and pos-candidates[0]>0x3FF:candidates.popleft()
        for previous in reversed(candidates):
            length=0
            while length<33 and pos+length<len(data) and data[previous+length]==data[pos+length]:length+=1
            if length>best_length:best_length=length;best_back=pos-previous
            if best_length==33:break
        if run>=3 and run>=best_length:
            flush();count=run
            if data[pos]==0:
                if count<=32:stream.append(0xE0+(count-2))
                else:stream.extend((0xFF,count-2))
            else:stream.extend((0xC0+(count-2),data[pos]))
        elif best_length>=3:
            flush();count=best_length
            stream.extend((((count-2)<<2)|(best_back>>8),best_back&255))
        else:
            count=1;literals.append(data[pos])
            if len(literals)==31:flush()
        for k in range(pos,pos+count):positions[data[k:k+3]].append(k)
        pos+=count
    flush()
    stream[:4]=len(stream).to_bytes(4,'big')
    if decompress(stream)!=data:raise ValueError('LZKN64 roundtrip mismatch')
    return bytes(stream)
