# skilltrim

Experimental review tool for Agent Skills. **Not yet verified for production use:** two-agent loading and task-success evaluations are outstanding. No effectiveness or typical savings claim is made.

## Install

Python 3.11+ is required. From a checkout of this folder:

```console
python -m venv .venv
.venv/Scripts/python -m pip install .
.venv/Scripts/skilltrim --help
```

On Unix use `.venv/bin/python` and `.venv/bin/skilltrim` instead.

## Review and export

```console
skilltrim path/to/skills --json --report review.json
skilltrim path/to/skills --experimental-cuts --diff
skilltrim path/to/skills --experimental-cuts --output optimized-skills --report export.json
```

Use the executable inside your virtual environment, or activate it first. Preview writes no skill files. Reports include original line ranges, candidate text, reasons, routing suggestions, and unified diffs. Default mode retains all text: narrative facts can be essential even without instruction words. `--experimental-cuts` enables the original heuristic deletions and requires semantic review. Export alone copies unchanged skills. There is no overwrite mode. Existing destinations and overlapping source/output trees are rejected. For one skill, retain its directory name in the output path.

Review each proposed deletion against the skill's tasks. Inspect exported files before installing them. Test representative tasks, including exceptions and permissions; revert cuts that alter behavior. Routing descriptions are suggestions only and are never automatically rewritten. Optional examples can be moved manually after checking links and behavior.

The bundled `SKILL.md` provides agent instructions. Copy the project folder under the name `skilltrim`; its scripts require its bundled `src` directory and PyYAML. Host discovery and invocation are not verified across agents.

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

Loading and following optimized skills in two real agents is **unverified**. Task-success preservation, routing improvements, and broad host compatibility are **unverified**. Public release remains experimental until those gates pass.

## Contribute or report a bad optimization

Open an issue with the smallest shareable SKILL.md, command, version, counting method, diff, expected behavior, and observed failure. Remove secrets first. Add a regression test demonstrating the lost requirement. Run the tests above before submitting a patch. Do not turn a savings observation into an effectiveness claim without paired task evidence.

MIT license covers project code; upstream benchmark material retains its upstream terms.
