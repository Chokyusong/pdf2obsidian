# PDF2Obsidian

🇺🇸 [English](README.md) | 🇰🇷 한국어

[![CI](https://github.com/Chokyusong/pdf2obsidian/actions/workflows/ci.yml/badge.svg)](https://github.com/Chokyusong/pdf2obsidian/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/Chokyusong/pdf2obsidian)](https://github.com/Chokyusong/pdf2obsidian/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

PDF2Obsidian은 PDF, 이미지, 강의 자막 파일을 Obsidian에서 바로 사용할 수 있는 Markdown 문서와 assets 폴더 구조로 변환하는 로컬 데스크톱 도구입니다.

사용자의 파일을 외부 서버로 업로드하지 않으며, OpenAI, Claude, Gemini 같은 외부 AI API를 필수로 사용하지 않습니다. Windows 사용자가 로컬에서 쉽게 실행하는 것을 1차 목표로 합니다.

![PDF2Obsidian GUI](docs/assets/gui-screenshot.png)

## 프로젝트 목표

PDF2Obsidian은 학생, 연구자, 지식관리 사용자들이 PDF와 강의 자료를 Obsidian 노트로 재사용할 수 있게 돕습니다. 1차 MVP는 클라우드 자동화보다 안정적인 로컬 변환에 집중합니다.

- PDF 텍스트 레이어를 경량 Markdown으로 변환
- PDF 구조를 가능한 범위에서 편집 가능한 Markdown으로 복원
- PDF 내부 이미지를 압축 WebP assets로 저장
- 이미지 파일을 WebP assets와 Markdown으로 변환
- 강의 자막을 구조화된 학습 노트로 변환
- OCR은 로컬에 설치된 OCR 도구가 있을 때만 선택적으로 실행

## 최종 제품 비전

장기 목표는 두 가지 흐름에 집중합니다.

1. PDF를 원본 시각적 레이아웃에서 벗어나지 않는 Markdown으로 변환합니다.
2. 강의 자막 또는 유튜브 자막을 영상 없이도 이해할 수 있는 상세 학습 자료로 변환합니다.

기본 흐름은 클라우드 AI 제품과 달라야 합니다. PDF2Obsidian은 외부 AI API나 클라우드 업로드를 필수로 요구하지 않습니다. 고급 AI 기능은 사용자가 직접 선택한 로컬 도구를 통해서만 선택적으로 연결합니다.

목표 기능:

- PDF 변환: 레이아웃 인식 텍스트 추출, 제목/목록/표 복원, 내장 이미지 추출, fallback 페이지 이미지, Obsidian Markdown 출력
- 자막 변환: SRT/VTT/TXT/MD 파싱, 반복 말투 정리, 강의 흐름 보존, 개념 설명, 예시, 절차, 주의사항, 최종 요약
- 유튜브 자막 흐름: 먼저 다운로드한 유튜브 자막 파일을 입력받고, 추후 URL 직접 입력을 검토
- 출력: Obsidian vault로 바로 옮길 수 있는 Markdown 폴더와 assets 구조

## 왜 만들었나요?

PDF 자료, 강의 이미지, 자막 파일은 Obsidian에서 바로 재사용하기 어렵습니다. PDF2Obsidian은 다음 흐름을 단순하게 만듭니다.

1. PDF, 이미지, 자막 파일을 선택합니다.
2. 페이지나 이미지를 압축된 WebP assets로 저장합니다.
3. Obsidian Wiki Link 형식의 Markdown을 생성합니다.
4. 출력 폴더를 열어 Obsidian vault로 옮깁니다.

## 주요 기능

- PDF 파일을 Markdown으로 변환
- PyMuPDF로 PDF 페이지 텍스트 추출
- PDF 텍스트 블록에서 간단한 제목, 굵은 글씨, 목록, 문단 추론
- 감지 가능한 PDF 표를 Markdown 표로 변환
- PDF 내부 이미지를 압축 WebP assets로 저장
- PDF 가져오기 모드 선택: Structured Markdown, Raw Text Markdown, Page Image Markdown fallback
- PNG, JPG, JPEG, WebP 이미지를 압축 WebP로 저장
- EasyOCR 우선, Tesseract 대안 OCR 래퍼 제공
- SRT, VTT, TXT, MD 강의 자막을 학습 노트로 정리
- 자막 타임스탬프 순서 유지
- Obsidian에서 바로 열 수 있는 Markdown 생성
- PySide6 기반 최소 GUI와 드래그 앤 드롭 지원
- 추후 CLI 또는 웹앱 확장을 위해 핵심 변환 로직과 GUI 분리

## 빠른 링크

- [출력 예시](docs/examples.md)
- [로드맵](docs/roadmap.md)
- [웹앱 확장 계획](docs/webapp-plan.md)
- [기여 안내](CONTRIBUTING.md)

## 설치 방법

Python 3.11 이상을 권장합니다.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

`requirements.txt`는 현재 프로젝트를 editable package로 설치하므로, 프로젝트 루트에서 아래 명령으로 실행할 수 있습니다.

```powershell
python -m pdf2obsidian.main
```

## 사용 방법

1. 앱을 실행합니다.
2. 파일 선택 버튼 또는 드래그 앤 드롭으로 PDF, 이미지, 자막 파일을 추가합니다.
3. 출력 폴더를 선택합니다.
4. 이미지 품질을 60, 75, 90 중에서 선택합니다.
5. OCR이 필요하고 로컬 OCR 도구가 설치되어 있으면 OCR을 켭니다.
6. `Start Conversion` 버튼을 누릅니다.
7. 변환 완료 후 output 폴더를 엽니다.

기본 출력 위치:

```text
output/
```

## Obsidian 출력 예시

`sample.pdf`를 변환하면 다음 구조가 생성됩니다.

```text
output/
└─ sample/
   ├─ sample.md
   └─ assets/
      ├─ image_p001_001.webp
      └─ table_p002_001.webp
```

Markdown 예시:

```markdown
---
title: "sample"
source_file: "sample.pdf"
created: "2026-06-25"
type: "pdf-import"
---

# sample

<p align="center"><sub>PDF 1페이지</sub></p>

## Main heading

본문 문단...

##### Table 1

| 항목 | 실행 |
| --- | --- |
| 예시 | 이렇게 하기 |

##### Image 1

![[assets/image_p001_001.webp]]
```

`lecture.vtt` 같은 강의 자막 파일은 강의 개요, 핵심 개념, 시간대별 정리, 체크리스트, 복습 질문이 포함된 학습 노트로 변환됩니다.

## PDF 가져오기 모드

- `Structured Markdown`: 기본값입니다. PDF 내용을 제목, 문단, 목록, Markdown 표, 링크, 필요한 이미지 중심의 편집 가능한 Markdown으로 변환합니다.
- `Raw Text Markdown`: PDF 텍스트 레이어를 가능한 그대로 유지하면서 감지된 표와 내부 이미지는 함께 보존합니다.
- `Page Image Markdown`: 스캔 PDF나 레이아웃이 매우 복잡한 PDF를 위한 fallback입니다. PDF 각 페이지를 `page_001.webp`, `page_002.webp`로 렌더링하고 페이지 이미지만 삽입합니다.

PyMuPDF가 단순 표 구조를 감지할 수 있는 경우 Markdown 표로 출력합니다. 불규칙한 표는 깨진 Markdown으로 억지 변환하지 않고 표 영역만 WebP fallback으로 저장할 수 있습니다.

## Windows 안내

PowerShell에서 스크립트 실행이 막히면 현재 세션에만 다음 명령을 적용할 수 있습니다.

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

PySide6 설치가 실패하면 pip를 먼저 업그레이드하세요.

```powershell
python -m pip install --upgrade pip
```

## OCR 안내

OCR은 선택 기능입니다. OCR 라이브러리가 없어도 PDF/Image/자막 변환 기능은 계속 사용할 수 있습니다.

EasyOCR 설치:

```powershell
pip install easyocr
```

Tesseract 대안을 사용하려면 Tesseract 프로그램과 Python wrapper가 필요합니다.

```powershell
pip install pytesseract
```

Tesseract for Windows는 별도로 설치해야 합니다. OCR을 켰는데 OCR 엔진이 없으면 프로그램은 종료되지 않고 안내 메시지를 Markdown에 남깁니다.

## EXE 빌드

의존성을 설치한 뒤 다음 명령을 실행합니다.

```powershell
powershell -ExecutionPolicy Bypass -File build.ps1
```

내부적으로 다음 PyInstaller 명령을 사용합니다.

```powershell
pyinstaller --noconfirm --windowed --name PDF2Obsidian src/pdf2obsidian/main.py
```

PySide6 환경에 따라 Qt plugin 또는 resource 관련 옵션이 추가로 필요할 수 있습니다. 실행 파일에서 Qt 관련 오류가 나면 PyInstaller와 PySide6를 업그레이드한 뒤 다시 빌드하세요.

## 개발

테스트 실행:

```powershell
pytest
```

Ruff 검사:

```powershell
ruff check .
```

## 로드맵

- PDF 원본 시각적 레이아웃 보존 강화
- 강의/유튜브 자막 상세 정리 품질 개선
- OCR 품질 개선
- 표 추출
- 이미지 크기 최적화
- Markdown 템플릿 설정
- 로컬 웹앱 버전
- 자막 정리 품질 향상을 위한 선택적 로컬 LLM 연동
- exe 배포 자동화

## 향후 웹앱 확장

핵심 변환 로직은 `src/pdf2obsidian/core/` 아래에 있어 GUI, CLI, FastAPI 서버에서 재사용할 수 있습니다.

첫 웹 버전은 사용자의 PC에서 `localhost`로 실행되는 로컬 웹앱을 목표로 합니다. 서버형 웹사이트는 개인정보 보호 안내와 zip 다운로드 흐름을 갖춘 뒤 검토합니다.

## GitHub 업로드

직접 업로드하려면 `<github-username>`을 본인의 GitHub 사용자명으로 바꾸세요.

```powershell
git init
git add .
git commit -m "Initial commit: PDF2Obsidian MVP"
git branch -M main
git remote add origin https://github.com/<github-username>/pdf2obsidian.git
git push -u origin main
```

GitHub CLI를 사용할 수도 있습니다.

```powershell
gh auth login
gh repo create pdf2obsidian --public --source=. --remote=origin --push
```

## 기여

Issue와 Pull Request를 환영합니다. 이 프로젝트는 local-first, 단순함, 초보자 친화성을 우선합니다. 필수 클라우드 업로드, 로그인, 결제, 외부 AI API 의존성은 추가하지 않습니다.

## 라이선스

MIT License. 자세한 내용은 [LICENSE](LICENSE)를 확인하세요.
