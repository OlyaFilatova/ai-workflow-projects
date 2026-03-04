# Project Diagrams

## 1) System Architecture Overview
```mermaid
graph TD
    U[User / CLI] --> API[Public API\nSQLDumpQueryEngine]
    API --> DR[Dump Reader\n_read_path_or_text]
    DR --> P[Parser\nsplit_statements + parse_copy]
    P --> DT[Dialect Transformer\ntranslator + type mapper]
    DT --> L[Loader\nload_into_engine]
    L --> DB[(DuckDB Engine)]
    API --> DB
    DB --> API
    API --> U
```

## 2) Data Flow Diagram
```mermaid
flowchart TD
    A[SQL Dump File] --> B[Read text]
    B --> C[Parse / split statements]
    C --> D[Dialect transformation]
    D --> E[Load into DuckDB]
    E --> F[User query]
    F --> G[DuckDB execution]
    G --> H[Rows + columns result]
```

## 3) Dump Processing Pipeline
```mermaid
flowchart TD
    S1["Start load_dump(path_or_text)"] --> S2[Read file or treat as raw SQL]
    S2 --> S3[split_statements]
    S3 --> S4{Event type?}
    S4 -->|SQL| S5[translate_statement]
    S4 -->|COPY| S6[parse_copy_header + parse_copy_row]
    S5 --> S7{Skipped?}
    S7 -->|Yes| S8[Record warning + increment skipped]
    S7 -->|No| S9[Execute SQL / batch INSERTs]
    S6 --> S10[Batch executemany INSERTs]
    S9 --> S11[Update stats]
    S10 --> S11
    S8 --> S11
    S11 --> S12[Return LoadStats]
```

## 4) Class Diagram
```mermaid
classDiagram
    class SQLDumpQueryEngine {
      +load_dump(path_or_text) LoadStats
      +query(sql) QueryResult
    }

    class Engine {
      +execute(sql)
      +executemany(sql, rows)
      +query(sql) (columns, rows)
    }

    class StatementParser {
      +split_statements(text) ParseEvent[]
    }

    class DialectTranslator {
      +translate_statement(event) TranslationArtifact
    }

    class TypeMapper {
      +normalize_type_tokens(sql) str
      +apply_enum_fallback(sql) (sql,warnings)
      +apply_unknown_type_fallback(sql) (sql,warnings)
    }

    class DumpReader {
      +_read_path_or_text(path_or_text) str
    }

    class Loader {
      +load_into_engine(engine, text) LoadStats
    }

    class WarningCollector {
      +warn(code, message, line)
    }

    class ParseEvent
    class TranslationArtifact
    class LoadStats
    class QueryResult

    SQLDumpQueryEngine --> Engine
    SQLDumpQueryEngine ..> DumpReader
    SQLDumpQueryEngine --> Loader
    Loader --> StatementParser
    Loader --> DialectTranslator
    DialectTranslator --> TypeMapper
    Loader --> WarningCollector
    Loader --> LoadStats
    SQLDumpQueryEngine --> QueryResult
```

## 5) Sequence Diagram: Loading a Dump
```mermaid
sequenceDiagram
    participant User
    participant API as SQLDumpQueryEngine
    participant Reader as DumpReader
    participant Parser as StatementParser
    participant Trans as DialectTranslator
    participant Loader
    participant DB as DuckDB

    User->>API: load_dump(path_or_text)
    API->>Reader: _read_path_or_text(...)
    Reader-->>API: dump text
    API->>Loader: load_into_engine(engine, text)
    Loader->>Parser: split_statements(text)
    Parser-->>Loader: ParseEvents

    loop each event
      alt SQL event
        Loader->>Trans: translate_statement(event)
        Trans-->>Loader: TranslationArtifact
        alt executable
          Loader->>DB: execute(sql) / batched execute
        else skipped
          Loader-->>Loader: warning + skipped count
        end
      else COPY event
        Loader->>DB: executemany(...) in batches
      end
    end

    Loader-->>API: LoadStats
    API-->>User: LoadStats
```

## 6) Sequence Diagram: Executing a Query
```mermaid
sequenceDiagram
    participant User
    participant API as SQLDumpQueryEngine
    participant DB as DuckDB

    User->>API: query(sql)
    API->>DB: query(sql)
    DB-->>API: columns, rows
    API-->>User: QueryResult
```

## 7) SQL Statement Parsing State Machine
```mermaid
stateDiagram-v2
    [*] --> Idle
    Idle --> InSQL: non-whitespace
    InSQL --> InSingleQuote: '
    InSQL --> InDoubleQuote: "
    InSQL --> InBacktick: `
    InSQL --> InLineComment: -- or #
    InSQL --> InBlockComment: /*
    InSQL --> StatementComplete: ; outside quotes/comments

    InSingleQuote --> InSQL: closing '
    InDoubleQuote --> InSQL: closing "
    InBacktick --> InSQL: closing `
    InLineComment --> InSQL: newline
    InBlockComment --> InSQL: */

    Idle --> CopyHeader: line matches COPY ... FROM stdin;
    CopyHeader --> CopyRows
    CopyRows --> CopyRows: read row
    CopyRows --> StatementComplete: line == \\.

    StatementComplete --> Idle: emit ParseEvent
