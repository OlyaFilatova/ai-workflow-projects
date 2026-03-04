# Diagrams

## 01_end_to_end_pipeline_flow

```mermaid
flowchart TD
    A[OpenAPI Spec\nJSON/YAML] --> B[Parser / Validator\nload_openapi_document]
    B --> C[$ref Resolver\nlocal refs + cycle detection]
    C --> D[IR Builder\nbuild_api_ir]
    D --> E[Code Generator\nJinja2 renderer]
    E --> F[Formatter / Linter\nquality_gates.sh\nruff + mypy + pytest]
    F --> G[Output Package\nmodels.py + client.py + __init__.py]
```

## 02_component_architecture

```mermaid
graph TD
    CLI[CLI\nopenapi_to_sdk.cli.main]
    PIPE[Pipeline\nopenapi_to_sdk.generator.pipeline]
    LOADER[Loader + Validator\nopenapi_to_sdk.parser.loader]
    RESOLVER["$ref Resolver\n(openapi_to_sdk.parser.loader internals)"]
    IR[IR + Type Mapper\nopenapi_to_sdk.ir.models + type_mapper]
    TEMPLATES[Templates\nopenapi_to_sdk.templates/*.j2]
    EMITTER[Emitters / Renderer\nopenapi_to_sdk.generator.renderer]
    FORMATTER[Formatter + Type/Lint/Test\nscripts/quality_gates.sh]
    RUNTIME[Runtime Clients\nopenapi_to_sdk.runtime.*]

    CLI --> PIPE
    PIPE --> LOADER
    LOADER --> RESOLVER
    PIPE --> IR
    IR --> EMITTER
    EMITTER --> TEMPLATES
    EMITTER --> RUNTIME
    PIPE --> FORMATTER
```

## 03_ir_data_model

```mermaid
classDiagram
    class ApiSpec {
      +title: str
      +version: str
      +paths: dict
      +components: dict
    }

    class Endpoint {
      +path: str
      +operations: Operation[*]
    }

    class Operation {
      +operation_id: str
      +python_name: str
      +method: str
      +path: str
      +parameters: Parameter[*]
      +request_body: RequestBody?
      +responses: Response[*]
      +auth_required: bool
    }

    class Parameter {
      +name: str
      +python_name: str
      +location: str
      +required: bool
      +type_hint: TypeRef
    }

    class Schema {
      +name: str
      +python_name: str
      +kind: str
      +type_hint: TypeRef
      +fields: Field[*]
    }

    class TypeRef {
      +python_type: str
      +nullable: bool
      +is_union: bool
    }

    class Model {
      +name: str
      +fields: Field[*]
      +config: ConfigDict
    }

    class Field {
      +name: str
      +python_name: str
      +type_hint: str
      +required: bool
      +alias: str?
    }

    ApiSpec "1" --> "*" Endpoint
    Endpoint "1" --> "*" Operation
    Operation "1" --> "*" Parameter
    Operation "1" --> "*" Schema : request/response refs
    Schema "1" --> "*" Field
    Field "1" --> "1" TypeRef
    Schema "1" --> "0..1" Model
```

## 04_ref_resolution_flowchart

```mermaid
flowchart TD
    A[See node with $ref?] -->|No| Z[Return node as-is]
    A -->|Yes| B{Remote ref?\nhttp/https}
    B -->|Yes| E[Fail\nOpenAPILoadError\nRemote refs unsupported]
    B -->|No| C[Split into file + fragment]
    C --> D[Resolve target file path]
    D --> F{In cache?}
    F -->|Yes| G[Use cached document]
    F -->|No| H[Load JSON/YAML file]
    H --> I[Store in cache]
    I --> G
    G --> J{"Cycle marker\n(file, pointer)"\nalready in stack?}
    J -->|Yes| K[Fail\nCircular $ref detected]
    J -->|No| L[Resolve JSON pointer]
    L --> M{Pointer valid?}
    M -->|No| N[Fail\nPointer resolution error]
    M -->|Yes| O[Recursively resolve nested refs]
    O --> P[Return resolved node]
```

## 05_schema_to_python_type_mapping

