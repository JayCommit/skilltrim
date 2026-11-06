## Summary

## Scope

- [ ] Default mode still does not change skill text
- [ ] Experimental cuts, if touched, stay opt-in and were reviewed against required facts, conditions, code, examples, and links
- [ ] No new dependency (PyYAML remains required; tiktoken remains optional)
- [ ] No downloaded corpus, secrets, machine paths, or `.test-output` contents

## Checks

- [ ] `python -m unittest discover -s tests -v`
- [ ] `skilltrim --help`
- [ ] `skilltrim benchmarks/fixtures --json`

Note anything you could not run. Do not describe token savings or routing lint as preserved task success.
