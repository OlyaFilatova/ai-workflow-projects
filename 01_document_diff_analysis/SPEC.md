# SPEC: Universal Document Diffing Library (Constrained v1)

## 1. Purpose
Build a Python library that compares documents across selected formats and produces readable, deterministic diffs.

## 2. Scope
### In scope
- Input formats: Markdown (`.md`), HTML (`.html`, `.htm`), DOCX (`.docx`)
- Core output: structured diff result + text rendering
- Granularity modes:
  - `block`
  - `block+word` (default)
  - `word`

### Explicitly out of scope
- PDF support
- Visual/layout comparison (fonts, colors, margins, pixel/screenshot diffs)
- Embedded image similarity
- OCR
- Track changes / revision history diff
- Full XML metadata diff
- Semantic/NLP similarity
- Move detection (reordering = remove + add)
- Advanced table semantics (e.g., column reorder detection)
- Performance optimization for very large files
- CLI entrypoint

## 3. Architecture
- `model`: dataclasses only (NDM and diff result types)
- `parsers`: convert source documents to NDM
- `diff`: compares NDM documents only
- `renderers`: consume `DiffResult` and produce output (text in v1)
- No circular imports
- Adding format support requires a new parser module and parser registration

## 4. Normalized Document Model (NDM)
### Document
- Ordered list of blocks

### Block types
- `HeadingBlock`
- `ParagraphBlock`
- `ListBlock`
- `TableBlock`
- `ImageBlock`

### NDM rules
- Preserve block order
- Normalize Unicode to NFC
- Normalize whitespace
- Strip HTML noise
- Deterministic, stable block IDs
- Fully JSON-serializable
- Full type hints

## 5. Diff Strategy
Two-stage hierarchical diff:
1. Block-level matching/classification
2. Word-level diff for modified textual blocks

Behavior rules:
- Adds/removes/modified/equal supported
- Reordering represented as remove + add
- Table diff limited to content comparison; no structural reorder heuristics

## 6. Rendering
Implement `TextRenderer` with markers:
- `+` added
- `-` removed
- `~` modified

Renderer must be separate from diff logic.

## 7. Packaging and Dependencies
- Python `>=3.11`
- `pyproject.toml` using PEP 621
- Runtime deps:
  - `python-docx`
  - `beautifulsoup4`
  - `markdown-it-py`
- Dev deps:
  - `pytest`

## 8. Quality Requirements
- Deterministic behavior
- No global mutable state
- PEP 8 style
- No unused imports
- Public API docstrings
- Clear module boundaries

## 9. Testing Requirements
Use `pytest` and cover:
- Model serialization
- Parser correctness for each supported format
- Block diff
- Word diff
- Table diff
- Renderer output for added/removed/modified/equal
- Cross-format equivalence (e.g., MD vs HTML same content)
- Realistic multi-paragraph fixtures
- Programmatically generated DOCX fixtures in tests

## 10. Documentation Requirements
README must include:
- Overview
- Supported formats
- Explicit exclusions
- Architecture explanation
- NDM description
- Diff strategy
- Usage examples
- Format-specific limitations
- Testing instructions
- Extension instructions

Documentation must not overclaim capabilities.

## 11. Non-goals and Delivery Strategy
- Prefer correctness and clear limits over broad but weak format support.
- Deliver a solid constrained core that can be extended incrementally.