```

## 8) Dialect Translation Workflow
```mermaid
flowchart LR
    A[Input statement] --> B{Dialect?}
    B -->|MySQL| C[MySQL normalization\nbackticks/engine/options]
    B -->|PostgreSQL| D[Postgres normalization\nschema/casts cleanup]
    B -->|Generic| E[Pass-through]
    C --> F[Common type normalization]
    D --> F
    E --> F
    F --> G[ENUM fallback]
    G --> H[Unknown type fallback]
    H --> I[DuckDB-compatible SQL + warnings]
```

## 9) Type Mapping Flow
```mermaid
flowchart LR
    T1[Source SQL type] --> T2{Known explicit rule?}
    T2 -->|Yes| T3[Apply explicit mapping rules]
    T3 --> M1[TINYINT 1 to BOOLEAN]
    T3 --> M2[JSONB to JSON]
    T3 --> M3[SERIAL to INTEGER]
    T3 --> M4[BIGSERIAL to BIGINT]
    T3 --> M5[DATETIME to TIMESTAMP]
    T2 -->|No| T4{ENUM?}
    T4 -->|Yes| T5[Map ENUM to TEXT and emit lossy warning]
    T4 -->|No| T6[Fallback to TEXT and emit lossy warning]
    M1 --> T7[Emit normalized DuckDB type]
    M2 --> T7
    M3 --> T7
    M4 --> T7
    M5 --> T7
    T5 --> T7
    T6 --> T7
```

## 10) Error Handling Flowchart
```mermaid
flowchart TD
    E1[Start operation] --> E2{Phase?}
    E2 -->|Parsing| E3[ParseError]
    E2 -->|Translation/Load SQL| E4[LoadError with line + statement]
    E2 -->|Query| E5[QueryError with statement]
    E2 -->|Unsupported construct| E6[WarningEvent skipped_construct]
    E2 -->|Lossy mapping| E7[WarningEvent lossy_mapping]
    E3 --> E8[Return/raise structured error]
    E4 --> E8
    E5 --> E8
    E6 --> E9[Continue pipeline]
    E7 --> E9
```

## 11) Streaming File Processing Diagram
```mermaid
flowchart TD
    F1[Large dump input] --> F2[Incremental line scanning]
    F2 --> F3[Build statement/COPY chunks]
    F3 --> F4[Emit ParseEvent]
    F4 --> F5[Translate]
    F5 --> F6[Execute immediately]
    F6 --> F2
```

## 12) COPY Block Handling Flow
```mermaid
flowchart TD
    C1[Detect COPY FROM stdin header] --> C2[Capture rows until COPY terminator]
    C2 --> C3[Parse header table + columns]
    C3 --> C4[Decode row tokens]
    C4 --> C41[Handle NULL marker token]
    C4 --> C42[Handle escaped characters]
    C41 --> C5[Chunk rows into batches]
    C42 --> C5
    C5 --> C6[executemany INSERT into DuckDB]
    C6 --> C7[Update load stats]
```

## 13) Insert Loading Strategy Diagram
```mermaid
flowchart TD
    I1[Translated INSERT statement] --> I2{Multi-row VALUES?}
    I2 -->|No| I3[Single execute]
    I2 -->|Yes| I4[Split tuple groups safely]
    I4 --> I5[Batch tuples e.g. 500]
    I5 --> I6[Emit batched INSERT statements]
    I6 --> I7[Execute batch by batch]
```

## 14) Component Interaction for Dialect Modules
```mermaid
graph TD
    Core[Core Loader] --> Trans[Dialect Translator]
    Trans --> MySQL[MySQL normalizer]
    Trans --> PG[PostgreSQL normalizer]
    Trans --> Common[Common type mapper]
    SQLite[SQLite adapter out of scope] -.-> Trans
    Common --> Duck[(DuckDB SQL output)]
```

## 15) Test Architecture Diagram
```mermaid
flowchart TD
    FX[Fixtures\nmysqldump + pg_dump] --> LD[Engine load_dump]
    LD --> Q[Query execution]
    Q --> V[Validate rows/columns]
    LD --> W[Validate warnings/errors]
    V --> PASS[Test pass/fail]
    W --> PASS
```

## 16) Performance Optimization Flow
```mermaid
flowchart TD
    P1[Input dump] --> P2[Incremental parsing]
    P2 --> P3[Skip non-essential directives]
    P3 --> P4[Batch INSERT tuples]
    P3 --> P5[Batch COPY rows]
    P4 --> P6[DuckDB execution]
    P5 --> P6
    P6 --> P7[Lower overhead and better throughput]
```

## 17) API Usage Diagram
```mermaid
flowchart TD
    U1[User code] --> U2[Initialize engine and load dump]
    U2 --> U3[Execute SQL query]
    U3 --> U4[Receive query result]
```