```mermaid
flowchart TD
    A[Schema Input] --> B{Has $ref?}
    B -->|Yes| R[Map ref -> Schema class name]
    B -->|No| C{Composition?\nallOf/oneOf/anyOf}

    C -->|allOf| D[Merge object-like parts\ncollect props+required]
    C -->|oneOf/anyOf| E[Map variants\nUnion via a or b]
    C -->|none| F{Type kind}

    F -->|string| G[str\nformat=date/datetime/uuid -> date/datetime/UUID]
    F -->|integer| H[int]
    F -->|number| I[float]
    F -->|boolean| J[bool]
    F -->|array| K[list of item_type]
    F -->|object| L[dictionary of string to value_type or model fields]
    F -->|enum| M[literal enum values]
    F -->|unknown| N[Any]

    D --> O[Apply nullable/optional rules]
    E --> O
    G --> O
    H --> O
    I --> O
    J --> O
    K --> O
    L --> O
    M --> O
    N --> O

    O --> P[Pydantic field rule\nrequired vs default None\nalias if python_name != original]
    R --> P
    P --> Q[Final Python type hint + field metadata]
```

## 06_composition_handling

```mermaid
flowchart TD
    A[Schema has composition] --> B{allOf?}
    B -->|Yes| C[Flatten object-like parts]
    C --> D{Any nested oneOf/anyOf/discriminator?}
    D -->|Yes| X[Unsupported\nraise UnsupportedSchemaError]
    D -->|No| E[Merge properties + required]

    B -->|No| F{oneOf / anyOf?}
    F -->|No| G[No composition handling needed]
    F -->|Yes| H{Has discriminator?}
    H -->|Yes| X
    H -->|No| I[Map each variant type]
    I --> J{Nested composition in variant?}
    J -->|Yes| X
    J -->|No| K[Deduplicate member types]
    K --> L{>= 2 unique types?}
    L -->|No| Y[Unsupported\nAmbiguous union]
    L -->|Yes| M[Return union type\nT1 or T2 or ...]

    E --> N[Supported output]
    M --> N
    G --> N
```

## 07_naming_normalization_flowchart

```mermaid
flowchart TD
    A[Raw Name Input] --> B{Context}

    B -->|operationId/path| C[to_snake_case]
    C --> C1[if missing operationId\nfallback method_path]
    C1 --> C2{collision in registry?}
    C2 -->|Yes| C3[append _2, _3...]
    C2 -->|No| C4[use name]

    B -->|schema name| D[to_pascal_case]
    D --> D1{collision in schema registry?}
    D1 -->|Yes| D2[append _2, _3...]
    D1 -->|No| D3[use class name]

    B -->|property name| E[to_snake_case]
    E --> E1{python keyword?}
    E1 -->|Yes| E2[append trailing _]
    E1 -->|No| E3[keep]
    E2 --> E4{changed from original?}
    E3 --> E4
    E4 -->|Yes| E5["set Field(alias=original)"]
    E4 -->|No| E6[no alias]
```

## 08_client_class_structure

```mermaid
classDiagram
    class BaseClient {
      +base_url: str
      +auth: AuthConfig
      +_build_url(path, path_params)
      +_build_query(query)
      +_build_headers(headers, bearer_token, api_key)
      +_build_request_kwargs(...)
      +_parse_success_response(response, response_model)
      +_raise_for_error(response, error_model)
    }

    class SyncClient {
      +request(...)
      +close()
    }

    class AsyncClient {
      +request(...)
      +aclose()
    }

    class Client {
      +generated endpoint methods
    }

    class GeneratedAsyncClient {
      +generated async endpoint methods
    }

    class AuthConfig {
      +api_key
      +api_key_name
      +api_key_in
      +bearer_token
    }

    class ErrorTypes {
      +ApiError
      +BadRequestError
      +UnauthorizedError
      +ForbiddenError
      +NotFoundError
      +ClientError
      +ServerError
      +TransportError
    }

    BaseClient <|-- SyncClient
    BaseClient <|-- AsyncClient
    SyncClient <|-- Client
    AsyncClient <|-- GeneratedAsyncClient
    BaseClient --> AuthConfig
    BaseClient --> ErrorTypes
```

## 09_request_building_sequence

