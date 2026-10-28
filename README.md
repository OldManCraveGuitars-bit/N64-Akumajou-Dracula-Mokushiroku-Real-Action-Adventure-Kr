<p align="center"><img src="docs/screenshots/01-title.png" width="640" height="480" alt="한글 타이틀 화면"></p>

**악마성 드라큘라 묵시록 · N64 일본판 한국어 패치 v0.6.1**

**v0.6.1 수정:** 첫 지역명 '침묵의 숲'이 두 화면으로 나뉘던 표시 오류를 고쳤습니다. 지역명 13개 모두 실제 한글 폭에 맞춰 한 줄로 표시하며, 원본의 표시 시간은 유지합니다. 오프닝 전체 진행과 13개 지역명 실행에서 자동 스크롤이 사라진 것을 확인했습니다. 일본판 원본에 다시 패치해 주세요.

일본어 텍스트 1,067구간과 일본어 로고를 한국어로 바꿨습니다. 컷신은 게임 엔진의 기존 자막 표시·대기 명령과 타이밍을 유지해 한국어로 표시합니다. 영어 메뉴·영문 부제·영어 음성은 보존합니다. 띄어쓰기는 U+0020 반각 공백이며 게임 안에서는 8픽셀입니다.

원문 930개(중복 포함 1,067구간)를 대조했고, 관용구 오역·조사·말더듬·점프 경고·지역명 등을 40구간 수정했습니다.

