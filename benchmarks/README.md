# Benchmarks

Run from the project root:

```console
python benchmarks/run.py
python benchmarks/run.py --encoding cl100k_base
```

`baseline.json` records the default offline estimator on three original synthetic fixtures: verbose narrative, an already lean skill, and a skill with operational background plus examples. The runner checks that their three CSV workflow contracts and frontmatter survive. These fixtures exercise the transformation, not agent behavior. They are deliberately small and are not evidence of typical savings or unchanged effectiveness. Both the per-skill mean and token-weighted reduction are reported so one verbose fixture cannot hide the distinction.

Real-world corpus analysis exists and is recorded in `real-results.json`, while behavioral effectiveness remains unmeasured; no task-success result or routing-accuracy improvement has been measured or published. The ≥40% mean reduction and unchanged task success remain product goals, not guarantees. Already concise skills should often stay unchanged.

To evaluate effectiveness before a release:

1. Collect a licensed, versioned skill corpus with representative sizes and domains. Record file hashes and selection criteria; avoid selecting only verbose skills.
2. Define task inputs, expected outputs, failure cases, permissions, and resource-link checks before optimization. Include tasks dependent on examples and background context.
3. Run original and optimized variants on the same agent/model versions, tool access, prompts, and seeds. Use multiple trials and a blinded rubric; report success counts and uncertainty, not just averages.
4. Test skill selection separately using matched requests and distractor skills. Report precision/recall and unnecessary activations before and after reviewed description edits.
5. Publish original and optimized hashes, exact tokenizer encoding, total and per-skill token counts, diffs, failures, human review decisions, and reproduction commands. Measure optional reference tokens on tasks that actually load those references.

Do not equate the routing lint score with observed selection accuracy or fixture contract retention with task success.
