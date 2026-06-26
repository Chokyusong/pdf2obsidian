# Security Policy

PDF2Obsidian is a local-first desktop tool. It should not require cloud upload, login, payment, or external AI API access to convert files.

## Supported Versions

The current public MVP is `0.1.x`.

## Reporting a Vulnerability

Please open a GitHub issue if you find a security or privacy problem. Do not include private files, secrets, or personal documents in the issue.

Report accidental private data exposure as a security/privacy issue. This includes private file names, local paths, API keys, paid PDF titles, personal notes, raw subtitle text, or generated output that should not be public.

## Security Expectations

- User files should remain on the local machine.
- OCR must be optional.
- External AI APIs must not be required.
- Build artifacts and generated output should not be committed.
- Private prompt archives, personal instructions, paid learning materials, and local vault paths should not be published.
- Local-first behavior must not be weakened without explicit discussion in an issue or pull request.
- Required cloud uploads, login, payment, or external AI API access must not be introduced silently.
