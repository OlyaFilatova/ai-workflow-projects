# docdiff

`docdiff` is a Python library for deterministic, human-readable document diffs across selected formats.

## Supported Formats
- Markdown (`.md`)
- HTML (`.html`, `.htm`)
- DOCX (`.docx`)

## Explicit Exclusions
The project currently does **not** implement:
- PDF support
- Visual/layout comparison (fonts, colors, margins)
- Screenshot/pixel comparison
- OCR
- Embedded image similarity comparison
- Track-changes/revision-history diff
- Full XML metadata diff
- Semantic/NLP similarity detection
- Move detection (reordering is represented as remove + add)
- Advanced table semantics such as column reorder detection
- CLI entrypoint

## Architecture
Project uses strict layer separation:
- `docdiff.model`: dataclasses only for NDM and diff output
- `docdiff.parsers`: source-specific parsing into NDM
- `docdiff.diff`: NDM-to-NDM comparison engine
- `docdiff.renderers`: rendering of diff results

## Normalized Document Model (NDM)
`Document` stores an ordered list of blocks:
- `HeadingBlock`
- `ParagraphBlock`
- `ListBlock`
- `TableBlock`
- `ImageBlock`

NDM behavior:
- Order-preserving
- Unicode NFC normalization (via parser normalization)
- Whitespace normalization
- Deterministic block IDs
- JSON-serializable dataclasses

## Diff Strategy
Two-stage hierarchical diff:
1. Block alignment and classification (`equal`, `added`, `removed`, `modified`)
2. Word-level token diff for modified blocks when granularity enables it

Supported granularity values:
- `block`
- `block+word` (default)
- `word`

## Usage Examples
```python
from docdiff.parsers import parse_markdown, parse_html, parse_docx_file
from docdiff.diff import diff_documents
from docdiff.renderers import render_text

before = parse_markdown("# Title\n\nOld paragraph")
after = parse_html("<h1>Title</h1><p>New paragraph</p>")
result = diff_documents(before, after, granularity="block+word")
print(render_text(result))
```

DOCX file parsing:
```python
from pathlib import Path
from docdiff.parsers import parse_docx_file

doc = parse_docx_file(Path("sample.docx"))
```

## Limitations by Format
- Markdown: parser targets common block patterns; advanced Markdown extensions are not fully modeled.
- HTML: content extraction is structural and text-focused; style/layout semantics are ignored.
- DOCX: list detection is best-effort based on paragraph styles; rich Word-specific constructs are not exhaustively represented.

## Testing
Run tests with:
```bash
pytest
```

Current tests cover:
- Model serialization
- Markdown, HTML, DOCX parsing
- Block/word/table diff behavior
- Text renderer output
- Integration flow and Markdown-vs-HTML equivalence

## Extending
To add a new format:
1. Add a parser module under `src/docdiff/parsers/`.
2. Convert source data to NDM blocks with deterministic ordering and IDs.
3. Export parser entrypoint in `src/docdiff/parsers/__init__.py`.
4. Add parser and cross-format tests.

Keep layer boundaries intact and avoid parser logic in diff/renderer layers.
