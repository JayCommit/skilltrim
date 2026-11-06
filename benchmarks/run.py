"""Reproduce the checked-in synthetic compression baseline, offline by default."""

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from skilltrim.core import TokenCounter, optimize, parse_skill


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--encoding')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    counter = TokenCounter(args.encoding)
    rows = []
    for file in sorted((ROOT / 'benchmarks' / 'fixtures').glob('*/SKILL.md')):
        text = file.read_text(encoding='utf-8')
        optimized, report = optimize(parse_skill(text, file.parent.name), counter)
        # A narrow fixture contract, not a behavioral effectiveness evaluation.
        contracts = [
            'Read the CSV with its declared encoding. Ask for the encoding if decoding fails.',
            'Preserve quoted delimiters, embedded newlines, column order, and leading zeroes.',
            'Return a Markdown table and the number of data rows. Never upload source records to external services.',
        ]
        assert all(rule in optimized for rule in contracts), file
        assert parse_skill(optimized, file.parent.name).metadata == parse_skill(text).metadata
        rows.append({key: report[key] for key in ('name', 'before_tokens', 'after_tokens', 'reduction_percent')})
    before = sum(row['before_tokens'] for row in rows)
    after = sum(row['after_tokens'] for row in rows)
    result = {'corpus': 'three synthetic fixtures, not real-world effectiveness evidence',
              'token_counter': counter.label, 'skills': rows,
              'weighted_reduction_percent': round((before - after) / before * 100, 2),
              'mean_reduction_percent': round(sum(row['reduction_percent'] for row in rows) / len(rows), 2),
              'task_success_evaluated': False, 'routing_accuracy_evaluated': False}
    rendered = json.dumps(result, indent=2) + '\n'
    if args.output:
        args.output.write_text(rendered, encoding='utf-8')
    print(rendered, end='')


if __name__ == '__main__':
    main()
