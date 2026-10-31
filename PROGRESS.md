# 학교 AI 작업실 — 진행 기록

인계 문서: [`docs/handoff.md`](docs/handoff.md)

## 2026-10-31 · Claude Code가 이어받음

### 확인한 사실

- 이 작업은 **클라우드 컨테이너(리눅스)** 에서 돌고 있다. 선생님의 윈도우 PC나 맥이 아니다.
  그래서 여기서 확인되는 RAM·CPU·GPU는 선생님 컴퓨터의 사양이 아니며, 기록하지 않는다.
- 저장소 `shineonyou1274/lmstudio`는 비어 있었다(커밋 없음). 덮어쓴 기존 파일은 없다.
- 이 세션에 연결된 선생님 컴퓨터 폴더(Remote Control)는 없다.

### 한 일

- 인계 문서를 `docs/handoff.md`로 보존했다.
- 이 진행 기록 파일을 만들었다.

### 아직 확인하지 않은 것

- 선생님 PC/맥의 운영체제, RAM, CPU, GPU, 여유 저장 공간, 설치 권한
- LM Studio, Python, Whisper 설치 여부
- 모델·프레임워크·저장 방식·배포 방식 (사양 확인 뒤 결정)

### 다음 행동 (선생님 선택 필요)

사양 확인 방법 중 하나를 고른다.

1. **선생님 PC에서 Claude Code를 직접 실행** (데스크톱 앱 또는 터미널) — 설치·LM Studio 연결 시험까지 이어서 할 수 있어 가장 권장.
2. **아래 명령을 직접 실행하고 결과를 붙여 넣기** — 가장 빠름. 읽기만 하는 명령이다.
3. **맥이라면 Remote Control로 이 세션에 폴더 연결** — 현재 Remote Control 폴더 연결은 맥·리눅스만 지원하고 윈도우는 지원하지 않는다.

병행 가능: 성적 분석실의 **계산 부분**(가상 데이터 생성, 시험별·학생별 변화, 결시 처리, 그래프)은 AI 모델 없이 검증할 수 있으므로 사양 확인과 별개로 여기서 먼저 만들 수 있다.

## 2026-10-31 · 선생님 윈도우 PC 사양 (선생님이 직접 실행해 붙여 준 결과)

| 항목 | 결과 |
|---|---|
| 운영체제 | Windows 11 Pro (10.0.26300) |
| RAM | 15.7 GB |
| CPU | 12세대 Intel Core i7-1260P (12코어 / 16스레드) — 노트북용 저전력 CPU |
| GPU | Intel Iris Xe (내장 그래픽, RAM을 나눠 씀). NVIDIA 없음 (`nvidia-smi` 없음) |
| C: 여유 공간 | 79.5 GB |
| Python | 3.12.10 설치됨 |
| LM Studio 흔적 (`~\.lmstudio`) | `False` — 설치·실행한 적 없는 것으로 보임 |
| 사용자 폴더 | `C:\Users\경남교육청` (한글 경로) |

### 사양으로 본 판단 (아직 실측 전 — 추측과 구분)

- 확실한 것: 전용 그래픽카드가 없으므로 모델은 CPU와 내장 그래픽, 공유 RAM으로 돌아간다. 큰 모델은 무리다.
- 시험해 볼 것: 3~4B급 작은 모델(4비트 양자화)은 쓸 만할 가능성이 높고, 7~8B급은 돌아가더라도 느릴 수 있다. 실제 속도는 LM Studio에서 재 봐야 한다. 구체적 모델은 그 시점의 공식 자료를 확인하고 고른다.
- 이 노트북 한 대를 학급 여러 명이 동시에 쓰는 서버로 쓰는 것은 현실적이지 않을 가능성이 크다. 우선 교사 개인용으로 시작한다.
- 한글 사용자 폴더 경로는 일부 Python·음성 도구에서 오류를 낼 수 있다. 프로젝트 폴더는 `C:\ai-lab`처럼 영문 경로에 두는 것을 권장한다.
- 사용자 이름이 `경남교육청`이라 기관 지급 PC일 수 있다. 프로그램 설치 권한(관리자 권한)과 학교 보안 정책을 먼저 확인해야 한다.

## 2026-10-31 · 기기 결정 논의

- 맥은 인텔 칩이다(선생님 확인). 로컬 AI 면에서 지금 윈도우 PC보다 낫다고 보기 어렵다.
- 선생님이 새 노트북으로 옮길 계획이 있다. 새 기기 사양을 고르는 중이다(미결정).
- 제안: 새 기기를 사기 전에 지금 윈도우 PC에서 LM Studio와 작은 모델을 먼저 시험해 보고, 실제로 무엇이 부족한지 확인한 뒤 고른다. 성적 분석 계산 부분은 기기와 상관없이 먼저 만들 수 있다.
- 지금 윈도우 PC는 새 기기를 사도 "동료 교사 환경과 비슷한 윈도우 시험용"으로 남겨 두면 좋다.

### 사양 확인 명령 (읽기 전용)

윈도우 PowerShell:

```powershell
Get-CimInstance Win32_OperatingSystem | Select-Object Caption, Version, @{n='RAM_GB';e={[math]::Round($_.TotalVisibleMemorySize/1MB,1)}}
Get-CimInstance Win32_Processor | Select-Object Name, NumberOfCores, NumberOfLogicalProcessors
Get-CimInstance Win32_VideoController | Select-Object Name, DriverVersion
Get-PSDrive -PSProvider FileSystem | Select-Object Name, @{n='Free_GB';e={[math]::Round($_.Free/1GB,1)}}
nvidia-smi --query-gpu=name,memory.total --format=csv
python --version
Test-Path "$env:USERPROFILE\.lmstudio"
```

- `nvidia-smi`는 NVIDIA 그래픽카드가 있을 때만 결과가 나온다. 오류가 나도 괜찮다.
- 마지막 줄이 `True`면 LM Studio를 한 번이라도 실행한 적이 있다는 뜻일 가능성이 높다.

맥 터미널:

```bash
sw_vers; sysctl -n machdep.cpu.brand_string; sysctl -n hw.memsize | awk '{print $1/1073741824 " GB"}'; df -h ~ | tail -1; python3 --version; ls -d ~/.lmstudio
```
