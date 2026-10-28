"""Assemble reviewed public release files without any ROM input in the archives."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import sys
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from patcher_core import VERSION,SOURCE_SHA1,SOURCE_SHA256,TARGET_SHA256

ROOT=Path(__file__).resolve().parents[1]
REPO='OldManCraveGuitars-bit/N64-Akumajou-Dracula-Mokushiroku-Real-Action-Adventure-Kr'
WEB='https://github.com/'+REPO
BASE=WEB+'/releases/download/v'+VERSION+'/'
RAW='https://raw.githubusercontent.com/'+REPO+'/v'+VERSION+'/'

def read(path):return json.loads(path.read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def archive(path,files):
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as zipped:
        for name,payload in files:
            info=zipfile.ZipInfo(name,(2026,10,29,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            zipped.writestr(info,payload,compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
    with zipfile.ZipFile(path) as zipped:
        assert zipped.testzip() is None
        assert not any(n.lower().endswith(('.z64','.v64','.n64')) or '/work/' in n for n in zipped.namelist())

def main():
    parser=argparse.ArgumentParser();parser.add_argument('project',type=Path);args=parser.parse_args()
    private=args.project;dist=ROOT/'dist';manifest=read(ROOT/'data/manifest.json')
    frozen=read(dist/'patcher-verification.json');assert frozen['all_passed']
    exe=dist/f'N64-Akumajou-Dracula-Mokushiroku-Kr-v{VERSION}-Patcher.exe'
    assert sha(exe)==frozen['executable_sha256']
    assert sha(ROOT/'.qa/editor/work/korean-candidate-v014.z64')==TARGET_SHA256
    build=read(private/'analysis/release-audit.json');assert build['sha256']==TARGET_SHA256
    suite=read(private/'qa/v065-final/summary.json')
    assert suite['all_passed'] and suite['rom_sha256']==TARGET_SHA256
    runtime=suite['cases']
    assert len(runtime)>=12 and all(r['rom_sha256']==TARGET_SHA256 and not r['native_fault'] for r in runtime)
    banners=read(private/'qa/v065-final/banners/results.json')
    assert len(banners)==13 and all(r['passed'] for r in banners)
    review=read(private/'analysis/review-v065.json')
    assert review['all_unique_pairs_reviewed'] and review['reviewed_unique_sources']==934
    coverage=read(private/'analysis/coverage-audit.json')
    verification=dict(version=VERSION,source_sha1=SOURCE_SHA1,source_normalized_sha256=SOURCE_SHA256,
        source_provided_v64_sha256='078ac90a17f6fad57300a95fff7d4a9c34bc1d981009ba965bd637df84a9f2eb',
        target_sha256=TARGET_SHA256,patch_sha256=manifest['patch_sha256'],
        executable_sha256=sha(exe),patcher=frozen,editor_rebuilt_same_target=True,
        translated_segments=1071,japanese_segments=1067,localized_character_name_entries=4,
        untranslated_catalog_segments=0,reviewed_unique_sources=934,
        proofreading_corrected_segments=40,assets_validated=254,map_text_pointers_validated=28,
        latin_font_pixels_preserved=True,english_title_pixels_preserved=True,audio_bytes_preserved=True,
        space='U+0020',space_width_pixels=8,checksum='N64 CIC-6102 verified',runtime=runtime,
        stage_banner_regression=banners,save_load=suite['save_load'],review_v065=review,
        character_selection_names_centered=True,character_selection_names_y=174,pause_character_name_scale=1.0,
        coverage_candidate_review=coverage['candidate_review'],texture_review=coverage['texture_review'],
        limitations=['모든 플레이 분기를 처음부터 끝까지 완주한 검증은 아닙니다.',
                     '일부 저해상도 배경 글씨는 완전히 판독하지 못했습니다.',
                     '텍스처 검사는 모든 이미지 형식을 전수 조사한 것은 아닙니다.'])
    (ROOT/'docs/validation.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    shutil.copy2(private/'analysis/proofread-2026-10-23.json',ROOT/'docs/proofreading.json')
    shutil.copy2(private/'analysis/review-v065.json',ROOT/f'docs/review-v{VERSION}.json')
    shutil.copy2(ROOT/'data'/manifest['patch_file'],dist/manifest['patch_file'])
    guide=f'''악마성 드라큘라 묵시록 N64 일본판 한국어 패치 v{VERSION}

Windows 10/11 x64에서 패처 EXE를 실행하고 일본판 원본 롬을 선택하세요.
출력 경로를 고른 뒤 '한글 패치 적용'을 누릅니다. Python 설치는 필요하지 않습니다.
원본은 보존하며, 기존 출력 파일이 있으면 새 이름을 선택해야 합니다.
.z64/.v64/.n64 파일의 실제 바이트 순서를 자동 판별합니다.
일반 BPS 프로그램에서는 big endian .z64 원본에 적용하세요.

지원 원본 크기: 12 MiB / 결과 크기: 16 MiB
원본 정규화 SHA1: {SOURCE_SHA1}
원본 정규화 SHA256: {SOURCE_SHA256}
결과 SHA256: {TARGET_SHA256}
EXE SHA256: {sha(exe)}
BPS SHA256: {manifest['patch_sha256']}

일본어 텍스트 1,067구간, 일본어 타이틀 로고, 기존 컷신 자막을 한국어로 바꿨습니다.
캐릭터 이름은 한글화하며, 그 외 영어 메뉴, 영문 부제, 영어 음성을 유지합니다. 띄어쓰기는 반각 공백(8픽셀)입니다.
한글 검수에서 40구간을 수정했습니다. 기존 자막 표시 명령과 타이밍을 보존했습니다.

완성된 한글 롬을 새로 부팅하고, 게임 안에서 저장 데이터를 불러오세요.
원본이나 이전 롬의 에뮬레이터 빠른 저장 상태 대신 게임의 저장 기능을 사용하세요.
새 부팅, 오프닝, 아이템, 실제 저장·새 부팅 불러오기, 엔딩 화면을 확인했습니다.
모든 분기 완주와 일부 저해상도 배경 글씨는 검증을 마치지 않았습니다.

v0.65 수정: 종료 확인 문구를 '종료할까요?'로 줄여 창 이탈을 고쳤습니다.
파일 처리 확인 문구는 '진행할까요?'로 바로잡았습니다.
캐릭터 이름을 공통 메뉴 테이블에서 한글화하여 선택/일시정지 메뉴에 적용했습니다.
캐릭터 선택 이름은 초상화 아래 가운데에 맞추고 기존보다 4픽셀 아래에 배치했습니다.
일시정지 메뉴 이름은 0.9배 축소를 없애 한글 획이 뭉개지는 문제를 수정했습니다.
전체 934개 원문(중복 포함 1,071구간)을 다시 대조했고, 저장 오류 안내도 다듬었습니다.
지역명 13개 한 줄 표시와 원본 표시 시간 보존 수정도 포함합니다.
일본판 원본 롬에 새 패치를 적용하세요.

텍스트 도구는 별도 Text-Tool-v{VERSION}.zip으로 제공됩니다.
도구에는 Python 3.11 이상과 Pillow가 필요하며, 첫 실행에서 원본 롬을 선택합니다.
검수 전후 내용은 저장소 docs/proofreading.json, 검증 결과는 docs/validation.json에 있습니다.

저장소: {WEB}
'''
    (dist/'사용설명.txt').write_text(guide,encoding='utf-8-sig')
    patcher_zip=dist/f'N64-Akumajou-Dracula-Mokushiroku-Kr-v{VERSION}-Windows.zip'
    inner_sums='\n'.join(sha(p)+'  '+p.name for p in [exe,dist/manifest['patch_file']])+'\n'
    archive(patcher_zip,[(exe.name,exe.read_bytes()),(manifest['patch_file'],(dist/manifest['patch_file']).read_bytes()),
                         ('사용설명.txt',guide.encode('utf-8-sig')),('SHA256SUMS.txt',inner_sums.encode())])
    editor_zip=dist/f'Text-Tool-v{VERSION}.zip'
    editor_files=[p for p in (ROOT/'text-tool').rglob('*') if p.is_file() and '__pycache__' not in p.parts and 'work' not in p.relative_to(ROOT/'text-tool').parts]
    archive(editor_zip,[('Text-Tool/'+str(p.relative_to(ROOT/'text-tool')).replace('\\','/'),p.read_bytes()) for p in sorted(editor_files)])
    screenshots_zip=dist/f'Screenshots-v{VERSION}.zip'
    archive(screenshots_zip,[(p.name,p.read_bytes()) for p in sorted((ROOT/'docs/screenshots').glob('*.png'))])
    shutil.copy2(ROOT/'docs/validation.json',dist/f'verification-v{VERSION}.json')
    assets=[exe,dist/manifest['patch_file'],patcher_zip,editor_zip,screenshots_zip,dist/f'verification-v{VERSION}.json']
    sums=''.join(sha(p)+'  '+p.name+'\n' for p in assets)
    (ROOT/'SHA256SUMS.txt').write_text(sums,encoding='ascii');(dist/'SHA256SUMS.txt').write_text(sums,encoding='ascii')
    hash_table='| 대상 | SHA256 |\n| --- | --- |\n'+''.join('| '+name+' | `'+digest+'` |\n' for name,digest in [
        ('원본 .z64 (바이트 순서 정규화)',SOURCE_SHA256),
        ('원본 .v64 (제공된 파일)',verification['source_provided_v64_sha256']),
        ('패치 결과 .z64',TARGET_SHA256),('Windows EXE',sha(exe)),('BPS 패치',manifest['patch_sha256']),('Windows ZIP',sha(patcher_zip))])
    intro=f'''**악마성 드라큘라 묵시록 · N64 일본판 한국어 패치 v{VERSION}**

**v0.65 수정 사항**

- 종료 확인을 **종료할까요?**로 줄여 창 안에 표시합니다. 파일 처리 확인의 잘못된 '사용할까요?'도 **진행할까요?**로 고쳤습니다.
- 캐릭터 이름을 공통 메뉴 문자열에서 한글화해 선택 화면과 일시정지 메뉴에 적용했습니다. 다른 영어 메뉴·부제·음성은 유지합니다.
- 선택 화면 이름을 초상화 아래 가운데에 맞추고 **4픽셀 아래로** 내렸습니다.
- 일시정지 메뉴 이름의 **0.9배 축소를 1배**로 바꾸어 한글 획이 뭉개지는 표시를 수정했습니다.
- 전체 원문 **934개, 중복 포함 1,071구간**을 다시 대조했습니다. 저장 공간·메모 칸 부족 안내도 고쳤습니다.
- v0.6.1의 지역명 13개 한 줄 표시 수정을 포함합니다. 원본 표시 시간은 유지합니다.

일본어 텍스트 1,067구간과 일본어 로고를 한국어로 바꿨으며, 이번 판에는 공통 이름 4개 항목도 한글화했습니다(미사용 이름 2개 포함). 컷신은 게임 엔진의 기존 자막 명령과 타이밍을 유지합니다. 띄어쓰기는 U+0020 반각 공백이며 게임 안에서는 8픽셀입니다.

**일본판 원본에 다시 패치하고 새로 부팅해 주세요.** 게임 안의 저장 기능으로 이어 할 수 있습니다.
'''
    downloads=f'''Windows 10/11 x64에서는 [EXE 패처]({BASE+exe.name}) 또는 [Windows ZIP]({BASE+patcher_zip.name})을 받으세요. Python 설치 없이 실행합니다. [BPS 단독 패치]({BASE+manifest['patch_file']}), [텍스트 도구]({BASE+editor_zip.name}), [스크린샷 모음]({BASE+screenshots_zip.name}), [SHA256 목록]({BASE+'SHA256SUMS.txt'})도 제공합니다.

1. 패처 EXE를 실행하고 일본판 원본 롬을 선택합니다.
2. 새 출력 파일 경로를 고르고 **한글 패치 적용**을 누릅니다.
3. 완료 후 표시된 결과 SHA256을 확인합니다.
4. 만들어진 .z64 롬을 새로 부팅하고 게임 안의 저장 데이터를 불러옵니다.

원본 크기는 **12 MiB**, 패치 결과는 **16 MiB**입니다. .z64/.v64/.n64의 바이트 순서를 자동 판별하며 원본을 보존합니다. 기존 출력 파일이 있으면 새 이름을 선택하세요. 일반 BPS 프로그램은 big endian .z64 원본에 적용합니다.

원본 정규화 **SHA1**: `{SOURCE_SHA1}`

'''
    validation='''실제 EXE로 세 가지 바이트 순서의 원본을 패치해 같은 결과 해시를 확인했습니다. 잘못된 원본·손상된 패치·원본 및 기존 출력 덮어쓰기 차단, GUI 시작, 텍스트 도구의 동일 결과 재빌드도 검사했습니다.

254개 자산과 28개 맵 문구 포인터, 번역 폭·페이지·참조·N64 체크섬을 검사했습니다. 최종 빌드에서 두 캐릭터 새 부팅과 선택 화면, 오프닝, 종료의 예/아니요, 두 캐릭터 아이템 메뉴, 실제 저장과 새 부팅 불러오기, 엔딩과 수정 컷신을 실행했습니다. 지역명 13개도 실행해 자동 스크롤 없이 한 줄로 표시되고 원본의 표시 시간을 유지하는지 확인했습니다.

앞선 빌드에서 검사한 두 주인공 × 27개 지역 로딩, 컷신 54개 진입 조건, 문구 누락·텍스처 검수 기록도 보존합니다. **모든 분기를 처음부터 끝까지 완주한 검증은 아닙니다. 일부 저해상도 배경 글씨와 모든 이미지 형식의 전수 확인은 마치지 않았습니다.**
'''
    def pictures(prefix):
        return '\n'.join('<p><img src="'+prefix+name+'" width="640" height="480" alt="'+label+'"></p>\n\n'+label+'\n'
                         for name,label in [('07-character-select.png','초상화 아래 가운데 정렬 및 위치 조정'),('08-exit-confirm.png','종료할까요? / 일시정지 메뉴의 한글 이름'),('09-carrie-menu.png','캐리 일시정지 메뉴'),('06-forest-banner.png','한 줄로 표시되는 침묵의 숲'),('02-opening.png','오프닝 한글 자막'),('03-dialogue.png','캐리 대사'),('04-save.png','화이트 주얼 저장창'),('05-inventory.png','아이템 메뉴')])
    title='<p align="center"><img src="docs/screenshots/01-title.png" width="640" height="480" alt="한글 타이틀 화면"></p>\n\n'
    source_notes='''텍스트 도구는 `text-tool/텍스트_도구_실행.cmd`로 실행합니다. Python 3.11 이상과 Pillow가 필요하며, 첫 실행에서 원본을 선택합니다. 원문·번역·ID 검색, 실제 글꼴 미리보기, Ctrl+S 저장, 폭/영문 보존 검증, 롬 빌드를 지원합니다.

패처 소스 실행: `python patcher_app.py`

EXE 빌드: `python -m pip install -r requirements-build.txt` 후 `scripts/build_exe.ps1`을 실행합니다. 게임 원본과 완성 롬은 배포 파일에 포함되지 않습니다. 게임의 권리는 원 권리자에게 있습니다.

분해 구조 참고: [k64ret/cv64](https://github.com/k64ret/cv64). 이번 재검수 기록은 [docs/review-v0.65.json](docs/review-v0.65.json), 이전 검수 기록은 [docs/proofreading.json](docs/proofreading.json), 검증 기록은 [docs/validation.json](docs/validation.json)에 있습니다.
'''
    (ROOT/'README.md').write_text(title+intro+'\n'+downloads+hash_table+'\n'+validation+'\n'+pictures('docs/screenshots/')+'\n'+source_notes,encoding='utf-8')
    release_title=title.replace('docs/screenshots/01-title.png',RAW+'docs/screenshots/01-title.png')
    (ROOT/f'docs/release-v{VERSION}.md').write_text(release_title+intro+'\n'+downloads+hash_table+'\n'+validation+'\n'+pictures(RAW+'docs/screenshots/'),encoding='utf-8')
    (dist/'release-assets.json').write_text(json.dumps([p.name for p in assets]+['SHA256SUMS.txt'],indent=2),encoding='utf-8')
    print(json.dumps(dict(version=VERSION,assets=[dict(name=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in assets]),indent=2))

if __name__=='__main__':main()
