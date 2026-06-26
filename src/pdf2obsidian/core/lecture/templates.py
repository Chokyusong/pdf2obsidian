from __future__ import annotations

from datetime import date

PLACEHOLDER = "Not clearly found in source."

LECTURE_STUDY_NOTE_SECTION_HEADINGS = [
    "## 0. One-Sentence Core Message",
    "## 1. Full Lecture Overview",
    "## 2. Lecture Flow Structure",
    "## 3. Key Concepts",
    "## 4. Detailed Lecture Notes",
    "## 5. Comparison / Structure",
    "## 6. Numbers / Cases",
    "## 7. Practical Application",
    "## 8. Mission / Exercise",
    "## 9. Personal Application",
    "## 10. Final Core Review",
    "## 11. Next Actions",
]


def _yaml_value(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _text(value: str | None) -> str:
    return value.strip() if value and value.strip() else PLACEHOLDER


def _list_items(value: str | None, count: int = 3, checkbox: bool = False) -> str:
    if value and value.strip():
        lines = [line.strip() for line in value.splitlines() if line.strip()]
        if lines:
            return "\n".join(lines)

    marker = "- [ ]" if checkbox else "-"
    return "\n".join(f"{marker} {PLACEHOLDER}" for _ in range(count))


def _numbered_items(value: str | None, count: int = 3) -> str:
    if value and value.strip():
        lines = [line.strip() for line in value.splitlines() if line.strip()]
        if lines:
            return "\n".join(lines)
    return "\n".join(f"{index}. {PLACEHOLDER}" for index in range(1, count + 1))


def render_lecture_study_note(
    title: str,
    source_type: str,
    overview: str = "",
    flow: str = "",
    concepts: str = "",
    details: str = "",
    comparisons: str = "",
    numbers: str = "",
    actions: str = "",
    mission: str = "",
    personal_application: str = "",
    final_review: str = "",
    next_actions: str = "",
    core_message: str = "",
    source_file: str = "",
    created: date | None = None,
) -> str:
    created_date = created or date.today()
    note_title = title.strip() or "Untitled lecture"
    source_label = source_type.strip() or "transcript"

    return f"""---
title: {_yaml_value(note_title)}
type: "lecture-study-note"
source: {_yaml_value(source_label)}
source_file: {_yaml_value(source_file or source_label)}
status: "processed"
created: "{created_date.isoformat()}"
tags:
  - lecture-note
  - study-note
  - obsidian
---

# {note_title}

## 0. One-Sentence Core Message

- {_text(core_message)}

## 1. Full Lecture Overview

### Core Problem

{_text(overview)}

### Lecture Outcome

{_text(final_review)}

### Main Takeaway

{_text(core_message or final_review)}

---

## 2. Lecture Flow Structure

| Order | Topic | Key Content | Importance |
|---|---|---|---|
{_text(flow)}

---

## 3. Key Concepts

{_text(concepts)}

---

## 4. Detailed Lecture Notes

{_text(details)}

---

## 5. Comparison / Structure

| Category | A | B |
|---|---|---|
{_text(comparisons)}

---

## 6. Numbers / Cases

| Item | Content | Meaning |
|---|---|---|
{_text(numbers)}

---

## 7. Practical Application

### Actions To Take Now

{_numbered_items(actions)}

### Small Action For Today

- {PLACEHOLDER}

### Long-Term Habit Or Asset To Build

- {PLACEHOLDER}

---

## 8. Mission / Exercise

{_text(mission)}

---

## 9. Personal Application

### Why This Lecture Matters

{_text(personal_application)}

### How It Connects To My Project Or Work

{PLACEHOLDER}

### Points To Review Later

{PLACEHOLDER}

---

## 10. Final Core Review

{_list_items(final_review)}

## 11. Next Actions

{_list_items(next_actions or actions, checkbox=True)}
"""