```mermaid
sequenceDiagram
    participant SDK as SDK Method (Client.get_x)
    participant Core as BaseClient
    participant HTTP as httpx.Client/AsyncClient
    participant API as API Server

    SDK->>Core: request(method, path, params, headers, json)
    Core->>Core: _build_url(path, path_params)
    Core->>Core: _build_query(query)
    Core->>Core: _build_headers(auth defaults + overrides)
    Core->>HTTP: send request kwargs
    HTTP->>API: HTTP request
    API-->>HTTP: HTTP response
    HTTP-->>Core: response object
    Core-->>SDK: parsed success or raised error
```

## 10_response_parsing_error_sequence

```mermaid
sequenceDiagram
    participant Core as BaseClient
    participant Resp as httpx.Response
    participant Model as Response/Error Model
    participant Caller as SDK Caller

    Core->>Resp: check status_code
    alt 2xx success
        alt 204 or empty body
            Core-->>Caller: return None
        else JSON body
            Core->>Model: model_validate(payload) (if model)
            Core-->>Caller: return parsed model/value
        end
    else 4xx/5xx error
        Core->>Resp: inspect content-type/body
        alt JSON + error_model
            Core->>Model: model_validate(error_payload)
        else no typed model
            Core->>Core: keep raw body/json
        end
        Core->>Caller: raise typed ApiError subclass
    end
```

## 11_auth_injection_flowchart

```mermaid
flowchart TD
    A[Start request build] --> B[Read configured AuthConfig]
    B --> C[Read per-request overrides\nbearer_token/api_key]
    C --> D{Bearer available?}
    D -->|Yes| E[Set Authorization: Bearer <token>]
    D -->|No| F[Skip bearer header]
    E --> G
    F --> G
    G --> H{API key available?}
    H -->|No| I[Skip API key]
    H -->|Yes| J{api_key_in == header?}
    J -->|Yes| K[Inject header api_key_name: api_key]
    J -->|No| L[Current MVP: query injection deferred]
    K --> M[Merge caller headers]
    I --> M
    L --> M
    M --> N[Sort headers deterministically]
    N --> O[Final request kwargs]
```

## 12_pagination_helper_behavior

```mermaid
flowchart TD
    A[Pagination helper present?] -->|No| B[Current implementation\nNo generic pagination helper\nuse raw params manually]
    A -->|Yes| C[Initial request]
    C --> D[Parse next cursor/link]
    D --> E{Has next?}
    E -->|No| F[Stop iteration]
    E -->|Yes| G[Issue next request]
    G --> D

    subgraph SyncIterator [Sync iterator branch]
      C1["next()" loop] --> D1[yield items]
      D1 --> E1{next token?}
      E1 -->|Yes| C1
      E1 -->|No| F1[stop]
    end

    subgraph AsyncIterator [Async iterator branch]
      C2[async for loop] --> D2[await + yield items]
      D2 --> E2{next token?}
      E2 -->|Yes| C2
      E2 -->|No| F2[stop]
    end
```

## 13_generated_tests_architecture

```mermaid
graph TD
    GEN[Generator] --> TG[Generated/Project Tests]
    TG --> MOCK[Mock layer\nhttpx.MockTransport / respx]
    TG --> ASSERT[Assertions]

    ASSERT --> A1[URL/path interpolation]
    ASSERT --> A2[Headers/auth injection]
    ASSERT --> A3[Query/body serialization]
    ASSERT --> A4[Return type parsing]
    ASSERT --> A5[Error mapping]
    ASSERT --> A6[Deterministic output]
```

## 14_golden_file_regression_testing

```mermaid
flowchart LR
    A[Fixture OpenAPI Specs] --> B[Run generator]
    B --> C[Produced files]
    C --> D["Normalize output\n(order/whitespace)"]
    D --> E[Compare with golden snapshots]
    E -->|No diff| F[PASS]
    E -->|Diff found| G[FAIL + review]
```

## 15_release_ci_pipeline

```mermaid
flowchart LR
    A[Push / PR] --> B[Install deps]
    B --> C[Lint + Typecheck + Unit tests]
    C --> D[Generate sample SDK]
    D --> E[Run generated SDK tests/smoke]
    E --> F[Build package\nsdist + wheel]
    F --> G[Publish/Release candidate]
```

