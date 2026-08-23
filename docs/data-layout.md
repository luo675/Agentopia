# Data Layout

## Local Runtime Data

`data/` contains the initial apartment, school, and persona-template state used by the simulator. It currently contains 1,757 files and 4,307,381 bytes. No license, source manifest, or provenance README is present inside that directory. It remains local and Git-ignored pending both a redistribution-license decision and a content review of the persona narratives.

## Experiment Outputs

The complete local archive is stored under `实验数据/`:

```text
实验数据/
|-- 基线/    Baselines and the three full-system long runs
|-- 验证/    Mechanism-validation runs
`-- 消融/    Ablation and partial-ablation runs
```

Verified migration totals on 2026-08-03:

| Category | Files | Bytes |
|---|---:|---:|
| 基线 | 15,863 | 7,633,744,549 |
| 验证 | 9,971 | 1,738,968,124 |
| 消融 | 11,932 | 8,242,499,735 |
| **Total** | **37,766** | **17,615,212,408** |

The directory is excluded from Git. It contains generated trajectories as well as copies or descendants of the initial world/persona state, so local generation alone does not resolve the upstream-data question. `data-samples/` is only a lightweight index and must not be interpreted as a released benchmark or a complete reproduction package.

## Paper Analysis Data

Small, derived audit tables are stored under `paper/analysis/`. The current CSVs contain counts, flags, lengths, rates, and similarity scores rather than raw activity or memory text; they also contain no local filesystem paths or author-identity strings in the 2026-08-04 audit. These tables are the preferred data-release layer, subject to a final anonymous-artifact scan.

Literature-search metadata is stored under `paper/literature/`. It supports citation checking but is not experimental data; retain source URLs and do not present automatically fetched metadata as an independently licensed literature dataset.

Generated PDFs and submission bundles are stored under `paper/build/` and `paper/release/`; both directories are local and Git-ignored.

## Release Boundary

| Material | Current action |
|---|---|
| `paper/analysis/*.csv` and figure aggregate CSVs | Candidate for reviewed derived-data release |
| Manuscript source and locally authored figures | Submission package only until venue policy is confirmed |
| `data/` initial states | Hold: upstream license/provenance and content review unresolved |
| `实验数据/` raw outputs | Hold: 17.6 GB, inherits unresolved inputs, and requires content/privacy review |
| Model weights and caches | Never bundle; users obtain them separately |
| `config.json`, `.env*`, credentials | Never bundle |

See `docs/license-and-release-audit.md` for the evidence behind this boundary.
