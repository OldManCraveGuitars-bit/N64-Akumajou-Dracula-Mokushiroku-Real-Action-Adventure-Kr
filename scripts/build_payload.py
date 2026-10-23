"""Create a versioned BPS payload from separately supplied local ROM files."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bps import create, apply
from patcher_core import VERSION, SOURCE_SHA1, SOURCE_SHA256, TARGET_SHA256, normalize, sha256

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('original',type=Path)
    parser.add_argument('translated',type=Path)
    args=parser.parse_args()
    source=normalize(args.original.read_bytes());target=args.translated.read_bytes()
    assert hashlib.sha1(source).hexdigest()==SOURCE_SHA1 and sha256(source)==SOURCE_SHA256
    assert sha256(target)==TARGET_SHA256
    folder=Path(__file__).resolve().parents[1]/'data'
    patch_name=f'Akumajou-Dracula-Mokushiroku-Korean-v{VERSION}.bps'
    metadata=json.dumps(dict(game='Castlevania 64 Japan',version=VERSION,language='Korean',
                             english='preserved',target_sha256=TARGET_SHA256),sort_keys=True).encode()
    patch=create(source,target,metadata)
    assert apply(source,patch)==target
    (folder/patch_name).write_bytes(patch)
    manifest=dict(version=VERSION,patch_file=patch_name,patch_sha256=sha256(patch),patch_bytes=len(patch),
                  source_sha1=SOURCE_SHA1,source_sha256=SOURCE_SHA256,source_bytes=len(source),
                  target_sha256=TARGET_SHA256,target_bytes=len(target))
    (folder/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(manifest,indent=2))

if __name__=='__main__':main()
