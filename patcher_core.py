"""Validated standalone BPS application. Original files are never overwritten."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
from typing import Callable
from bps import apply as apply_bps

VERSION = '0.6.1'
SOURCE_SHA1 = 'aa70348968589e6ba6e7091ca115fb505099cd97'
SOURCE_SHA256 = 'f5b8a1bd8dd4d03b5fe291428b284ca30d9afd300fe25f60317aa1e4590db638'
TARGET_SHA256 = '9fcc7bb34de13ad953ebb6b48d1e9b6b0236f74ba0c70c048c50423d88419fdd'
OUTPUT_NAME = f'Akumajou Dracula Mokushiroku (Japan) (Korean v{VERSION}).z64'

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def normalize(data: bytes) -> bytes:
    if data[:4] == bytes.fromhex('80371240'):
        return data
    width = 2 if data[:4] == bytes.fromhex('37804012') else 4 if data[:4] == bytes.fromhex('40123780') else 0
    if not width or len(data) % width:
        raise ValueError('N64 원본 롬의 형식이 올바르지 않습니다.')
    output = bytearray(len(data))
    for i in range(width):
        output[i::width] = data[width - i - 1::width]
    return bytes(output)

def load_bundle(folder: Path) -> tuple[bytes, dict]:
    manifest = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
    if manifest['version'] != VERSION or manifest['source_sha1'] != SOURCE_SHA1 or manifest['target_sha256'] != TARGET_SHA256:
        raise ValueError('패처의 버전 또는 내장 파일 정보가 올바르지 않습니다.')
    patch = (folder / manifest['patch_file']).read_bytes()
    if sha256(patch) != manifest['patch_sha256']:
        raise ValueError('내장 패치 파일의 SHA256이 다릅니다.')
    return patch, manifest

def patch_file(source_path: Path, output_path: Path, bundle: Path,
               progress: Callable[[int, str], None] | None = None) -> dict:
    source_path = Path(source_path).resolve()
    output_path = Path(output_path).resolve()
    tell = progress or (lambda value, message: None)
    if source_path == output_path or (output_path.exists() and os.path.samefile(source_path, output_path)):
        raise ValueError('원본 롬을 덮어쓸 수 없습니다. 다른 출력 경로를 선택하세요.')
    if output_path.exists():
        raise FileExistsError('출력 파일이 이미 있습니다. 새 파일 이름을 선택하세요.')
    if not source_path.is_file():
        raise ValueError('원본 롬 파일을 선택하세요.')
    if source_path.stat().st_size != 12 * 1024 * 1024:
        raise ValueError('지원하는 일본판 원본은 12 MiB입니다. 다른 파일 또는 이전 패치본을 선택했습니다.')
    tell(10, '원본 형식과 해시를 확인합니다.')
    raw = source_path.read_bytes()
    source = normalize(raw)
    if hashlib.sha1(source).hexdigest() != SOURCE_SHA1 or sha256(source) != SOURCE_SHA256:
        raise ValueError('지원하는 일본판 원본과 해시가 다릅니다. 원본 롬을 확인하세요.')
    tell(30, '원본 검증 완료. 내장 BPS 패치를 적용합니다.')
    patch, manifest = load_bundle(bundle)
    target = apply_bps(source, patch)
    if sha256(target) != TARGET_SHA256:
        raise ValueError('출력 롬의 SHA256 검증에 실패했습니다.')
    tell(85, '결과 검증 완료. 새 한글 롬을 저장합니다.')
    # Exclusive creation also protects files created after the earlier check.
    output_path.parent.mkdir(parents=True, exist_ok=True)
    created = False
    try:
        with output_path.open('xb') as stream:
            created = True
            stream.write(target)
            stream.flush()
            os.fsync(stream.fileno())
        if sha256(output_path.read_bytes()) != TARGET_SHA256:
            raise OSError('디스크에 기록한 파일의 SHA256이 다릅니다.')
    except BaseException:
        if created:
            output_path.unlink(missing_ok=True)
        raise
    tell(100, '한글 패치 적용을 마쳤습니다.')
    return dict(version=VERSION, source=str(source_path), output=str(output_path),
                source_raw_sha256=sha256(raw), source_normalized_sha1=SOURCE_SHA1,
                source_normalized_sha256=SOURCE_SHA256, target_sha256=TARGET_SHA256,
                patch_sha256=manifest['patch_sha256'], output_bytes=len(target), original_preserved=True)
