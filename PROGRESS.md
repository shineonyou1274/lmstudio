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
| 메모리 구성 | 2GB × 8채널, 4267MT/s — LPDDR4X 온보드(메인보드에 붙은) 메모리로 보임. 증설 불가로 판단 |
| 디스크 | 448GB 중 80.6GB 여유 (선생님 스크린샷). 시작에 필요한 약 20GB는 충분 |

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

## 2026-10-31 · 결정: 지금 PC로 가능한 것부터

- **결정**: 지금 윈도우 PC(16GB, 증설 불가)로 가능한 것부터 시작하고, 새 노트북을 사면 그때 옮긴다.
- LM Studio 공식 요구 사항(https://lmstudio.ai/docs/app/system-requirements, 2026-10-31 확인):
  윈도우 x64는 AVX2 필수, RAM 16GB 이상 권장, 전용 VRAM 4GB 이상 권장.
  i7-1260P는 AVX2를 지원한다. 전용 VRAM이 없으므로 CPU 중심으로 돌아갈 것이다(속도는 실측 필요).
- 진행 방식: 두 갈래로 나란히 간다.
  1. 선생님 PC: LM Studio 설치 → 모델 검색 화면 캡처 → 함께 작은 모델 고르기 → 첫 대화와 속도 측정
  2. 클라우드(여기): 성적 분석실 계산 부분 범위 제안 → 선생님 승인 → 구현·검증

## 2026-11-01 · 설치 파일 확인

- 선생님이 받은 파일: `Bionic-1.1.10-8-x64.exe`
- lmstudio.ai/download 확인 결과: **LM Studio Bionic**은 LM Studio 회사의 공식 제품이지만, 일반 LM Studio와 다른 별도 앱이다.
  공식 설명은 "An agent made for open models"(오픈 모델용 에이전트)이다. 클라우드 사용 여부와 로그인 필요 여부는 공식 페이지에 적혀 있지 않다(미확인).
- 이 프로젝트에 필요한 것은 모델 관리와 로컬 서버(API) 기능이 있는 **일반 LM Studio**(2026-11-01 기준 Windows 0.4.28)다.
  다운로드: https://lmstudio.ai/download/latest/win32/x64
- 결정: Bionic은 지금 설치하지 않는다. 에이전트 앱은 PC에서 작업을 실행할 수 있으므로, 필요해지면 데이터 경로와 권한을 따로 점검한 뒤 검토한다.

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
