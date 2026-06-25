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