Windows 10/11 x64에서는 [EXE 패처](https://github.com/OldManCraveGuitars-bit/N64-Akumajou-Dracula-Mokushiroku-Real-Action-Adventure-Kr/releases/download/v0.6.1/N64-Akumajou-Dracula-Mokushiroku-Kr-v0.6.1-Patcher.exe) 또는 [Windows ZIP](https://github.com/OldManCraveGuitars-bit/N64-Akumajou-Dracula-Mokushiroku-Real-Action-Adventure-Kr/releases/download/v0.6.1/N64-Akumajou-Dracula-Mokushiroku-Kr-v0.6.1-Windows.zip)을 받으세요. Python 설치 없이 실행합니다. [BPS 단독 패치](https://github.com/OldManCraveGuitars-bit/N64-Akumajou-Dracula-Mokushiroku-Real-Action-Adventure-Kr/releases/download/v0.6.1/Akumajou-Dracula-Mokushiroku-Korean-v0.6.1.bps), [텍스트 도구](https://github.com/OldManCraveGuitars-bit/N64-Akumajou-Dracula-Mokushiroku-Real-Action-Adventure-Kr/releases/download/v0.6.1/Text-Tool-v0.6.1.zip), [스크린샷 모음](https://github.com/OldManCraveGuitars-bit/N64-Akumajou-Dracula-Mokushiroku-Real-Action-Adventure-Kr/releases/download/v0.6.1/Screenshots-v0.6.1.zip), [SHA256 목록](https://github.com/OldManCraveGuitars-bit/N64-Akumajou-Dracula-Mokushiroku-Real-Action-Adventure-Kr/releases/download/v0.6.1/SHA256SUMS.txt)도 제공합니다.

1. 패처 EXE를 실행하고 일본판 원본 롬을 선택합니다.
2. 새 출력 파일 경로를 고르고 **한글 패치 적용**을 누릅니다.
3. 완료 후 표시된 결과 SHA256을 확인합니다.
4. 만들어진 .z64 롬을 새로 부팅하고 게임 안의 저장 데이터를 불러옵니다.

원본 크기는 **12 MiB**, 패치 결과는 **16 MiB**입니다. .z64/.v64/.n64의 바이트 순서를 자동 판별하며 원본을 보존합니다. 기존 출력 파일이 있으면 새 이름을 선택하세요. 일반 BPS 프로그램은 big endian .z64 원본에 적용합니다.

원본 정규화 **SHA1**: `aa70348968589e6ba6e7091ca115fb505099cd97`

| 대상 | SHA256 |
| --- | --- |
| 원본 .z64 (바이트 순서 정규화) | `f5b8a1bd8dd4d03b5fe291428b284ca30d9afd300fe25f60317aa1e4590db638` |
| 원본 .v64 (제공된 파일) | `078ac90a17f6fad57300a95fff7d4a9c34bc1d981009ba965bd637df84a9f2eb` |
| 패치 결과 .z64 | `9fcc7bb34de13ad953ebb6b48d1e9b6b0236f74ba0c70c048c50423d88419fdd` |
| Windows EXE | `f1bb078ce11a7e71633c7f056c9f28283f695e98a9f8f75e5279d12a3379bbac` |
| BPS 패치 | `e605e29409e3709c3797469e64e85a62f9c9d29919a5b6f8032a7aeae355bd6a` |
| Windows ZIP | `738cb2fad9f89182c5b66c5c6ca3b72ef9a97c8492904a9590747cff743850c1` |

EXE의 실제 패치 실행을 세 가지 바이트 순서로 시험해 같은 결과 해시를 확인했습니다. 잘못된 원본·손상된 패치·원본 및 기존 출력 덮어쓰기를 차단하는 검사, GUI 시작, 텍스트 도구의 동일 결과 재빌드를 통과했습니다.

254개 자산과 28개 맵 문구 포인터, 폭·페이지·참조·N64 체크섬을 검사했습니다. v0.6에서 새 부팅, 오프닝 자막, 캐리 아이템 메뉴, 실제 저장과 새 부팅 불러오기, 엔딩 뒤 저장창, 수정 컷신을 확인했습니다. v0.6.1은 지역명 표시 폭 테이블만 바뀌었고 다른 253개 해제 자산은 동일합니다. 수정판은 오프닝을 건너뛰지 않은 새 부팅과 지역명 13개를 추가 실행 검증했습니다. 앞선 빌드에서는 두 주인공 × 27개 지역 로딩 및 컷신 54개 진입 조건을 시험했습니다.

**확인한 범위에서 추가 일본어 누락은 찾지 못했습니다. 모든 플레이 분기를 처음부터 끝까지 완주한 검증은 아니며, 일부 저해상도 배경 글씨와 모든 이미지 형식의 전수 확인은 마치지 않았습니다.**

<p><img src="docs/screenshots/06-forest-banner.png" width="640" height="480" alt="v0.6.1: 한 줄로 표시되는 침묵의 숲"></p>

v0.6.1: 한 줄로 표시되는 침묵의 숲

<p><img src="docs/screenshots/02-opening.png" width="640" height="480" alt="오프닝 한글 자막"></p>

오프닝 한글 자막

<p><img src="docs/screenshots/03-dialogue.png" width="640" height="480" alt="캐리 대사"></p>

캐리 대사

<p><img src="docs/screenshots/04-save.png" width="640" height="480" alt="화이트 주얼 저장창"></p>

화이트 주얼 저장창

<p><img src="docs/screenshots/05-inventory.png" width="640" height="480" alt="아이템 메뉴"></p>

아이템 메뉴

텍스트 도구는 `text-tool/텍스트_도구_실행.cmd`로 실행합니다. Python 3.11 이상과 Pillow가 필요하며, 첫 실행에서 원본을 선택합니다. 원문·번역·ID 검색, 실제 글꼴 미리보기, Ctrl+S 저장, 폭/영문 보존 검증, 롬 빌드를 지원합니다.

패처 소스 실행: `python patcher_app.py`

EXE 빌드: `python -m pip install -r requirements-build.txt` 후 `scripts/build_exe.ps1`을 실행합니다. 게임 원본과 완성 롬은 배포 파일에 포함되지 않습니다. 게임의 권리는 원 권리자에게 있습니다.

분해 구조 참고: [k64ret/cv64](https://github.com/k64ret/cv64). 검수 기록은 [docs/proofreading.json](docs/proofreading.json), 검증 기록은 [docs/validation.json](docs/validation.json)에 있습니다.
