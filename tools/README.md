# tools

Scripts that build this pay data and the Knackboard pay tracker pages. Kept here so a box cleanup cannot lose them again. A working copy lives in `/workspace/kb-seo-notes/build/` on the build box; edit both together.

None of these scripts commit, push, or POST anywhere except `micro1_feed.py`, which reads micro1's public feed.

| Script | What it does |
|---|---|
| `paytracker_refresh.py` | Full refresh: rechecks every source in `paydata/sources.json`, updates `state.json`, the change log, both CSVs, the tracker page, history, this mirror, and the Markdown twins. `--no-fetch --date YYYY-MM-DD` rebuilds without fetching. |
| `pt_fetch.py` | GET-only fetchers for DataAnnotation, Handshake AI, and Mercor listing pages, plus micro1 pay wording (`Pay: $X-Y/h`). |
| `micro1_feed.py OUT.json` | Saves micro1's public expert feed (the data behind https://www.micro1.ai/experts/opportunities) with a direct POST to `prod-api.micro1.ai/api/v1/job/portal`, paging until `total` is reached. Refuses partial captures. No browser. |
| `micro1_capture.py OUT.json` | Older capture that renders the public page headlessly (Playwright). Kept for reference; prefer `micro1_feed.py`. |
| `paydata_repo_build.py [mirror] [--src paydata]` | Writes this repo: CSVs, public change log, `charts/`, and the top-level README. Leaves `tools/` alone. |
| `paytracker_charts.py` | History CSV and the inline and standalone SVG range charts. |
| `md_build.py [repo]` | Knackboard `.md` twins, `X-Markdown-Tokens` in `_headers`, and `llms.txt` lists. |
| `add_micro1_row.py`, `recheck_micro1_field.py` | Add or recheck single micro1 rows in `sources.json` / `state.json`. |
| `livecheck.py SHA BASE` | Compares changed files on the live site with a commit after a deploy. |
| `payreport/make_report.py`, `payreport/recheck.py` | Monthly pay report builder and its recheck helper. |

Rules the scripts follow: listed rates only, in each platform's own wording, with the date checked. Ceilings are never shown as typical pay.

Run: `python3 tools/paytracker_refresh.py --repo <knackboard checkout>` in a fresh branch off the latest main. Tests in the site repo: `node --test tests/*.test.mjs`.
