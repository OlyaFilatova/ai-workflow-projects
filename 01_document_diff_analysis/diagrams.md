# Project Diagrams

Note: diagrams marked `conceptual` include extension flows described by the project architecture/spec but not currently implemented as concrete modules/functions in `src/`.

## 1) High-Level Architecture
```mermaid
flowchart LR
    A[Input Sources<br/>Markdown/HTML/DOCX] --> B[Parsers]
    B --> C[NDM<br/>Document + Blocks]
    C --> D[Diff Engine<br/>diff_documents]
    D --> E[DiffResult<br/>DiffItem + WordDiff]
    E --> F[Renderers<br/>TextRenderer]
```

## 2) Folder/Module Dependency Boundaries
```mermaid
flowchart TB
    subgraph model["docdiff.model"]
      M1[types.py]
    end

    subgraph parsers["docdiff.parsers"]
      P0[__init__.py]
      P1[common.py]
      P2[markdown_parser.py]
      P3[html_parser.py]
      P4[docx_parser.py]
      PB[base.py]
    end

    subgraph diff["docdiff.diff"]
      D0[__init__.py]
      D1[engine.py]
    end

    subgraph renderers["docdiff.renderers"]
      R0[__init__.py]
      R1[text.py]
    end

    P2 --> M1
    P3 --> M1
    P4 --> M1
    PB --> M1
    D1 --> M1
    R1 --> M1
    P0 --> P2
    P0 --> P3
    P0 --> P4
    D0 --> D1
    R0 --> R1

    P2 --> P1
    P3 --> P1
    P4 --> P1
```

## 3) Parser Plugin Registry Flow (conceptual)
```mermaid
flowchart LR
    A["register_parser(ext, parser_fn)"] --> B[(Parser Registry)]
    C["parse_path(path)"] --> D[resolve extension]
    D --> B
    B --> E[get parser_fn]
    E --> F["parse_*_file(path)"]
    F --> G[Document]
```

## 4) Renderer Plugin Registry Flow (conceptual)
```mermaid
flowchart LR
    A["register_renderer(name, renderer)"] --> B[(Renderer Registry)]
    C["get_renderer(name)"] --> B
    B --> D[Renderer instance]
    D --> E["render(DiffResult)"]
    E --> F[Rendered Output]
```

## 5) Normalized Document Model Class Diagram
```mermaid
classDiagram
    class Document {
      +list[Block] blocks
      +str source_format
      +dict metadata
      +to_dict()
    }

    class HeadingBlock {
      +str block_id
      +int index
      +int level
      +str text
      +block_type='heading'
    }

    class ParagraphBlock {
      +str block_id
      +int index
      +str text
      +block_type='paragraph'
    }

    class ListBlock {
      +str block_id
      +int index
      +bool ordered
      +list[str] items
      +block_type='list'
    }

    class TableBlock {
      +str block_id
      +int index
      +list[str] header
      +list[list[str]] rows
      +block_type='table'
    }

    class ImageBlock {
      +str block_id
      +int index
      +str source
      +str alt_text
      +str caption
      +block_type='image'
    }

    Document --> HeadingBlock : blocks[]
    Document --> ParagraphBlock : blocks[]
    Document --> ListBlock : blocks[]
    Document --> TableBlock : blocks[]
    Document --> ImageBlock : blocks[]
```

## 6) Parsing Pipeline Sequence (per format)
```mermaid
sequenceDiagram
    participant Caller
    participant PlainText as PlainText Parser (conceptual)
    participant MD as parse_markdown
    participant HTML as parse_html
    participant DOCX as parse_docx_file
    participant Norm as normalize_text/make_block_id
    participant NDM as Document

    alt PlainText
      Caller->>PlainText: parse_text(...)
      PlainText->>Norm: normalize + split to paragraph blocks
      Norm-->>PlainText: normalized tokens/ids
      PlainText-->>NDM: Document(blocks, source_format='txt')
    else Markdown
      Caller->>MD: parse_markdown(text)
      MD->>Norm: headings/lists/tables/paragraphs normalization
      MD-->>NDM: Document(..., source_format='md')
    else HTML
      Caller->>HTML: parse_html(text)
      HTML->>Norm: strip noise + normalize extracted text
      HTML-->>NDM: Document(..., source_format='html')
    else DOCX
      Caller->>DOCX: parse_docx_file(path)
      DOCX->>Norm: style-based block extraction + normalization
      DOCX-->>NDM: Document(..., source_format='docx')
    end
```

