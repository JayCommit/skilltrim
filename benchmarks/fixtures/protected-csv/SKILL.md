---
name: protected-csv
description: Extract CSV records into Markdown tables when preparing tabular reports.
---

# CSV records

## Background

The older parser requires UTF-8 input. Never replace malformed bytes silently.

## Workflow

Read the CSV with its declared encoding. Ask for the encoding if decoding fails.

Preserve quoted delimiters, embedded newlines, column order, and leading zeroes.

Return a Markdown table and the number of data rows. Never upload source records to external services.

## Examples

```csv
account,notes
0012,"hello, world"
```

The identifier remains 0012, including both leading zeroes.
