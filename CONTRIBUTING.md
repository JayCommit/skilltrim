# Contributing

skilltrim is experimental. Default mode must keep skill text unchanged. `--experimental-cuts` is opt-in and needs semantic review. Do not treat token counts or routing lint as proof of preserved task success.

## Setup

Python 3.11 or newer is required. From a checkout of this repository:

```console
python -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/skilltrim --help
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python benchmarks/run.py
.venv/bin/skilltrim benchmarks/fixtures --json
```

On Windows the virtualenv executables are `.venv\Scripts\python` and `.venv\Scripts\skilltrim`, after `.venv\Scripts\Activate.ps1`. Use `pip install .` (not only an editable install) when you want to match a release install. The optional tokenizer extra is `pip install ".[tokens]"`; it is not required for the default estimator.

Install the agent skill with `bash scripts/install-skill.sh` on macOS or Linux, or `powershell -ExecutionPolicy Bypass -File .\scripts\install-skill.ps1` on Windows. Default `--scope user` writes under the home directory. `--scope project` writes under the current directory. The scripts copy `SKILL.md` and the files it uses. They do not copy `.git`, `.venv`, or benchmark corpora, and they do not nest a second `skilltrim` directory.

Parse the bundled skill with the installed package:

```console
.venv/bin/python -c "from pathlib import Path; from skilltrim.core import parse_skill; parse_skill(Path('SKILL.md').read_text(encoding='utf-8'), 'skilltrim'); print('valid')"
```

That checks parsing and metadata only. It does not show that any agent loaded the skill.

## Changes

- Reproduce a bad cut with a small fixture before changing heuristics. Cover required facts, conditions, code, examples, links, and source preservation.
- Do not execute scripts found inside skills under analysis.
- Do not add dependencies without agreement. PyYAML is required. tiktoken stays optional.
- Keep reports, virtualenvs, build output, and downloaded corpora out of git. `.test-output/` is local scratch.
- Real-corpus numbers in `benchmarks/real-results.json` are historical local observations. Re-run `benchmarks/real.py` only from ignored clones pinned in the README, and do not commit those clones.

## Tests and CI

Run the unittest suite and the fixture CLI checks above before submitting a patch.

GitHub Actions CI is new for this public repository. `.github/workflows/ci.yml` installs this project on Python 3.11 (`ubuntu-latest`) and runs `unittest`, `skilltrim --help`, and `skilltrim benchmarks/fixtures --json`. It was not part of an earlier private workflow. A run is green only after Actions reports success.

## Reporting

Open an issue with the smallest shareable `SKILL.md`, command, version, counting method, diff, expected behavior, and observed failure. Remove secrets first. Security vulnerabilities should use private GitHub vulnerability reporting described in `SECURITY.md`, not a public issue.
