# Configuration Profiles

This directory separates the configuration used by the reported experiments from the configuration recommended for a new run.

## `reported-full-system.json`

This is a sanitized semantic snapshot of the three full-system archives:

- `T6-Run1-20260709-5ag-52wk`
- `T6-Run2-20260711-5ag-52wk`
- `T6-Run3-20260716-5ag-52wk`

After replacing each run-specific `world.data_dir`, the three archived JSON files are identical. The published snapshot changes only two presentation details:

1. `world.data_dir` is replaced with `apartment_REPLACE_WITH_NEW_RUN_ID` so a reader cannot accidentally target an archived run directory.
2. `world.time.enable_24h` is written explicitly as `true`. The archived files omit this key, and the implementation defaults the missing value to `true` in `src/world/world.py`.

The snapshot intentionally preserves the archived client-side `models.my-vllm-model.context_length` value of 28,672. The actual vLLM server used `--max-model-len 24576`; this client/server mismatch is part of the reported setup and helps explain the context boundary observed in Run 3. It is not recommended for a fresh run.

The full-system adaptation flags are:

| Module | Effective value |
|---|---|
| Layered memory (`world.memory.enable_layered`) | `true` |
| Four-block time (`world.time.enable_24h`) | `true` (implicit in the raw archives, explicit here) |
| Health (`world.health.enable`) | `true` |

The three runs are independent stochastic restarts. They do not share a fixed global run-level seed and must not be described as controlled-seed replications.

## Root `config.example.json`

The root example is a safer 10-week configuration for starting a new local run. It uses the same model, output-token budgets, adaptation flags, and single-request concurrency as the reported setup, but aligns the client context length with the 24,576-token server limit.

| Setting | Reported snapshot | New-run example |
|---|---:|---:|
| Weeks | 52 | 10 |
| Role output budget | 3,584 | 3,584 |
| God output budget | 3,840 | 3,840 |
| Client context length | 28,672 | 24,576 |
| vLLM server context | 24,576 | 24,576 |
| Max concurrency | 1 | 1 |
| M/T/H | on/on/on | on/on/on |

Copy the root example to the Git-ignored `config.json` for a new run. Do not copy the reported snapshot over an active or archived run without first changing `world.data_dir` and understanding the historical client/server mismatch.
