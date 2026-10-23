"""Prepare reproducible build inputs from the user's original ROM."""
import hashlib
from pathlib import Path
import sys
from text_codec import ROOT

EXPECTED='aa70348968589e6ba6e7091ca115fb505099cd97'

def normalize(data):
    if data[:4]==bytes.fromhex('80371240'):return data
    size=2 if data[:4]==bytes.fromhex('37804012') else 4 if data[:4]==bytes.fromhex('40123780') else 0
    if not size:raise ValueError('N64 롬의 바이트 순서를 확인할 수 없습니다.')
    if len(data)%size:raise ValueError('잘못된 롬 크기입니다.')
    out=bytearray(len(data))
    for i in range(size):out[i::size]=data[size-1-i::size]
    return bytes(out)

def prepare(path):
    source=Path(path).resolve();data=normalize(source.read_bytes())
    if hashlib.sha1(data).hexdigest()!=EXPECTED:raise ValueError('지원하는 일본판 원본 롬과 해시가 다릅니다.')
    work=ROOT/'work';work.mkdir(exist_ok=True)
    target=work/'original.z64'
    if target.resolve()==source:print('검증된 원본 작업 사본을 사용합니다.')
    else:target.write_bytes(data)
    from extract_rom import extract
    extract()
    print('원본은 보존했습니다. 텍스트 도구와 빌드를 사용할 수 있습니다.')

if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('사용법: python tools/prepare_project.py 원본롬경로')
    prepare(sys.argv[1])
