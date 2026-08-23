# Reproducibility

## Validated Environment

- Windows 11 with WSL2 Ubuntu 22.04
- NVIDIA RTX 5070 Ti, 12 GB VRAM
- Qwen3-8B-AWQ (4-bit)
- vLLM 0.19.1
- One concurrent model request (`--max-num-seqs 1`)
- Effective server context limit: 24,576 tokens

The long runs were executed inside the WSL2 Linux filesystem. Keeping active simulation files under `~/agentopia` avoids the Windows-mounted filesystem overhead observed during long runs.

## Local Files

`config.json`, `data/`, and `实验数据/` are intentionally Git-ignored.

1. Create `config.json` from the root `config.example.json`.
2. Restore the initial world/persona data under `data/`.
3. Never commit API keys, tokens, model caches, or raw experiment data.

The current workstation has the required local `data/` directory. A clean clone is not fully runnable until that directory is restored; redistribution will be decided only after the upstream data license is confirmed.

## Configuration Profiles

- `config.example.json` is the recommended 10-week new-run configuration. It explicitly enables M/T/H, uses Role/God output budgets of 3,584/3,840 tokens, limits concurrency to one request, and aligns the client context with the 24,576-token vLLM server.
- `configs/reported-full-system.json` is a sanitized semantic snapshot of the three reported full-system archives. It preserves the archived 52-week settings and 28,672-token client context. Do not treat that client value as the server limit or as the recommended setting for a new run.
- `configs/README.md` records the exact sanitization, implicit-default handling, and differences between the two profiles.

The three archived full-system configs are identical after replacing their run-specific `world.data_dir`. The archived files omit `world.time.enable_24h`; the code defaults the missing key to `true`, and the reported snapshot makes that effective value explicit.

The reported client/server context mismatch is historical:

| Layer | Reported value |
|---|---:|
| Archived client `context_length` | 28,672 |
| vLLM `--max-model-len` | 24,576 |

The new-run example uses 24,576 at both layers. This prevents the client from budgeting requests above the server limit.

## Installation

Create the environment inside WSL/Linux so the pinned vLLM dependency is installed:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

The requirements file pins `vllm==0.19.1` on Linux, matching the validated environment. Model weights are not included in this repository and must be obtained separately under the model provider's terms.

## Runtime

Start vLLM:

```bash
export HF_HUB_OFFLINE=1
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

Run the 10-week new-run example:

```bash
source .venv/bin/activate
cp config.example.json config.json
python scripts/run_world.py --max-agents 5 --years 1 --weeks 10 --no-parallel
```

For a 52-week reproduction attempt, first read `configs/README.md`, then copy and edit the reported profile deliberately. A new run receives a generated `world.data_dir`; never resume or overwrite an archived directory by accident.

Before a fresh run, archive the existing apartment output instead of overwriting it. The runtime writes checkpoints and activity records into the local data tree.

## Validation

Use the metric scripts in `scripts/` for run-level checks. Paper-specific longitudinal audits and figure generation live in `paper/scripts/`; run each script with `--help` before use because its input and output paths are explicit.

The three reported full-system runs did not share a fixed global run-level seed. Treat them as independent stochastic restarts, not controlled-seed replications.

Before publishing an artifact, follow `docs/license-and-release-audit.md`. In particular, do not include `data/`, `实验数据/`, model weights, credentials, or Git history in an anonymous or public bundle until their release conditions are resolved.
