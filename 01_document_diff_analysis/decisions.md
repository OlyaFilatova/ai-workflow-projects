- supported formats: HTML, MD, DOCX
- The project must NOT implement:
    * Visual formatting comparison (fonts, colors, layout, margins)
    * Screenshot or pixel-based comparison
    * PDF support
    * Embedded image similarity detection
    * OCR
    * Track changes / revision history diff
    * Full XML metadata diff
    * Semantic/NLP-based similarity detection
    * Move detection (reordering = remove + add)
    * Advanced table semantics (column reorder detection, style comparison)
    * Performance optimization for very large documents

- Strict code separation rules:
    * `model` contains only dataclasses.
    * `parsers` convert input → NDM.
    * `diff` operates only on NDM.
    * `renderers` operate only on `DiffResult`.
    * No circular imports.

- Normalized Document Model (NDM)
    * Document - ordered list of blocks

    * Block types: HeadingBlock, ParagraphBlock, ListBlock, TableBlock, ImageBlock
    * Rules:
        * Preserve order
        * Normalize whitespace
        * Normalize Unicode (NFC)
        * Strip noise in HTML
        * Stable deterministic block IDs
        * Fully JSON-serializable
        * Use Python dataclasses + type hints

- Adding a new format must require:
    * Adding new parser file
    * Registering it

- Diff strategy - Two-stage hierarchical diff: Block and word levels
    * Granularity
        * "block"
        * "block+word" (default)
        * "word"
    * Tables - No column reorder detection

- Implement `TextRenderer`:
    * `+` added
    * `-` removed
    * `~` modified
    * Rendering must be separate from diff logic.

- Testing Strategy
    * Use pytest.
    * Tests must cover:
        * Model serialization
        * Parser correctness (each format)
        * Block diff
        * Word diff
        * Table diff
        * Renderer output. Must cover all variants, ex.: added, removed, modified, equal.
        * Cross-format diff (e.g., Markdown vs HTML equivalent content)
    * diff tests must cover all variants, ex.: added, removed, modified, equal.
    * Tests must use realistic multi-paragraph content.
    * DOCX fixtures may be generated programmatically in tests.

- Use `pyproject.toml` (PEP 621).

- Requirements:

    * Python >= 3.11
    * Dependencies:

    * python-docx
    * beautifulsoup4
    * markdown-it-py
    * Dev dependencies:
    * pytest

- Do NOT add CLI entrypoint.

- README must include:

    * Overview
    * Supported formats
    * Explicit exclusions
    * Architecture explanation
    * NDM description
    * Diff strategy explanation
    * Usage examples
    * Limitations per format
    * Testing instructions
    * Extending instructions

- Documentation must not overclaim capabilities.

- Code Quality Requirements
    * Python 3.11+
    * Full type hints
    * Dataclasses for data models
    * Clear docstrings for public classes/functions
    * No unused imports
    * Deterministic behavior
    * No global state
    * Follows PEP-8