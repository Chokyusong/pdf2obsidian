# Design Decisions

This document records project-level decisions that should guide future work. Update it whenever the project changes direction in a meaningful way.

## Decision Priority

When documents disagree, use this order:

1. Source code and tests.
2. `AGENTS.md`.
3. This file.
4. `docs/roadmap.md`.
5. README files.

The roadmap can change often. Design decisions should change only when there is a clear reason.

## Local-First Is Required

PDF2Obsidian is built for users who want to convert learning material on their own computer. Core conversion must not require cloud uploads, login, payment, or an external AI API.

Reasons:

- Users may process private notes, paid learning material, research PDFs, or personal Obsidian vault content.
- Local processing is easier to explain and trust.
- The project should remain useful even without an internet connection after installation.

## Privacy-First Samples and Releases

Public examples, screenshots, tests, and release assets must not include private PDFs, paid course names, raw private transcripts, personal paths, API keys, or personal Obsidian notes.

Safe public examples should be synthetic, public-domain, openly licensed, or explicitly redistributable.

## Obsidian-First Output

The product goal is not generic document conversion. The output should be useful inside an Obsidian vault.

This means:

- Markdown should be readable and editable.
- Assets should be lightweight and placed predictably.
- Generated notes should avoid unnecessary orphan-note creation.
- Lecture notes should preserve concepts, examples, numbers, procedures, cautions, and action items.

## Windows-First Desktop Workflow

The first supported user experience is Windows desktop. Cross-platform support can be added later, but Windows behavior should not regress.

Reasons:

- The current GUI and release workflow target Windows users.
- PyInstaller packaging and local Ollama setup need Windows-specific testing.
- Many target users expect a downloadable ZIP or executable instead of a developer setup.

## PDF Conversion Before OCR

PDF text layers should be used before OCR. OCR is optional and should not be required for the application to run.

Priority:

1. Extract embedded text from the PDF.
2. Extract embedded images when useful.
3. Use OCR only when the user enables it or when a future workflow clearly needs it.

## Ollama Is Optional

Local AI with Ollama is an optional enhancement for lecture reconstruction. It must not become a required dependency for basic PDF, image, or transcript conversion.

`qwen2.5:7b` is the recommended practical local model because it is more realistic for normal PCs. Larger qwen3.6-class models can be documented as high-quality or experimental, but they may be too slow or unstable for typical users.

## Cloud AI Is Future Optional Work

OpenAI-compatible cloud AI can be considered later, but only as an explicit optional mode. The application should continue to work without OpenAI, Claude, Gemini, or any other cloud AI provider.

## Prompts Must Stay General

Lecture prompts must not hardcode one course, instructor, keyword set, or example output. Golden examples can be used to extract quality rules, but not to force specific content into unrelated lectures.

Output quality rules should be general:

- Preserve logical flow.
- Preserve important numbers and examples.
- Explain concepts with enough density.
- Keep procedures and missions actionable.
- Avoid leaked prompt text, thinking traces, and Obsidian wiki links in final lecture notes.

## Prefer One-Shot Local AI by Default

The default Ollama workflow should save the first cleaned result with warnings instead of repeatedly retrying slow fallback reconstruction.

Reasons:

- Local models vary widely by hardware.
- Long retry loops make the GUI feel stuck.
- Users need visible progress and saved output more than hidden repeated attempts.

High-quality retry modes may be added later as explicit advanced options.

## GUI Must Show Progress

Long-running actions should show status through labels, logs, progress bars, or step messages.

This includes:

- Transcript to Markdown.
- PDF to Markdown plus images.
- PDF to compressed WebP PDF.
- Ollama installation.
- Ollama model download.
- Ollama reconstruction.

## Keep GUI and Conversion Logic Separate

GUI code should coordinate input, options, progress, and display. Conversion logic should stay in reusable core modules so future CLI, web, or batch workflows can reuse it.

## Release Artifacts Must Be Fresh

Release ZIP files must be built from the final source for that release. Do not reuse an older `dist` folder.

Before uploading a release asset:

- Run tests.
- Run Ruff.
- Build the executable.
- Confirm prompt files are included.
- Confirm the release version is consistent across code, README links, and changelog.
- Move local build artifacts to `.trash/` after upload when cleanup is requested.
