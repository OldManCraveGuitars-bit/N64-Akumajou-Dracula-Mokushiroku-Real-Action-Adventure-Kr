"""Apply a Korean BPS patch to a verified Japanese ROM in any N64 byte order."""
import argparse,hashlib
from pathlib import Path
from bps import apply
from prepare_project import normalize,EXPECTED

def main():
    parser=argparse.ArgumentParser(description='악마성 64 일본판 한글 패치 적용')
    parser.add_argument('original',type=Path);parser.add_argument('patch',type=Path)
    parser.add_argument('output',type=Path,nargs='?');args=parser.parse_args()
    output=args.output or args.original.with_name(args.original.stem+' (Korean).z64')
    if output.resolve()==args.original.resolve():raise ValueError('원본 파일을 덮어쓸 수 없습니다.')
    source=normalize(args.original.read_bytes())
    if hashlib.sha1(source).hexdigest()!=EXPECTED:raise ValueError('지원하는 일본판 원본 롬이 아닙니다.')
    result=apply(source,args.patch.read_bytes());output.parent.mkdir(parents=True,exist_ok=True)
    output.write_bytes(result)
    print('한글 롬:',output.resolve())
    print('SHA256:',hashlib.sha256(result).hexdigest())

if __name__=='__main__':main()
