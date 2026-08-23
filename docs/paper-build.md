# Paper Build

## Source Layout

- `paper/main.tex`: manuscript source
- `paper/custom.bib`: bibliography
- `paper/acl.sty`, `paper/acl_natbib.bst`: current ACL-style build files
- `paper/figures/`: editable and compiled figures
- `paper/scripts/`: audit and plotting scripts
- `paper/analysis/`: derived longitudinal-analysis tables
- `paper/literature/`: verified literature metadata and candidate BibTeX

The ACL style is the currently compiled working template. It is not evidence that the final workshop requires the ACL template; confirm the venue's official instructions before submission.

## Local Build

With Tectonic installed:

```bash
cd paper
tectonic main.tex --outdir build
```

The validated 2026-08-04 build is eight pages and is stored locally as `paper/build/main.pdf`. Build intermediates and PDFs are ignored by Git.

## Overleaf

The current local release bundle is `paper/release/Agentopia-Overleaf-20260804.zip`. It contains `main.tex`, `custom.bib`, the style files, and the two PDF figures with their expected `figures/` paths. The older 20260803 bundle is retained only as a previous snapshot.

Before submission, verify the compiled PDF page by page and confirm anonymity, venue template, page limit, appendix policy, and presentation requirements from the venue's official instructions.
