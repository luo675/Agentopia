# License and Release Audit

Status: public-fork release audit, updated 2026-08-23. This document records operational release boundaries; it is not legal advice.

## Public-Fork Update (2026-08-23)

The repository owner confirmed that `luo675/Agentopia` is an existing GitHub fork of [`Neph0s/Agentopia`](https://github.com/Neph0s/Agentopia), rather than a new standalone code release. The upstream repository publicly states that Agentopia is released under the MIT License, and the GitHub fork relationship preserves the upstream link and attribution. The `paper` branch may therefore publish the consumer-GPU implementation changes and research materials while clearly retaining upstream authorship.

This update supersedes the earlier instruction below to withhold the complete source repository. It does not relax the data boundary: initial persona/world data, raw experiment archives, credentials, model weights, caches, and machine-specific configuration remain excluded.

## Scope and Method

The audit covers the current working tree, reachable local Git history, initial data, experiment outputs, paper assets, derived analysis tables, model/dependency references, and anonymous-release risks. It uses local evidence only; no online license lookup was performed.

## Findings

| Material | Local evidence | Current status |
|---|---|---|
| Simulation source (`src/`, `scripts/`) | `README-original.md` identifies `Neph0s/Agentopia` as the upstream source and states that the project is MIT-licensed. The repository owner confirms the public GitHub repository is a fork, so its upstream relationship remains visible even though this local clone has a short branch history. | **Publish on the existing fork only.** Preserve the upstream link and attribution, and describe the consumer-GPU work as local modifications rather than a newly authored standalone implementation. |
| Local modifications | The working tree contains source changes, but the current history is not sufficient to reconstruct per-file upstream/local authorship reliably. | Preserve upstream attribution; document local modifications without assigning unsupported ownership. |
| Root `config.json` | Git-ignored local file; may contain endpoint or runtime state and does not match the reported full-system flags/context. | Never release. Use the two reviewed profiles instead. |
| `config.example.json` | Sanitized new-run profile with local vLLM endpoint, no credential, explicit M/T/H flags, one-request concurrency, and matched 24,576-token client/server context. | Candidate for release after the source-code license blocker is resolved. |
| `configs/reported-full-system.json` | Sanitized semantic snapshot of the three normalized full-run archives. Run directory is replaced; implicit time default is made explicit; no secret is present. | Candidate for release with the paper artifact. Clearly retain the historical 28,672-client/24,576-server distinction. |
| Initial `data/` | 1,757 files; no license, source manifest, or provenance README was found inside the directory. Persona files contain extensive fictional biographical narratives, including sensitive themes. | **Do not redistribute.** Resolve upstream provenance and perform a content/safety review even if a code license is recovered. |
| Raw `实验数据/` | 37,766 files / 17,615,212,408 bytes. Locally generated outputs include copies or descendants of unresolved initial state and large volumes of model-generated narrative. | **Do not redistribute by default.** Prefer derived statistics; any raw subset needs provenance, content, privacy, and venue review. |
| `paper/analysis/*.csv` | The 2026-08-04 audit found only counts, flags, lengths, rates, and similarity scores; no raw activity/memory text, local path, email, author name, or institution string was found. | Best candidate for a derived-data release after one final anonymous scan. |
| Figure data and plots | Figure 1 was authored locally; Figure 2 and its aggregate CSV were generated from the local experiment archive. | Suitable for the manuscript package. Public licensing can be decided with the manuscript after venue policy is known. |
| Manuscript and bibliography | Locally written paper source plus bibliographic metadata. The current review PDF is anonymous. | Share through the submission/Overleaf package under venue policy; choose a public manuscript license only after policy confirmation. |
| `paper/acl_natbib.bst` | File header explicitly permits redistribution/modification under LPPL v1 or later and retains its notices. | May accompany the paper template with the header intact. |
| `paper/acl.sty` | Header identifies the official ACL style-file repository but contains no license notice in the local file. | Keep in the submission bundle as a template dependency; verify the authoritative style license before a general repository release. |
| Python dependencies | Listed in `requirements.txt`; not vendored. vLLM is pinned to 0.19.1 on Linux. | Users install dependencies separately under their respective licenses. Add verified notices only if vendoring occurs. |
| Qwen3-8B-AWQ weights | Referenced by name and local path only; weights are not in the repository. | Never bundle. Users obtain the model separately under the provider's terms. |
| Git remote/history | `origin` points to a personal GitHub account and commit metadata identifies the author. | Exclude `.git` and personal remote URLs from any double-blind artifact. Do not make the current remote public for review. |

## Release Boundary

### Safe to prepare now

- The anonymous manuscript/Overleaf package already used for submission preparation.
- Sanitized configuration profiles and their provenance notes.
- Reviewed derived audit tables that contain no raw narrative, local paths, or author identity.
- Reproduction instructions that reference, but do not bundle, the model and local raw data.

### Hold until conditions are resolved

- Initial world/persona data: wait for source/license documentation and content review.
- Raw experiment archives: wait for the initial-data decision plus raw-output content/privacy review.
- Public manuscript or figure licensing: wait for venue policy.
- ACL style files in a general code release: verify the authoritative `acl.sty` license; retain the LPPL notice in the `.bst` file.

### Never include

- `config.json`, `.env*`, credentials, API keys, caches, model weights, active run directories, or machine-specific paths.
- `.git`, personal remotes, commit identities, email exports, or non-anonymous submission correspondence in a double-blind artifact.

## Required Actions Before Public Release

1. Keep the GitHub fork relationship and upstream link visible; do not describe the upstream source as solely locally authored.
2. Add an exact upstream revision and standalone license/notice copy later if the upstream repository publishes one; do not synthesize missing copyright ownership.
3. Create a provenance manifest for every initial-data subtree (`apartment`, `school`, and persona templates), including source, creator, license, and whether redistribution is permitted.
4. Default to releasing derived audit tables rather than the 17.6 GB raw archive. If a raw subset is necessary, build it from a reviewed allowlist and scan narrative content.
5. Scan every public update for credentials, absolute local paths, and machine-specific configuration.

## Current Decision

Publish the implementation changes and research artifact on the existing GitHub fork's `paper` branch, with explicit upstream attribution. Do not add a synthesized license file or publish initial data, raw run archives, credentials, model weights, caches, or local configuration.
