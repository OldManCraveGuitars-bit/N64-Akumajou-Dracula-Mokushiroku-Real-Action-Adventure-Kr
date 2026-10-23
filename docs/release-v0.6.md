<p align="center"><img src="https://raw.githubusercontent.com/OldManCraveGuitars-bit/N64-Akumajou-Dracula-Mokushiroku-Real-Action-Adventure-Kr/v0.6/docs/screenshots/01-title.png" width="640" height="480" alt="한글 타이틀 화면"></p>

**악마성 드라큘라 묵시록 · N64 일본판 한국어 패치 v0.6**

일본어 텍스트 1,067구간과 일본어 로고를 한국어로 바꿨습니다. 컷신은 게임 엔진의 기존 자막 표시·대기 명령과 타이밍을 유지해 한국어로 표시합니다. 영어 메뉴·영문 부제·영어 음성은 보존합니다. 띄어쓰기는 U+0020 반각 공백이며 게임 안에서는 8픽셀입니다.

원문 930개(중복 포함 1,067구간)를 대조했고, 관용구 오역·조사·말더듬·점프 경고·지역명 등을 40구간 수정했습니다.

Windows 10/11 x64에서는 [EXE 패처](https://github.com/OldManCraveGuitars-bit/N64-Akumajou-Dracula-Mokushiroku-Real-Action-Adventure-Kr/releases/download/v0.6/N64-Akumajou-Dracula-Mokushiroku-Kr-v0.6-Patcher.exe) 또는 [Windows ZIP](https://github.com/OldManCraveGuitars-bit/N64-Akumajou-Dracula-Mokushiroku-Real-Action-Adventure-Kr/releases/download/v0.6/N64-Akumajou-Dracula-Mokushiroku-Kr-v0.6-Windows.zip)을 받으세요. Python 설치 없이 실행합니다. [BPS 단독 패치](https://github.com/OldManCraveGuitars-bit/N64-Akumajou-Dracula-Mokushiroku-Real-Action-Adventure-Kr/releases/download/v0.6/Akumajou-Dracula-Mokushiroku-Korean-v0.6.bps), [텍스트 도구](https://github.com/OldManCraveGuitars-bit/N64-Akumajou-Dracula-Mokushiroku-Real-Action-Adventure-Kr/releases/download/v0.6/Text-Tool-v0.6.zip), [스크린샷 모음](https://github.com/OldManCraveGuitars-bit/N64-Akumajou-Dracula-Mokushiroku-Real-Action-Adventure-Kr/releases/download/v0.6/Screenshots-v0.6.zip), [SHA256 목록](https://github.com/OldManCraveGuitars-bit/N64-Akumajou-Dracula-Mokushiroku-Real-Action-Adventure-Kr/releases/download/v0.6/SHA256SUMS.txt)도 제공합니다.

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
| 패치 결과 .z64 | `ad2a0edc13d547385f4b234bcd740f448405acfabad95f0c251d822d88686e89` |
| Windows EXE | `b3cd72378da56d64203514d1ed7b3b989d167801cbe493b18f928feaf284fdf5` |
| BPS 패치 | `bd02ecff7a716a2adde077f2741cfbdbf89ca4a8d7e79252066d2ad37b428af7` |
| Windows ZIP | `e67df5916e7378b55a4a919979d5b101459e12e89796b71d6f89fb4719dfb83b` |

EXE의 실제 패치 실행을 세 가지 바이트 순서로 시험해 같은 결과 해시를 확인했습니다. 잘못된 원본·손상된 패치·원본 및 기존 출력 덮어쓰기를 차단하는 검사, GUI 시작, 텍스트 도구의 동일 결과 재빌드를 통과했습니다.

254개 자산과 28개 맵 문구 포인터, 폭·페이지·참조·N64 체크섬을 검사했습니다. 최신 결과 롬에서 새 부팅, 오프닝 자막, 캐리 아이템 메뉴, 실제 저장과 새 부팅 불러오기, 엔딩 뒤 저장창, 수정 컷신을 확인했습니다. 앞선 빌드에서는 두 주인공 × 27개 지역 로딩 및 컷신 54개 진입 조건을 시험했습니다.

**확인한 범위에서 추가 일본어 누락은 찾지 못했습니다. 모든 플레이 분기를 처음부터 끝까지 완주한 검증은 아니며, 일부 저해상도 배경 글씨와 모든 이미지 형식의 전수 확인은 마치지 않았습니다.**

<p><img src="https://raw.githubusercontent.com/OldManCraveGuitars-bit/N64-Akumajou-Dracula-Mokushiroku-Real-Action-Adventure-Kr/v0.6/docs/screenshots/02-opening.png" width="640" height="480" alt="오프닝 한글 자막"></p>

오프닝 한글 자막

<p><img src="https://raw.githubusercontent.com/OldManCraveGuitars-bit/N64-Akumajou-Dracula-Mokushiroku-Real-Action-Adventure-Kr/v0.6/docs/screenshots/03-dialogue.png" width="640" height="480" alt="캐리 대사"></p>

캐리 대사

<p><img src="https://raw.githubusercontent.com/OldManCraveGuitars-bit/N64-Akumajou-Dracula-Mokushiroku-Real-Action-Adventure-Kr/v0.6/docs/screenshots/04-save.png" width="640" height="480" alt="화이트 주얼 저장창"></p>

화이트 주얼 저장창

<p><img src="https://raw.githubusercontent.com/OldManCraveGuitars-bit/N64-Akumajou-Dracula-Mokushiroku-Real-Action-Adventure-Kr/v0.6/docs/screenshots/05-inventory.png" width="640" height="480" alt="아이템 메뉴"></p>

아이템 메뉴
