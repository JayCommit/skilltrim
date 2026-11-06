# Release audit

Found: narrative headings and greeting prefixes could trigger deletion of essential facts; duplicate prose can encode ordering; routing lint is not routing accuracy; synthetic savings were not behavioral evidence; real agents had not been exercised.

Changed: all heuristic deletions are review-only by default. Experimental mode explicitly opts into the previous behavior. Added domain-fact retention regression. Findings and reasons are visible in terminal output. Added real corpus hashes, counts, errors, and a reproducible experimental example. Added MIT license and skeptical documentation.

Remaining gates: two real agents must load exports and complete paired tasks; experimental cuts require semantic review. Stable inputs are required during copying. Exact tokenizer integration was previously checked with a test double, not every supported runtime. No claim of production readiness is made.

## 2026-11-06 verification

Local Linux check before the public v0.0.1 commit. Python 3.11.2. Package version is 0.0.1 in `pyproject.toml` and `skilltrim.__version__` (the earlier 0.1.0 suggestion was not used). No tests asserted the old version. Install was a fresh virtualenv and `pip install .`, not only an editable install.

Commands and results:

- `skilltrim --help` exited 0 and described preview-by-default behavior.
- `python -m unittest discover -s tests -v`: 25 tests, OK.
- `python benchmarks/run.py` matched `benchmarks/baseline.json` exactly. Default-mode synthetic totals remain 0% mean and 0% weighted reduction (98, 157, and 438 tokens, all unchanged). That baseline was not replaced with an experimental-cut headline.
- `skilltrim benchmarks/fixtures --json`: version 0.0.1, estimated counter, 693 → 693 tokens, no removals.
- `skilltrim benchmarks/fixtures --experimental-cuts --diff`: preview only. Experimental mode on these fixtures was 693 → 366 estimated tokens. That figure is not a default-mode result and is not a task-success claim.
- Default export to a new directory matched the fixture bytes. A second export to that existing path was rejected (exit 2). Fixture SHA-256 values were unchanged by the run.
- Experimental export rewrote only `verbose-csv/SKILL.md`. Reports were left in ignored scratch output.
- `parse_skill` on `SKILL.md` with folder name `skilltrim` printed `valid`.

Pinned corpus clones are small public repositories and were re-run from this root with `benchmarks/real.py` at `anthropics/skills` `ca45fc496a3436251f191354091d557da31c15b5` (20 `SKILL.md` files, 2 rejected) and `openai/skills` `49f948faa9258a0c61caceaf225e179651397431` (44 files, 0 rejected). Revisions, accept/reject errors, review-item counts, and before/default/experimental token counts matched the historical file for all 64 inputs. Default output was unchanged for every accepted file. The corpora were not committed.

SHA-256 values differed and were investigated before editing them. All 64 historical digests are the SHA-256 of a CRLF translation of the LF git blobs; none matched the blobs. Token counts matched because analysis reads text with universal newlines. Published digests are now the SHA-256 of that newline-normalized UTF-8 text, which on this Linux checkout equals the git blob bytes. Counts were not changed. `benchmarks/real-example.json` uses the same LF digest for `skills/brand-guidelines/SKILL.md` and records the previous CRLF digest in its attribution note. That excerpt remains a candidate diff under the upstream Apache License 2.0, not an endorsed optimization.

Optional `.[tokens]` was installed here (tiktoken 0.14.0). `skilltrim benchmarks/fixtures --encoding cl100k_base --json` succeeded and still preserved text (508 → 508). It is not part of the required install. No encoding download was separately confirmed.

Not run, so not claimed: Windows, two-agent loading, paired task success, routing accuracy, and PyPI publication. GitHub Actions CI is new for this public repository and was not described as green in this note.

## 2026-11-06 v0.0.2

Linux check for the v0.0.2 release. Python 3.11.2. User-facing version is 0.0.2 in `pyproject.toml` and `skilltrim.__version__`. `skilltrim --version` prints `skilltrim 0.0.2`. JSON reports use the same string. Tests assert that string so the two files cannot drift silently.

Commands and results:

- Fresh virtualenv and `pip install .` (not only an editable install).
- `python -m unittest discover -s tests -v`: 30 tests, OK. The previous suite had 25 tests. Added checks cover the 0.0.2 version string and the Unix skill installer (host paths, no nested `skilltrim` folder, no `.git` / `.venv` / benchmark corpora).
- `skilltrim --help` exited 0.
- `skilltrim benchmarks/fixtures --json`: version 0.0.2, estimated counter, 693 → 693 tokens, no removals. Default mode still preserves text.
- `python benchmarks/run.py` matched `benchmarks/baseline.json` exactly. That file was not edited.
- `bash -n scripts/install-skill.sh` exited 0. Installer behavior was exercised on this Linux host with a temporary `HOME`, not on macOS.

Not run, so not claimed: macOS, Windows (`scripts/install-skill.ps1` was not executed), two-agent loading, paired task success, routing accuracy, and PyPI publication. GitHub Actions CI is still the workflow added for the public repository. It was not described as green in this note.

`benchmarks/real.py` now resolves clone and result paths from the repository directory instead of the process working directory. The pinned corpora were not re-cloned for this release, and `benchmarks/real-results.json` was not rewritten.

