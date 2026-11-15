# Format-Specific Conversion Guide

Detailed notes per file format. Consult this when output quality needs improvement
or when working with a specific document type.

## Word Documents (.docx, .doc)

- Headings are preserved as Markdown `#` headings based on Word heading styles.
- Tables become Markdown tables.
- Images are extracted and referenced via relative paths (when supported by the converter).
- Tracked changes are accepted/converted to final text.
- For `.doc` (legacy Word), markitdown may require LibreOffice or `docx2txt` as a backend.

**Tip:** If formatting is lost, check if the document uses custom styles rather than built-in heading styles.

## Excel Spreadsheets (.xlsx, .xls, .csv)

- Each sheet is converted to a separate Markdown table.
- Sheet names become section headings.
- Merged cells are flattened.
- Formulas are converted to their calculated values.

**Tip:** Very large sheets (>10k rows) may produce enormous Markdown. Consider converting specific ranges or sheets first.

## PowerPoint Presentations (.pptx, .ppt)

- Each slide becomes a section with its title as a heading.
- Speaker notes are included when available.
- Slide text and tables are converted.
- Images are not described (use vision model for that).

**Tip:** Use with `--vision` and `--gpt-model` to get descriptions of diagram-heavy slides.

## PDF Documents (.pdf)

- Text-based PDFs extract text with reasonable layout preservation.
- Scanned PDFs require `--ocr` to extract text.
- Tables in PDFs may not always preserve column structure perfectly.

**OCR Engines:**
- `tesseract` — local, free, requires Tesseract OCR installed
- `azure` — cloud-based, higher accuracy, requires Azure Vision API key

**Tip:** For multi-column PDFs, try `--ocr` even on text-based PDFs if the layout is complex.

## Web Pages / HTML (.html, .htm, URLs)

- Article text is extracted, boilerplate removed.
- Links are preserved as Markdown links.
- Images are referenced but not downloaded by default.

**Tip:** For URL conversion, markitdown fetches and parses the page. Rate limiting may apply for frequent use.

## Images (OCR / Vision)

### OCR mode (`--ocr`)
- Extracts text from images (scans, screenshots, photos of documents).
- Output is plain text wrapped in Markdown.

### Vision mode (`--vision`)
- Uses GPT-4V / similar to describe image content in natural language.
- Requires `OPENAI_API_KEY` and a vision-capable model.
- Much richer descriptions than OCR but more expensive and slower.

**Tip:** Use OCR for document-like images (forms, receipts, scanned text). Use vision for photos, diagrams, charts, and infographics.

## Audio / Video

- Speech is transcribed to text.
- Timestamps are included in the output.
- Requires Whisper (local or API) or Azure Speech.

**Tip:** Long audio files (>30 min) can take a while. Consider splitting first if you only need a segment.

## Jupyter Notebooks (.ipynb)

- Code cells become fenced code blocks.
- Markdown cells become regular Markdown.
- Output cells are included (text only; rich output may be simplified).

## ZIP Archives (.zip)

- Contents are extracted and each supported file is converted.
- Output is concatenated Markdown with separators per file.

**Tip:** For large archives, extract manually and use batch mode (`--dir`) for more control.

## JSON / XML

- Pretty-printed and wrapped in code blocks.
- Structure is preserved.

## Plain Text (.txt, .rtf, .yaml, .yml)

- Pass-through with minimal formatting.
- RTF is converted to plain text Markdown.
