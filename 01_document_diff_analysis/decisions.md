# Architectural and Scope Decisions

## Scope Control
- Chosen v1 formats: Markdown, HTML, DOCX.
- Explicitly excluded PDF, OCR, visual diffs, semantic similarity, CLI, and advanced table/move detection.
- Rationale: deliver a robust constrained core instead of broad shallow coverage.

## Data Model
- All core model objects are dataclasses in `docdiff.model`.
- NDM uses ordered block list with deterministic `block_id` and `index`.
- Rationale: deterministic behavior and simple serialization contracts.

## Parsing Strategy
- Each parser maps source documents directly into NDM.
- Shared normalization utility applies Unicode NFC and whitespace normalization.
- DOCX list support uses style-based best-effort classification.
- Rationale: maintain consistency across formats while acknowledging parser limitations.

## Diff Strategy
- Diff engine compares NDM only.
- Uses block-level sequence alignment plus optional word-level token diffs.
- Reordering is represented as remove + add (no move detection).
- Rationale: clear behavior aligned to constraints and easy to reason about in tests.

## Rendering
- `TextRenderer` consumes only `DiffResult`.
- Marker format:
  - `+` added
  - `-` removed
  - `~` modified
  - `=` equal
- Rationale: deterministic and human-readable output with minimal coupling.

## Quality and Testing
- Added tests for serialization, per-format parsing, diff behaviors, renderer output, and integration/cross-format scenarios.
- Fixtures use realistic multi-paragraph content and generated DOCX samples.
- Rationale: verify behavior by contract and reduce regression risk.

## Documentation Principle
- Documentation intentionally avoids overclaiming unsupported features.
- Known limitations are documented in README.
