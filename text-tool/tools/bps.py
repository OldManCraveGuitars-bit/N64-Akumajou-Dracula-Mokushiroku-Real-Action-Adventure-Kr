"""Small standard BPS1 encoder/decoder with source, target and patch CRC checks.

The encoder uses SourceRead and TargetRead. The decoder accepts all four BPS
actions, so output patches also work in normal BPS patching applications.
"""
import struct
import zlib

def number(value):
    out=bytearray()
    while True:
        byte=value&127;value>>=7
        if not value:out.append(byte|128);return out
        out.append(byte);value-=1

def read_number(data,cursor):
    value=0;shift=1
    while True:
        if cursor>=len(data):raise ValueError('잘린 BPS 숫자입니다.')
        byte=data[cursor];cursor+=1;value+=(byte&127)*shift
        if byte&128:return value,cursor
        shift<<=7;value+=shift
        if shift>1<<63:raise ValueError('잘못된 BPS 숫자입니다.')

def create(source,target,metadata=b''):
    patch=bytearray(b'BPS1')+number(len(source))+number(len(target))+number(len(metadata))+metadata
    pos=0
    while pos<len(target):
        if pos<len(source) and source[pos]==target[pos]:
            end=pos+1
            while end<min(len(source),len(target)) and source[end]==target[end]:end+=1
            patch.extend(number((end-pos-1)<<2));pos=end
        else:
            end=pos+1
            while end<len(target):
                if end<len(source) and source[end:end+16]==target[end:end+16]:break
                end+=1
            patch.extend(number(((end-pos-1)<<2)|1));patch.extend(target[pos:end]);pos=end
    patch.extend(struct.pack('<II',zlib.crc32(source),zlib.crc32(target)))
    patch.extend(struct.pack('<I',zlib.crc32(patch)))
    assert apply(source,patch)==target
    return bytes(patch)

def apply(source,patch):
    if patch[:4]!=b'BPS1' or len(patch)<19:raise ValueError('BPS1 패치가 아닙니다.')
    source_crc,target_crc,patch_crc=struct.unpack_from('<III',patch,len(patch)-12)
    if zlib.crc32(patch[:-4])!=patch_crc:raise ValueError('패치 파일이 손상되었습니다.')
    if zlib.crc32(source)!=source_crc:raise ValueError('원본 롬 CRC가 다릅니다.')
    source_size,cursor=read_number(patch,4);target_size,cursor=read_number(patch,cursor)
    metadata_size,cursor=read_number(patch,cursor);cursor+=metadata_size
    if len(source)!=source_size or target_size>64*1024*1024:raise ValueError('지원하지 않는 롬 크기입니다.')
    target=bytearray();source_relative=0;target_relative=0
    while len(target)<target_size:
        action,cursor=read_number(patch,cursor);count=(action>>2)+1;kind=action&3
        if len(target)+count>target_size:raise ValueError('BPS 출력 범위를 벗어났습니다.')
        if kind==0:
            data=source[len(target):len(target)+count]
            if len(data)!=count:raise ValueError('BPS 원본 범위를 벗어났습니다.')
            target.extend(data)
        elif kind==1:
            if cursor+count>len(patch)-12:raise ValueError('BPS 리터럴이 잘렸습니다.')
            target.extend(patch[cursor:cursor+count]);cursor+=count
        else:
            delta,cursor=read_number(patch,cursor);delta=-(delta>>1) if delta&1 else delta>>1
            if kind==2:
                source_relative+=delta
                if not 0<=source_relative<=len(source)-count:raise ValueError('BPS 원본 복사 범위를 벗어났습니다.')
                target.extend(source[source_relative:source_relative+count]);source_relative+=count
            else:
                target_relative+=delta
                if not 0<=target_relative<len(target):raise ValueError('BPS 출력 복사 범위를 벗어났습니다.')
                for _ in range(count):target.append(target[target_relative]);target_relative+=1
    if cursor!=len(patch)-12 or zlib.crc32(target)!=target_crc:raise ValueError('BPS 출력 검증에 실패했습니다.')
    return bytes(target)
