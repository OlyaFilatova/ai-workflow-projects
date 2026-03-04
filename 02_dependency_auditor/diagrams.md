# auditpy Project Diagrams

## 1) High-level System Architecture
```mermaid
flowchart LR
    CLI[cli.py\nCLI entrypoint] --> CFG[config.py\nScanConfig]
    CLI --> PARSE[parsing.py\nrequirements parser]
    CLI --> RES[resolution.py\ndependency resolver]
    CLI --> VULN[vulnerabilities.py\nOSV analysis]
    CLI --> LIC[licenses.py\nlicense policy checks]
    CLI --> REP[reporting.py\nrenderers + exit checks]

    PARSE --> RES
    RES --> VULN
    RES --> LIC
    VULN --> REP
    LIC --> REP
    RES --> REP
```

## 2) End-to-End Execution Flow (`auditpy scan`)
```mermaid
flowchart TD
    A[auditpy scan -r requirements.txt] --> B[build_parser + argparse]
    B --> C[ScanConfig.create]
    C --> D[resolve_dependencies]
    D --> E{resolution.ok?}
    E -- no --> F[print runtime error\nreturn exit_code=2]
    E -- yes --> G[scan_vulnerabilities]
    G --> H[evaluate_licenses]
    H --> I[Build Report model]
    I --> J{--json provided?}
    J -- yes --> K[write_json_report]
    J -- no --> L[skip JSON write]
    K --> M[render_cli_summary + print warnings]
    L --> M
    M --> N{threshold_violated?}
    N -- yes --> O[return 1]
    N -- no --> P[return 0]
```

## 3) Dependency Resolution Workflow
```mermaid
flowchart TD
    A["resolve_dependencies(requirements.txt)"] --> B[parse_requirements]
    B --> C[Create temp dir]
    C --> D[_create_venv]
    D --> E[_venv_python]
    E --> F[_pip_install_requirements]
    F --> G[_collect_installed_distributions\nimportlib.metadata]
    G --> H[_build_edges + adjacency]
    H --> I[_build_paths]
    I --> J[ResolutionOutcome\nnodes/edges/paths/distributions]
```

## 4) Dependency Graph Model
```mermaid
graph LR
    R[requests==2.31.0] --> U[urllib3==2.2.0]
    R --> I[idna==3.7]
    R --> C[certifi==2024.x]
    U --> I

    classDef node fill:#eef,stroke:#446,stroke-width:1px;
    class R,U,I,C node;
```

## 5) Vulnerability Analysis Pipeline
```mermaid
flowchart TD
    A[Resolved PackageNode list] --> B[Build OSV batch queries]
    B --> C["Cache lookup (.auditpy_cache/osv_cache.json)"]
    C --> D{fresh cache?}
    D -- yes --> E[use cached vulns]
    D -- no --> F[OSV querybatch API call]
    F --> G[cache store/update]
    E --> H[normalize severity\nCVSS -> LOW/MEDIUM/HIGH/CRITICAL]
    G --> H
    H --> I[map findings to package + dependency paths]
```

## 6) License Analysis Pipeline
```mermaid
flowchart TD
    A["Resolved distributions\n(name/version/license/classifiers)"] --> B[Extract candidates]
    B --> C[Normalize to SPDX\nNORMALIZATION_MAP]
    C --> D{normalized set empty?}
    D -- yes --> E[policy_result=warn\nadd warning]
    D -- no --> F[evaluate policy\nno-gpl]
    F --> G[policy_result=allow/violation]
    E --> H[attach dependency paths]
    G --> H
    H --> I[LicenseFinding list]
```

## 7) Dependency Path Tracing Algorithm
```mermaid
flowchart TD
    A[Root requirement] --> B[Traverse adjacency graph]
    B --> C[Track path history]
    C --> D{neighbor already in path?}
    D -- yes --> E[skip cycle]
    D -- no --> F[extend path + continue]
    F --> G[record path for each reached package]
    G --> H[deduplicate + deterministic sort]
    H --> I[paths_by_target map: target -> list of paths]
```

## 8) Report Generation Flow
```mermaid
flowchart LR
    A[Vulnerability findings + License findings + graph] --> B[Report model]
    B --> C["Report.to_dict()"]
    C --> D[write_json_report\nJSON renderer]
    B --> E[render_cli_summary\ntext renderer]
```

## 9) CLI Command Handling
```mermaid
flowchart TD
    A["main(argv)"] --> B["build_parser()"]
    B --> C["parse_args()"]
    C --> D[scan subcommand selected]
    D --> E["_run_scan(args)"]
    E --> F["ScanConfig.create(policy, fail_on, ttl, verbose)"]
    F --> G[Pipeline execution\nresolve -> vuln -> license -> report]
    G --> H[threshold_violated + runtime checks]
    H --> I[exit code 0/1/2]
```

## 10) Exit Code Decision Flow
```mermaid
flowchart TD
    A[Report ready] --> B{resolution runtime error?}
    B -- yes --> C[Exit 2]
    B -- no --> D{vuln severity >= fail_on?}
    D -- yes --> E[Exit 1]
    D -- no --> F{license policy violation exists?}
    F -- yes --> E
    F -- no --> G[Exit 0]
```

## 11) OSV Caching Mechanism
```mermaid
flowchart TD
    A[Package name+version] --> B[cache key canonical==version]
    B --> C[Read osv_cache.json]
    C --> D{fresh entry within TTL?}
    D -- yes --> E[use cached vulns]
    D -- no --> F[POST /v1/querybatch]
    F --> G[store fetched_at + vulns]
    G --> H[use response for findings]
```

## 12) Error Handling and Failure Paths
```mermaid
flowchart TD
    A[Input requirements path] --> B{file exists?}
    B -- no --> C[ResolutionFailure runtime\nexit 2]
    B -- yes --> D[parse_requirements]
    D --> E{unsupported line?\neditable, VCS/URL, or invalid include}
    E -- yes --> C
    E -- no --> F[pip install in temp venv]
    F --> G{pip/install/metadata failure?}
    G -- yes --> C
    G -- no --> H[scan_vulnerabilities]
    H --> I{OSV failure/timeout?}
    I -- yes --> J[warning + fallback to cache]
    I -- no --> K[normal vulnerability findings]
    J --> L[evaluate licenses + reporting]
    K --> L
```

## 13) Project Module and Test Architecture
```mermaid
flowchart LR
    subgraph SRC[src/auditpy]
        MAIN[__main__.py]
        CLI[cli.py]
        CFG[config.py]
        PARSE[parsing.py]
        RES[resolution.py]
        VULN[vulnerabilities.py]
        LIC[licenses.py]
        REP[reporting.py]
        MOD[models.py]
    end

    MAIN --> CLI
    CLI --> CFG
    CLI --> RES
    CLI --> VULN
    CLI --> LIC
    CLI --> REP
    RES --> PARSE
    RES --> MOD
    VULN --> MOD
    LIC --> MOD
    REP --> MOD

    subgraph TESTS[tests]
        TPARSE[test_parsing.py]
        TRES[test_resolution.py]
        TVULN[test_vulnerabilities.py\nmock _query_osv_batch]
        TLIC[test_licenses.py]
        TREP[test_reporting.py]
        TCLI[test_cli_reporting.py]
        TCFG[test_config_and_cli_validation.py]
        TMOD[test_models.py]
    end

    TPARSE --> PARSE
    TRES --> RES
    TVULN --> VULN
    TLIC --> LIC
    TREP --> REP
    TCLI --> CLI
    TCFG --> CFG
    TMOD --> MOD
```
