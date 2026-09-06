# LICENSE_DECISION.md
### > **SUPERSEDED (23 Aug 2026):** the decision below was adopted. Final licenses now live in `LICENSE` (MIT, source code) and `LICENSE-CONTENT.md` (CC BY 4.0, research content); UCI data stays under its own CC BY 4.0 (`data/README.md`). This file is retained as the rationale record.
### Licensing recommendation for the public repository · 23 Aug 2026
### A bare `LICENSE` file is intentionally NOT committed yet — licensing is the author's decision and the repo mixes code, figures, a manuscript, and third-party data. Pick per component below, then add the files.

The repository has four kinds of content with different appropriate licenses. Applying one license to everything would be wrong (e.g., an MIT `LICENSE` at the root would appear to cover the manuscript and the UCI-derived material, which it should not).

| Component | What it is | Recommended license | Rationale |
|---|---|---|---|
| **Source code** (`src/`, `pilot/`, `tests/`, `reproduce.py`, runners) | The simulator, architecture, analysis, tests | **MIT** (or Apache-2.0) | Permissive, standard for research code; Apache-2.0 if you want an explicit patent grant. Put this `LICENSE` at repo root and reference it from `README`. |
| **Figures & manuscript** (`paper/`, generated PDFs/PNGs) | The paper text and figures | **CC BY 4.0** | Standard for written/creative research output; allows reuse with attribution. Note: on acceptance, the **final published version's copyright transfers to IEEE** (IEEE eCopyright at camera-ready) — so CC BY 4.0 applies to *your preprint/repo copy*, not the IEEE Xplore version. State this explicitly. |
| **Third-party data** (`data/raw/credit_default.*`, UCI 350) | UCI Default of Credit Card Clients | **Not yours to license — UCI CC BY 4.0** | Redistribution is permitted under CC BY 4.0 **with attribution to Yeh & Lien (2009)** and the UCI repository. Do not relicense. Prefer *not committing* the raw file (see below) and providing a download script + checksum instead. |
| **Pre-registrations & raw results** (`preregistration/`, `results/raw/`) | Frozen experimental record | **CC BY 4.0** or CC0 | These are factual records; CC BY 4.0 keeps attribution, CC0 maximizes reuse. Your call. |

## Recommended concrete choice (if you want a single quick decision)
- Add **`LICENSE`** = MIT at repo root (covers code).
- Add **`LICENSE-CONTENT`** = CC BY 4.0, and state in `README` that it governs the manuscript, figures, and raw results.
- Add a **`data/README.md`** stating the UCI dataset is CC BY 4.0 (Yeh & Lien 2009) and is **not** re-licensed by this repo.

## Dataset-committing recommendation (see also §Dataset policy in README)
`data/raw/credit_default.xls` (5.5 MB) and `credit_default.csv` (2.7 MB) are currently committed. Recommendation: **remove them from the packaged repo** and ship a small downloader + checksum instead (the UCI file is freely downloadable; committing an 8 MB copy is unnecessary and mixes third-party data into your license surface). A ready `.gitignore` excluding `data/raw/` has been added. If you prefer to keep the copy for convenience, that is permitted under CC BY 4.0 provided the attribution in `data/README.md` is present.

## Action required
Author to (1) confirm code license (MIT vs Apache-2.0), (2) confirm content license (CC BY 4.0), (3) decide whether to commit or gitignore the UCI raw file. Once confirmed, the `LICENSE`/`LICENSE-CONTENT`/`data/README.md` files can be added. **No license file is committed until you choose**, to avoid an incorrect blanket license.
