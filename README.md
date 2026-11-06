# skilltrim

Experimental review tool for Agent Skills. **Not yet verified for production use:** two-agent loading and task-success evaluations are outstanding. No effectiveness or typical savings claim is made. Default mode preserves skill text. There is no PyPI release; install from a checkout.

## Install the CLI

Python 3.11+ is required. PyYAML is required. tiktoken stays optional. From a checkout of this folder:

### macOS and Linux

```console
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
skilltrim --help
```

### Windows

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install .
skilltrim --help
```

Use that activated environment for later commands. These steps are the documented install. This repository does not record a macOS or Windows run of them. `.github/workflows/ci.yml` is new for this public repository: on Python 3.11 and `ubuntu-latest` it installs the project and runs unittest, `skilltrim --help`, and `skilltrim benchmarks/fixtures --json`. A run is green only after Actions reports success.

## Install the agent skill

The destination folder is named `skilltrim` and contains `SKILL.md` directly. Do not nest `skilltrim/skilltrim`. The frontmatter `name` matches that folder. Antigravity requires `description`. The installer copies `SKILL.md`, the bundled CLI (`scripts/skilltrim.py` and `src/skilltrim`), `pyproject.toml`, `README.md`, `LICENSE`, and the linked reference `benchmarks/README.md`. It does not copy `.git`, `.venv`, or benchmark corpora.

Paths below are install locations. Invocation strings are host conventions, not evidence that an agent loaded the skill or that routing improved.

### macOS and Linux

```console
bash scripts/install-skill.sh
bash scripts/install-skill.sh --host cursor --scope project
```

### Windows

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install-skill.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\install-skill.ps1 --host cursor --scope project
```

`--host` is `grok`, `grok-bot`, `cursor`, `openai`, `antigravity`, `claude`, or `all` (default `all`). `--scope` is `user` (default) or `project`. User scope writes under the home directory. Project scope writes under the current directory.

### Grok

| Scope | Path |
| --- | --- |
| project | `.grok/skills/skilltrim/` |
| user | `~/.grok/skills/skilltrim/` |

Invoke `/skilltrim`.

### Grok Bot

On the bot computer, install the same `SKILL.md` to `~/.grok/skills/skilltrim/`. The script prints this paste-in prompt:

> Clone https://github.com/JayCommit/skilltrim and copy its agent skill into ~/.grok/skills/skilltrim/ on the bot computer. Copy SKILL.md plus the files that skill uses (bundled scripts/skilltrim.py, src/skilltrim, and linked references such as benchmarks/README.md). Do not copy .git, .venv, or benchmark corpora. Do not nest another skilltrim directory inside the destination; SKILL.md must sit directly at ~/.grok/skills/skilltrim/SKILL.md. Use the same SKILL.md from that repository. Invoke /skilltrim.

`--scope project` also copies into `.grok/skills/skilltrim/` in the current directory. Invoke `/skilltrim`.

### Cursor

| Scope | Path |
| --- | --- |
| project | `.cursor/skills/skilltrim/` |
| user | `~/.cursor/skills/skilltrim/` |

The skill `name` matches the folder name `skilltrim`. Invoke `/skilltrim`.

### OpenAI / ChatGPT app

| Scope | Path |
| --- | --- |
| project | `.agents/skills/skilltrim/` |
| user | `~/.agents/skills/skilltrim/` |

Zip the `skilltrim` folder (the directory that directly contains `SKILL.md`). In the ChatGPT app: Plugins → Skills → Add → Upload. In Codex, invoke `$skilltrim`.

### Antigravity

| Scope | Path |
| --- | --- |
| project | `.agents/skills/skilltrim/` (one `skills` level, not `skills/skills` and not `skilltrim/skilltrim`) |
| user | `~/.gemini/config/skills/skilltrim/` |
| CLI | `~/.gemini/antigravity-cli/skills/skilltrim/` |

Frontmatter `description` is required. Invoke `/skilltrim`.

### Claude

| Scope | Path |
| --- | --- |
| project | `.claude/skills/skilltrim/` |
| user | `~/.claude/skills/skilltrim/` |

Invoke `/skilltrim`.

## Review and export

```console
skilltrim path/to/skills --json --report review.json
skilltrim path/to/skills --experimental-cuts --diff
skilltrim path/to/skills --experimental-cuts --output optimized-skills --report export.json
```

