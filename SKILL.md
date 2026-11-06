---
name: skilltrim
description: Analyze and compress existing Agent Skills (SKILL.md), review token waste, and improve routing descriptions when optimizing a skill or skill collection before publishing or installing it.
---

# skilltrim

Requires Python 3.11+ and PyYAML 6. Optional tiktoken provides encoding-specific counts.

Run the bundled CLI from this skill folder: `python scripts/skilltrim.py TARGET --diff --report NEW_REPORT.json`. Install this folder with `python -m pip install .` if dependencies are missing. Target only existing Agent Skills.

Review findings and routing suggestions against each skill's intended tasks. Preserve permissions, stopping conditions, tool contracts, required examples, environment constraints, and local resource links. The analyzer is heuristic: even proposed automatic cuts need semantic review.

Default mode retains every paragraph. To preview unverified heuristic deletions, add `--experimental-cuts --diff`; review them before exporting. Two-agent behavioral effectiveness is unverified.

Export with `python scripts/skilltrim.py TARGET --output NEW_DIRECTORY`. The CLI preserves source files and copies supporting resources. Review the report's diffs before adopting the export.

For manual refinement, keep task-specific decisions in SKILL.md. Move long optional examples into linked references only when core instructions remain sufficient; keep paths valid. Rewrite descriptions around the actual capability and activation context without expanding scope. Do not remove guidance merely because it resembles a base prompt you have not inspected. Apply SMART where useful; do not invent deadlines or quotas.

Report the counting method, before/after counts, routing suggestions, and unresolved review items. Test representative tasks and skill selection before claiming equivalent effectiveness. Read [benchmark methodology](benchmarks/README.md) when designing those evaluations. Savings alone do not demonstrate preserved task success.
