---
name: office2md
description: >-
  Convert Office documents and various file formats to clean Markdown using
  Microsoft markitdown library, with semantic post-processing (decimal ratios
  to percentages, etc.) and automatic conversion reports. Supports Word
  (.docx, .doc), Excel (.xlsx, .xls, .csv), PowerPoint (.pptx, .ppt), PDF,
  HTML, images (with OCR), audio and video (with whisper transcripts),
  Jupyter notebooks, ZIP archives, JSON, XML, and more. Use when the user
  wants to convert a document or file to Markdown, extract text or content
  from Office files, batch-convert a directory of documents, read the
  contents of a docx/xlsx/pptx/pdf as text for analysis, or convert web
  pages or URLs to Markdown.
---

# office2md

Convert Office documents and files to Markdown using Microsoft's open-source
[markitdown](https://github.com/microsoft/markitdown) library, with semantic
post-processing and automatic conversion reports.

**Version**: v1.0.1

The bundled `scripts/convert.py` provides a single entry point with
auto-install, batch conversion, semantic enhancements, and consistent output
across agent platforms.

## Quick Start

Convert a single file (default: semantic mode + report):

```bash
python3 <skill-dir>/scripts/convert.py path/to/document.docx -o document.md
```

This produces two files:
- `document.md` — the converted Markdown (with semantic enhancements)
- `document.report.md` — the conversion report

Faithful-only mode (no semantic changes):

```bash
python3 <skill-dir>/scripts/convert.py data.xlsx -o data.md --no-semantic
```

Convert without generating a report:

```bash
python3 <skill-dir>/scripts/convert.py report.pdf -o report.md --no-report
```

Batch-convert a directory:

```bash
python3 <skill-dir>/scripts/convert.py --dir ./docs --output-dir ./docs-md
```

The script auto-installs `markitdown` on first run (PyPI first, GitHub source
as fallback).

## Supported Formats

| Category | Extensions |
|---|---|
| Word | .docx, .doc |
| Excel | .xlsx, .xls, .csv |
| PowerPoint | .pptx, .ppt |
| PDF | .pdf |
| Web | .html, .htm, URLs |
| Images (OCR) | .jpg, .jpeg, .png, .gif, .bmp, .tiff |
| Audio/Video | .mp3, .mp4, .wav, .mpga, .mpeg |
| Other | .json, .xml, .ipynb, .zip, .txt, .rtf, .yaml, .yml |

Run `--formats` for the full list, `--check` to verify environment.

## Semantic Post-Processing

By default, the converter applies semantic enhancements beyond faithful
conversion. These are non-faithful changes designed to improve readability.
Every change is documented in the conversion report.

### Decimal to Percentage

Detects ratio/percentage columns and fields by their names (e.g. "占比",
"增长率", "完成率", "percentage", "rate") and converts decimal values
between -1 and 1 to percentages.

**Examples:**
- Table column named "占比" with value `0.35` → `35%`
- Inline field "完成率: 0.85" → "完成率: 85%"
- Negative growth `−0.05` → `−5%`

**Recognition rules:**
- Column headers or field labels must match ratio keywords (Chinese + English)
- Value must be a decimal number between -1 and 1 (excluding 0, 1, -1)
- Risk level: medium — based on label inference, could misinterpret non-ratio decimals

### Disabling Semantic Mode

Use `--no-semantic` for a purely faithful conversion:

```bash
python3 <skill-dir>/scripts/convert.py data.xlsx -o data.md --no-semantic
```

## Conversion Report

Every conversion generates a `.report.md` file alongside the output. The
report includes:

- **Basic info** — tool version, source file, timestamp, character counts
- **Key steps** — numbered list of conversion pipeline steps
- **Non-faithful changes** — table of every semantic change with original
  value, transformed value, reason, and risk level
- **Risk assessment** — changes grouped by risk level (high / medium / low)
  with human review recommendations
- **General advice** — known limitations and best practices

Report files are named `<output-basename>.report.md` and written to the same
directory as the output file.

For detailed format-specific notes, see [references/formats.md](references/formats.md).

## CLI Reference

```
positional:
  input                 Input file path or URL
  output                Output Markdown file (positional)

options:
  -o, --output PATH     Output Markdown file path
  --dir PATH            Convert all files in a directory
  --output-dir PATH     Output directory for batch mode
  --no-recursive        Skip subdirectories in batch mode
  --ocr                 Enable OCR for image files
  --ocr-engine {tesseract,azure}
  --vision              Enable vision model for image understanding
  --gpt-model NAME      OpenAI model for vision/complex tasks
  --no-semantic         Disable semantic post-processing (faithful only)
  --no-report           Don't generate a conversion report
  --check               Check environment and markitdown availability
  --formats             List supported file formats
  --version             Show office2md version
  --json                Output results in JSON format
```

## Workflow Patterns

### 1. Read a document's contents

When the user asks to "read", "summarize", or "look at" a document file:

```bash
python3 <skill-dir>/scripts/convert.py path/to/file.docx -o /tmp/file.md
```

Then work with `/tmp/file.md`. Check `/tmp/file.report.md` for any
non-faithful transformations that might affect interpretation.

### 2. Batch convert a folder

```bash
python3 <skill-dir>/scripts/convert.py --dir ./input_docs --output-dir ./output_md
```

Each output file gets its own `.report.md`. Files that fail conversion are
skipped with a stderr message; exit code is non-zero if any file failed.

### 3. Faithful-only mode for data-critical tasks

When accuracy is paramount and the user needs exact values (e.g. financial
analysis, data extraction for computation):

```bash
python3 <skill-dir>/scripts/convert.py financials.xlsx -o out.md --no-semantic
```

### 4. Use as a Python module

```python
import sys
sys.path.insert(0, "<skill-dir>/scripts")
from convert import convert_file, convert_directory, post_process_markdown

# Single file with semantic processing and report
md_text, report_text, changes = convert_file("report.docx", "report.md")

# Faithful only
md_text, _, _ = convert_file("data.xlsx", "data.md", semantic=False)

# Just post-process existing markdown
processed, changes = post_process_markdown(raw_md, semantic=True)
```

## Dependencies

- **Python 3.8+** required
- **markitdown** — auto-installed on first run; full install includes
  `markitdown[all]`
- **OCR** — requires Tesseract (local) or Azure Vision API key
- **Vision** — requires `OPENAI_API_KEY` environment variable with
  vision-capable model access
- **Audio/Video transcription** — requires Whisper or Azure Speech

## Environment Variables

| Variable | Purpose |
|---|---|
| `OPENAI_API_KEY` | Required for --vision and --gpt-model options |
| `AZURE_VISION_ENDPOINT` | Azure Computer Vision endpoint (for azure OCR) |
| `AZURE_VISION_KEY` | Azure Computer Vision key (for azure OCR) |

## Cross-Platform Compatibility

This skill is designed to work with any agent platform (Codex, Claude Code,
OpenClaw, etc.):

- No Codex-specific APIs — pure Python CLI + Python module
- Standard Unix paths; works on macOS, Linux, and Windows (WSL/PowerShell)
- Self-contained script with auto-install; no setup steps required
- Deterministic output: UTF-8 Markdown to stdout or file
- Structured JSON output with `--json` for machine-readable results
- Conversion reports for auditability of non-faithful changes

## Troubleshooting

**markitdown fails to install:** Install manually:
```bash
pip install markitdown[all]
# or from source:
pip install 'markitdown[all] @ git+https://github.com/microsoft/markitdown.git'
```

**Semantic conversion got a value wrong:** Use `--no-semantic` for faithful
output, or check the `.report.md` file to see exactly what was changed and
why.

**PDF conversion is slow or low quality:** markitdown uses pdfplumber by
default. For scanned PDFs, use `--ocr`.

**Images produce no text:** OCR is off by default. Add `--ocr` flag.

**Excel files produce incomplete output:** Complex spreadsheets with multiple
sheets are converted to Markdown tables; very large files may be truncated.
Use `--json` mode to check success status per file in batch mode.

## Version History

See [references/changelog.md](references/changelog.md) for the full changelog.
