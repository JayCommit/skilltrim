# Working on skilltrim

skilltrim is an experimental Python CLI and agent skill for reviewing Agent Skills. Default analysis preserves all text; `--experimental-cuts` opts into unverified heuristic deletions. Savings and routing lint do not establish task effectiveness.

## Layout

- `src/skilltrim/core.py`: YAML validation, Markdown heuristics, counting, routing lint.
- `src/skilltrim/cli.py`: input validation, preview, reports, staged collection export.
- `scripts/skilltrim.py`: entrypoint using bundled `src`, without package installation.
- `scripts/install-skill.sh` and `scripts/install-skill.ps1`: copy `SKILL.md` and the files it uses into a host folder named `skilltrim`. They do not copy `.git`, `.venv`, or benchmark corpora, and they do not nest `skilltrim/skilltrim`. macOS/Linux uses the shell script; Windows uses the PowerShell script.
- `SKILL.md`: agent entrypoint; `benchmarks/README.md`: on-demand evaluation guidance.
- `tests/`: unittest regression suite. `benchmarks/`: synthetic fixtures and pinned real-corpus evidence.
- `.test-output/`: ignored scratch files and downloaded corpora; never publish this directory.

## Development

Run from this directory. macOS and Linux:

```console
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
python -m unittest discover -s tests -v
skilltrim --help
python benchmarks/run.py
skilltrim benchmarks/fixtures --json
bash -n scripts/install-skill.sh
```

Windows, from the same checkout:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install .
python -m unittest discover -s tests -v
skilltrim --help
python benchmarks/run.py
skilltrim benchmarks/fixtures --json
```

Install the agent skill with `bash scripts/install-skill.sh` (macOS/Linux) or `powershell -ExecutionPolicy Bypass -File .\scripts\install-skill.ps1` (Windows). Do not describe either script as having been executed on macOS or Windows unless that run actually happened.

No project linter is configured. `.github/workflows/ci.yml` is new for this public repository: on Python 3.11 and `ubuntu-latest` it installs the project and runs unittest, `skilltrim --help`, and `skilltrim benchmarks/fixtures --json`. Do not describe that workflow as older than the public repository, and do not call a run green until Actions finishes. To validate the bundled skill using existing code, from the activated environment:

```console
python -c "from pathlib import Path; from skilltrim.core import parse_skill; parse_skill(Path('SKILL.md').read_text(encoding='utf-8'), 'skilltrim'); print('valid')"
```

This validates parsing and metadata, not host discovery or agent behavior. Reproduce real-corpus results using the pinned clone commands in `README.md`, then run `benchmarks/real.py` (paths are anchored to this repository, not the current working directory).

## Constraints

Keep all work self-contained here; do not depend on parent-repository files or absolute local paths. Prefer explicit Python and the existing standard-library unittest suite. Do not add dependencies without maintainer agreement; PyYAML is required and tiktoken is optional.

Preserve source immutability, new destination requirements, frontmatter, companion resources, and review-only defaults. Never execute input skill scripts during analysis. Export copies the entire source tree: tests must use scoped fixtures, not secret-bearing directories. Concurrent source mutation is unsupported.

Preserve progressive disclosure: concise entrypoint instructions, linked optional reference detail, functioning relative links. There is no enforced token budget; do not invent one or optimize toward a promised savings quota. Estimated counts are UTF-8 bytes/4 rounded up per skill; exact counts name their encoding. Neither count includes agent wrappers or optional resource loading.

Do not expand scope into marketplaces, automatic description rewrites, destructive overwrite, or automatic adoption of experimental cuts. Do not claim two-agent compatibility, routing improvements, or preserved effectiveness without recorded behavioral evidence. Update documentation and evidence when behavior changes; do not silently reuse obsolete baselines.

## Before committing

Run the tests and checks above. For transformations, add regression coverage for required domain facts, conditions, code/examples, links, and source preservation. Preview both default and experimental modes; inspect diffs and reasons, then export into a fresh scratch destination and reparse the output. Verify default output remains unchanged. Inspect `git diff` and staged files for secrets, machine paths, generated artifacts, accidental corpus redistribution, and changes outside this directory. `GO_LIVE.md` was a pre-publication checklist and is not part of the public tree; open limits remain in `RELEASE-AUDIT.md` and the README.
