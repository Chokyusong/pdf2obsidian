# Maintenance Tasks

This page lists public roadmap tasks that can be copied into GitHub Issues. Do not include private PDFs, paid learning materials, raw subtitle transcripts, personal Obsidian paths, or local machine paths in issue descriptions.

## Recommended Issues

### Add real before/after conversion examples

Create safe examples using synthetic, public-domain, openly licensed, or explicitly redistributable sample files.

### Add PDF conversion regression tests

Cover text extraction, headings, lists, embedded images, blank-image filtering, table extraction, page markers, and conversion reports.

### Add table extraction research task

Evaluate PyMuPDF table detection limits and document fallback behavior for merged cells, borderless tables, and irregular layouts.

### Add privacy hardcoding scan before release

Run a keyword scan before each release to catch private file names, local paths, paid material titles, raw subtitles, and generated output.

### Improve README for Obsidian users

Add screenshots, common workflows, and non-developer setup notes for Windows and Obsidian vault usage.

### Automate Windows build with GitHub Actions

Verify that the PyInstaller build produces a usable Windows executable on every release tag.

### Add CLI batch conversion entry point

Expose the core converter through a CLI command for batch conversion without starting the GUI.

### Add sample files that are safe for public repository

Generate tiny synthetic PDFs, images, and subtitle files for tests and documentation.

### Improve subtitle line merging into readable paragraphs

Merge fragmented subtitle lines into readable paragraphs without losing timestamp order.

### Add semantic section detection for lecture transcripts

Detect lecture sections such as introduction, definition, example, summary, mission, checklist, and review questions.

### Improve Korean lecture keyword extraction

Avoid treating meaningless frequent words as core concepts in Korean lecture notes.

### Add rule-based lecture pattern detection

Implement local rule-based detection before considering optional AI enhancements.

### Add optional local LLM enhancement plan

Document how optional local LLM tools such as Ollama could improve lecture note structuring without becoming required dependencies.

### Add regression tests for lecture note structuring

Cover subtitle merging, semantic section detection, keyword extraction, examples, action steps, cautions, review questions, and checklist output.

### Add before/after examples for subtitle-to-study-note conversion

Use synthetic subtitle samples only. Do not commit real lecture names, instructor names, paid course titles, or raw private transcripts.

### Add tests for AI mode selection

Verify that Basic mode is the default and that AI Mode remains independent from Output Mode.

### Add mock tests for Ollama client

Mock Ollama status, model list, pull, timeout, and generate responses. Tests must pass without a running Ollama server.

### Add mock tests for AI summarizer

Cover chunking, Ollama failure fallback, and Study Note Markdown rendering without real network calls.

### Add privacy scan for API keys and private course names

Before releases, scan for provider API key names, local paths, private course names, and raw transcript content.
