# AGENTS.md

# PDF2Obsidian 프로젝트 규칙

## 프로젝트 목표

PDF2Obsidian은 PDF 변환기가 아니다.

모든 학습자료를 Obsidian에서 바로 사용할 수 있는 Markdown 구조로 변환하는 것이 목표이다.

지원 대상

- PDF
- 이미지
- SRT
- VTT
- TXT
- Markdown

향후 지원

- DOCX
- PPTX
- YouTube 자막
- Audio
- Video

---

## 핵심 원칙

- Local-first
- Privacy-first
- Obsidian-first
- Windows-first

기본 기능은 외부 AI API 없이 동작해야 한다.

사용자의 파일을 외부 서버로 전송하지 않는다.

---

## 개발 원칙

- 기존 기능을 삭제하지 않는다.
- 정상 동작하는 코드를 처음부터 다시 작성하지 않는다.
- 구현된 기능은 중복 구현하지 않는다.
- 작은 단위로 수정한다.
- GUI와 변환 로직을 분리한다.
- 재사용 가능한 구조를 유지한다.

---

## 출력 원칙

현재 완성 대상

- Raw Markdown
- Structured Markdown

향후 추가

- Study Note
- 전자책 원고
- Local Wiki
- Obsidian MOC
- Flashcards
- Q&A

구현되지 않은 기능을 README에 완료된 것처럼 작성하지 않는다.

---

## OCR

OCR은 선택 기능이다.

우선순위

1. PDF 텍스트 사용
2. 필요할 때만 OCR

OCR이 없어도 프로그램은 종료되지 않아야 한다.

---

## AI 정책

핵심 기능은

- OpenAI API
- Claude API
- Gemini API

없이 동작해야 한다.

향후 AI 연동은 선택 기능으로만 추가한다.

---

## 테스트

작업 전후 반드시 실행한다.

pytest

ruff check .

테스트가 실패하면 원인을 먼저 수정한다.

---

## Git 규칙

Conventional Commit 사용

예)

feat:
fix:
docs:
test:
refactor:
chore:

---

## 금지사항

- 프로젝트명을 변경하지 않는다.
- 기존 기능을 깨뜨리지 않는다.
- 처음부터 다시 작성하지 않는다.
- 불필요한 의존성을 추가하지 않는다.
- 사용자의 파일을 외부로 전송하지 않는다.

---

## 장기 목표

PDF2Obsidian을 모든 학습자료를 Obsidian으로 변환하는 최고의 로컬 오픈소스 프로젝트로 발전시킨다.