## 7) Diff Engine Sequence Diagram
```mermaid
sequenceDiagram
    participant C as Caller
    participant E as diff_documents
    participant SM as SequenceMatcher
    participant WD as _word_diff
    participant R as DiffResult

    C->>E: diff_documents(before, after, granularity)
    E->>E: _block_signature() for all blocks
    E->>SM: SequenceMatcher(before_signatures, after_signatures)
    SM-->>E: block opcodes
    loop each opcode
      E->>E: classify equal/added/removed/replace
      alt replace and word granularity
        E->>WD: _word_diff(_block_text(before), _block_text(after))
        WD->>SM: SequenceMatcher(before_words, after_words)
        SM-->>WD: token opcodes
        WD-->>E: list[WordDiff]
      end
    end
    E-->>R: DiffResult(granularity, items)
```

## 8) Block Matching Logic Flowchart
```mermaid
flowchart TD
    A[Start diff_documents] --> B[Build block signatures]
    B --> C[SequenceMatcher on signatures]
    C --> D{Opcode tag}
    D -->|equal| E["Emit DiffItem(equal)"]
    D -->|delete| F["Emit DiffItem(removed)"]
    D -->|insert| G["Emit DiffItem(added)"]
    D -->|replace| H["zip_longest(before_slice, after_slice)"]
    H --> I{both blocks present?}
    I -->|yes| J["Emit DiffItem(modified)"]
    I -->|before only| F
    I -->|after only| G
    J --> K{granularity in block+word/word?}
    K -->|yes| L[Compute word_diffs from block text]
    K -->|no| M[No word_diffs]
```

## 9) Word Diff Algorithm Diagram
```mermaid
flowchart TD
    A[before_text, after_text] --> B["split() tokenization"]
    B --> C["SequenceMatcher(a=before_words,b=after_words)"]
    C --> D["get_opcodes()"]
    D --> E{opcode}
    E -->|equal| F["WordDiff(token, equal)"]
    E -->|delete| G["WordDiff(token, removed)"]
    E -->|insert| H["WordDiff(token, added)"]
    E -->|replace| I[removed tokens + added tokens]
```

## 10) Table Diff Hierarchy
```mermaid
flowchart TD
    A[TableBlock before/after] --> B["_block_text(table)"]
    B --> C[header join + row join]
    C --> D["_word_diff(combined_table_text)"]
    D --> E[DiffItem.word_diffs]
    E --> F[(Conceptual deeper hierarchy: row diffs -> cell diffs -> word diffs)]
```

## 11) List Diff Hierarchy
```mermaid
flowchart TD
    A[ListBlock before/after] --> B["_block_text(list)"]
    B --> C["join items with spaces"]
    C --> D["_word_diff(list_text)"]
    D --> E[DiffItem.word_diffs]
    E --> F[(Conceptual deeper hierarchy: item diffs -> nested block diffs)]
```

## 12) DiffResult Data Structure Diagram
```mermaid
classDiagram
    class DiffResult {
      +granularity: block|block+word|word
      +items: list[DiffItem]
      +to_dict()
    }

    class DiffItem {
      +change_type: added|removed|modified|equal
      +before: Block|None
      +after: Block|None
      +word_diffs: list[WordDiff]
    }

    class WordDiff {
      +token: str
      +change_type: added|removed|modified|equal
    }

    class Block

    DiffResult --> DiffItem : items[]
    DiffItem --> WordDiff : word_diffs[]
    DiffItem --> Block : before/after
```

## 13) Text Renderer Formatting Flow
```mermaid
flowchart TD
    A[DiffResult] --> B["TextRenderer.render()"]
    B --> C[Iterate DiffItem list]
    C --> D[Map marker + / - / ~ / =]
    D --> E["_block_summary(item)"]
    E --> F[Append main line]
    F --> G{modified and has word_diffs?}
    G -->|yes| H[Format token markers per WordDiff]
    G -->|no| I[Continue]
    H --> J[Join lines to output string]
    I --> J
```

## 14) Cross-Format Diff Example Sequence
```mermaid
sequenceDiagram
    participant User
    participant PM as parse_markdown
    participant PH as parse_html
    participant DE as diff_documents
    participant TR as render_text

    User->>PM: Markdown content
    PM-->>User: Document(source_format='md')
    User->>PH: HTML content
    PH-->>User: Document(source_format='html')
    User->>DE: diff_documents(md_doc, html_doc, granularity='block')
    DE-->>User: DiffResult(items all equal for equivalent content)
    User->>TR: render_text(DiffResult)
    TR-->>User: deterministic text report
```

## 15) End-to-End CLI Flow (conceptual)
```mermaid
flowchart TD
    A[CLI args] --> B["load_document(path) conceptual"]
    B --> C{extension}
    C -->|.md| D[parse_markdown_file]
    C -->|.html/.htm| E[parse_html_file]
    C -->|.docx| F[parse_docx_file]
    D --> G[Document before/after]
    E --> G
    F --> G
    G --> H["diff_documents(before, after, granularity)"]
    H --> I[get renderer by name conceptual]
    I --> J["TextRenderer.render(result)"]
    J --> K[stdout]
```
