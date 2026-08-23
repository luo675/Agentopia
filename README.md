# Agentopia on a Consumer GPU

This repository contains a reduced-scale, long-horizon port of Agentopia for a single consumer GPU. The tested configuration uses five active agents, one apartment world, Qwen3-8B-AWQ, vLLM, and an RTX 5070 Ti with 12 GB VRAM.

The project is an exploratory systems study. It is not a same-scale reproduction of the original 100-agent, 10-year system, and it is not a controlled comparison between the original model and Qwen3-8B.

## Current Evidence

- Three full-system restarts completed 52, 52, and 50 weeks.
- The runs cover 154 system-weeks and 770 agent-weeks.
- Finalized activity logs contain 13,084 records; 1,335 are flagged `NO_RESPONSE` records (10.20% pooled).
- No threshold-based health warning or death was recorded in the tested runs.
- The memory-off run establishes an implementation dependency for L2/L3 artifacts, not a causal effect on downstream behavior.
- A separate 10-week M versus M+T comparison describes a trade-off among activity volume, lexical reuse, and missing fields; it is not a causal diversity result.

See the paper source for the complete scope, measurement definitions, and limitations.

## Repository Layout

```text
Agentopia-paper/
|-- src/                    Simulation and agent implementation
|-- scripts/                Runtime and metric scripts
|-- data/                   Local initial world/persona data (Git-ignored)
|-- data-samples/           Lightweight data index only
|-- docs/                   Reproduction, data, and paper instructions
|-- paper/                  LaTeX source, figures, analyses, and literature data
|-- 实验数据/                Full local experiment outputs (Git-ignored)
|-- configs/                Sanitized reported-run configuration and provenance
|-- config.example.json     Safer 10-week new-run configuration
|-- config.json             Local configuration (Git-ignored)
`-- requirements.txt
```

The complete raw experiment data and generated paper artifacts remain local. They are intentionally excluded from Git because of size, credentials, and release-policy constraints.

## Quick Start

Create a local configuration and install the Python dependencies:

```bash
cp config.example.json config.json
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Start an OpenAI-compatible vLLM server in one terminal:

```bash
vllm serve ~/models/Qwen3-8B-AWQ \
  --served-model-name Qwen/Qwen3-8B-AWQ \
  --port 8000 \
  --gpu-memory-utilization 0.85 \
  --max-model-len 24576 \
  --enforce-eager \
  --max-num-seqs 1 \
  --enable-auto-tool-choice \
  --tool-call-parser hermes
```

Run the 10-week example in another terminal:

```bash
python scripts/run_world.py --max-agents 5 --years 1 --weeks 10 --no-parallel
```

The root example is not the archived paper configuration. For the reported 52-week profile, the historical client/server context mismatch, and local-data requirements, read [`configs/README.md`](configs/README.md) and [`docs/reproducibility.md`](docs/reproducibility.md).

## Paper

The public preprint source is in [`paper/main.tex`](paper/main.tex), and the compiled PDF is in [`paper/Agentopia-consumer-gpu-preprint.pdf`](paper/Agentopia-consumer-gpu-preprint.pdf). Build instructions and artifact locations are documented in [`docs/paper-build.md`](docs/paper-build.md). Raw-data layout and audit outputs are documented in [`docs/data-layout.md`](docs/data-layout.md).

## Upstream

The implementation is based on **Agentopia: Long-Term Life Simulation and Learning in Agent Societies** (arXiv:2606.07513). Translated upstream README files are retained in [`docs/upstream/`](docs/upstream/).

## License and Release Status

This repository is a public fork of [`Neph0s/Agentopia`](https://github.com/Neph0s/Agentopia), and the GitHub fork relationship preserves the upstream project link and attribution. The upstream README states that Agentopia is released under the MIT License. This branch documents the consumer-GPU port and its local modifications; it does not claim original authorship of the upstream implementation.

Raw initial data and the 17.6 GB experiment archive also have unresolved redistribution provenance and are excluded from Git. Model weights, credentials, caches, and local configurations are never part of the release bundle.

The evidence and release boundaries are recorded in [`docs/license-and-release-audit.md`](docs/license-and-release-audit.md). Public materials are limited to the forked implementation and local modifications, sanitized configurations, manuscript files, reviewed derived tables, analysis scripts, and aggregate figure data. Raw experiment archives, initial persona data, credentials, model weights, and machine-specific configuration remain excluded.
