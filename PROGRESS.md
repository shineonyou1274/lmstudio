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
