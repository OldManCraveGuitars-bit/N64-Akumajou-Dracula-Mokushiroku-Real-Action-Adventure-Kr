"""Exercise the actual frozen executable, including failure paths."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from patcher_core import normalize, TARGET_SHA256, VERSION

def main():
    parser=argparse.ArgumentParser();parser.add_argument('original',type=Path);args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    exe=root/'dist/N64-Akumajou-Dracula-Mokushiroku-Kr-v0.6-Patcher.exe'
    original=args.original.read_bytes();normalized=normalize(original);checks=[]
    with tempfile.TemporaryDirectory(prefix='cv64-frozen-check-') as temporary:
        folder=Path(temporary)
        def run(name,arguments,expected=True):
            report=folder/(name+'.json')
            result=subprocess.run([str(exe),*map(str,arguments),'--report',str(report)],timeout=90,
                                  creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            data=json.loads(report.read_text(encoding='utf-8'))
            assert data['success']==expected and (result.returncode==0)==expected,(name,result.returncode,data)
            checks.append(dict(name=name,passed=True))
            return data
        run('embedded_payload',['--self-test'])
        run('gui_initialization',['--gui-self-check'])
        for width in [1,2,4]:
            raw=bytearray(len(normalized))
            for i in range(width):raw[i::width]=normalized[width-1-i::width]
            source=folder/f'원본 {width}.rom';source.write_bytes(raw)
            output=folder/f'한글 {width}.z64'
            data=run(f'byte_order_{width}',['--apply',source,'--output',output])
            assert hashlib.sha256(output.read_bytes()).hexdigest()==TARGET_SHA256
            assert source.read_bytes()==raw and data['original_preserved']
        wrong=folder/'wrong.z64';damaged=bytearray(normalized);damaged[0x200]^=1;wrong.write_bytes(damaged)
        rejected=folder/'rejected.z64'
        run('wrong_source_rejected',['--apply',wrong,'--output',rejected],False)
        assert not rejected.exists()
        run('original_overwrite_rejected',['--apply',args.original,'--output',args.original],False)
        existing=folder/'existing.z64';existing.write_bytes(b'preserve existing output')
        run('existing_output_preserved',['--apply',args.original,'--output',existing],False)
        assert existing.read_bytes()==b'preserve existing output'
    assert args.original.read_bytes()==original
    result=dict(version=VERSION,all_passed=True,checks=checks,source_original_preserved=True,
                target_sha256=TARGET_SHA256,executable_sha256=hashlib.sha256(exe.read_bytes()).hexdigest(),
                frozen_executable_tested=True)
    (root/'dist/patcher-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
