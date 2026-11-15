# Changelog

All notable changes to the office2md skill are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this skill adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] — 2026-08-03

### Added
- **Semantic post-processing**: automatic conversion of decimal ratios to
  percentages when the column/field name indicates a ratio, percentage,
  rate, or progress field (supports Chinese and English keywords).
  —  `scripts/convert.py`

- **Conversion report** (`*.report.md`): generated alongside every output
  file, documenting: conversion steps, all non-faithful transformations
  (original value, transformed value, reason, risk level), risk assessment
  by severity, and human review recommendations.
  —  `scripts/convert.py`

- **New CLI flags**:
  - `--no-semantic` — disable semantic post-processing (faithful-only mode)
  - `--no-report` — skip conversion report generation
  - `--version` — show office2md version

- **`--json` output enhancement**: single-file mode now includes
  `changes_count`, `changes[]` (detailed list of semantic changes), and
  `report_path` in JSON output.

- **Changelog**: this file.

### Changed
- `convert_file()` now returns a 3-tuple `(markdown, report_text, changes)`
  instead of just the markdown string. Python module users should update
  their unpacking.
- Batch conversion results are now dicts instead of tuples, with keys:
  `input`, `output`, `success`, `changes_count`, `report_path`, `error`.

### Fixed
- N/A

## [1.0.0] — 2026-08-03

### Added
- Initial release of office2md skill.
- `scripts/convert.py`: CLI wrapper around Microsoft's markitdown library
  with auto-install on first use (PyPI → GitHub fallback).
- Support for: Word (.docx, .doc), Excel (.xlsx, .xls, .csv), PowerPoint
  (.pptx, .ppt), PDF, HTML/URLs, images (with OCR), audio/video (with
  whisper), Jupyter notebooks, ZIP archives, JSON, XML, plain text, and
  more.
- Single-file and batch directory conversion modes.
- OCR (tesseract / azure) and vision model integration.
- JSON output for machine-readable results.
- `SKILL.md` with comprehensive usage guide and cross-platform compatibility.
- `references/formats.md` with format-specific conversion tips.
- `agents/openai.yaml` with UI metadata for Codex skill gallery.