Use the executable inside your virtual environment, or activate it first. Preview writes no skill files. Reports include original line ranges, candidate text, reasons, routing suggestions, and unified diffs. Default mode retains all text: narrative facts can be essential even without instruction words. `--experimental-cuts` enables the original heuristic deletions and requires semantic review. Export alone copies unchanged skills. There is no overwrite mode. Existing destinations and overlapping source/output trees are rejected. For one skill, retain its directory name in the output path.

Review each proposed deletion against the skill's tasks. Inspect exported files before installing them. Test representative tasks, including exceptions and permissions; revert cuts that alter behavior. Routing descriptions are suggestions only and are never automatically rewritten. Optional examples can be moved manually after checking links and behavior.

The bundled `SKILL.md` is the agent entrypoint. `scripts/skilltrim.py` needs the bundled `src` directory and PyYAML. Use the installer above rather than copying the repository tree: a full copy would include `.git`, `.venv`, and benchmark corpora, and copying the repository into an existing `skilltrim` folder nests a second `skilltrim` directory. Loading the installed skill in real agents is unverified.

## Token counts

Default counts are estimates: UTF-8 bytes divided by four, rounded up per skill. They exclude companion resources and agent wrappers. Encoding-specific counting is optional:

```console
python -m pip install ".[tokens]"
skilltrim path/to/skills --encoding cl100k_base --json
```

The tokenizer may download encoding data. Counts for one encoding are not universal model counts. The routing score is a four-check lint score, not selection accuracy.

## Evidence

```console
python -m unittest discover -s tests -v
python benchmarks/run.py
```

Install the package before running tests. Synthetic fixtures are transformation checks, not real-world performance evidence. The old synthetic compression baseline has been superseded: safe default mode now retains all content.

Real corpus results, rejected inputs, revisions, and SHA-256 hashes are recorded in `benchmarks/real-results.json`. These cover 20 Anthropic and 44 OpenAI skill files: 62 accepted, two rejected. Default output is unchanged for every accepted file. Experimental counts are recorded separately. Hashes are SHA-256 of the UTF-8 text after universal newline normalization, so they identify the LF git blobs at the pinned revisions rather than a CRLF working tree. `benchmarks/real-example.json` contains a real-source experimental before/after diff and estimated token counts; it is not an endorsed optimization or behavioral result.

Reproduce from this project root (network and Git required):

```console
git clone https://github.com/anthropics/skills.git .test-output/anthropic
git -C .test-output/anthropic checkout ca45fc496a3436251f191354091d557da31c15b5
git clone https://github.com/openai/skills.git .test-output/openai
git -C .test-output/openai checkout 49f948faa9258a0c61caceaf225e179651397431
python benchmarks/real.py
```

The corpus remains in ignored `.test-output`; it is not redistributed as project code. The runner compares frontmatter and text retention; it does not launch agents. The short experimental diff in `benchmarks/real-example.json` is an excerpt from `skills/brand-guidelines/SKILL.md` in [anthropics/skills](https://github.com/anthropics/skills) at commit `ca45fc496a3436251f191354091d557da31c15b5`. That skill is Copyright 2026 Anthropic, PBC and is licensed under the Apache License, Version 2.0 (http://www.apache.org/licenses/LICENSE-2.0; upstream `skills/brand-guidelines/LICENSE.txt`). The file published here is a unified diff of an experimental heuristic cut, not the original skill, not the upstream corpus, and not an endorsed optimization. Upstream benchmark material keeps its upstream terms. See `benchmarks/README.md` for the task-success evaluation protocol.

## Limitations

English keyword heuristics miss implicit requirements and can misclassify background facts. Experimental deletions can break intent. Default mode therefore makes no automatic cuts. YAML validation rejects malformed or nonconforming skills rather than repairing them; client extensions may differ. Only UTF-8 SKILL.md files are supported. Supporting files are copied unchanged. Symlinks and junctions are rejected. Inputs must be stable during export; concurrent mutation is unsupported. Export copies the entire supplied tree, so select a skill collection rather than a repository containing secrets. No input scripts are executed by the analyzer.

Loading and following optimized skills in two real agents is **unverified**. Task-success preservation, routing improvements, and broad host compatibility are **unverified**. macOS and Windows install commands are documented above and were not part of the recorded release run. Public release remains experimental until those gates pass. There is no PyPI package.

## Contribute or report a bad optimization

Open an issue with the smallest shareable SKILL.md, command, version, counting method, diff, expected behavior, and observed failure. Remove secrets first. Add a regression test demonstrating the lost requirement. Run the tests above before submitting a patch. Do not turn a savings observation into an effectiveness claim without paired task evidence.

MIT license covers project code; upstream benchmark material retains its upstream terms.
