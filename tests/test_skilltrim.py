import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from skilltrim.cli import main
from skilltrim.core import SkillError, TokenCounter, optimize, parse_skill


HEADER = '---\nname: sample\ndescription: Extract records from CSV files when preparing a report.\nmetadata:\n  owner: "team"\nallowed-tools: Read\n---\n'


class CoreTests(unittest.TestCase):
    def transform(self, body):
        return optimize(parse_skill(HEADER + body, "sample"), TokenCounter(), experimental_cuts=True)

    def test_cuts_narrative_but_retains_operational_content(self):
        text, report = self.transform('# Background\n\nThis project began many years ago as an experiment in data analysis.\n\nNever send private records to external services.\n\n## Workflow\n\nRun `parse.py` and verify the schema.\n')
        self.assertNotIn("began many years", text)
        self.assertIn("Never send private records", text)
        self.assertIn("Run `parse.py`", text)
        self.assertTrue(report["saved_tokens"] > 0)
        self.assertTrue(text.startswith(HEADER))

    def test_fences_are_opaque_including_headings(self):
        for fence in ('```', '~~~~'):
            body = f'# Workflow\n\n{fence}text\n# History\nWelcome to this amazing product.\n{fence}\n\nRun the tool.\n'
            text, _ = self.transform(body)
            self.assertEqual(text, HEADER + body)

    def test_shorter_fence_does_not_close_longer_fence(self):
        body = '# Examples\n\n````text\n```\n# History\nWelcome to the tool.\n````\n'
        self.assertEqual(self.transform(body)[0], HEADER + body)

    def test_list_and_quote_fences_are_opaque(self):
        for opener, closer in [('- ```text', '  ```'), ('> ```text', '> ```')]:
            body = f'# Background\n\n{opener}\n\n# History\n\nWelcome to this product.\n\n{closer}\n'
            self.assertEqual(self.transform(body)[0], HEADER + body)

    def test_routing_reports_proposal_without_rewriting_metadata(self):
        header = HEADER.replace('Extract records from CSV files when preparing a report.', 'This skill helps you to extract CSV records when preparing reports.')
        text, report = optimize(parse_skill(header + '# Workflow\n\nRun the tool.\n', 'sample'), TokenCounter(), experimental_cuts=True)
        self.assertTrue(text.startswith(header))
        self.assertEqual(report['routing']['proposed_description'], 'Extract CSV records when preparing reports.')

    def test_exact_counter_handles_literal_special_tokens(self):
        class FakeEncoder:
            def encode(self, text, **kwargs):
                self.options = kwargs
                return [1, 2, 3]
        encoder = FakeEncoder()
        with patch.dict('sys.modules', {'tiktoken': type('Tokenizer', (), {'get_encoding': lambda name: encoder})}):
            counter = TokenCounter('example')
            self.assertEqual(counter.count('<|endoftext|>'), 3)
        self.assertEqual(encoder.options, {'disallowed_special': ()})

    def test_lists_links_tables_indentation_and_commands_are_preserved(self):
        body = '# Overview\n\n- Domain requirement: unique identifiers.\n\n[Guide](references/guide.md)\n\n| code | value |\n| a | b |\n\n    special command\n\n`tool --flag`\n'
        self.assertEqual(self.transform(body)[0], HEADER + body)

    def test_optional_examples_are_review_only(self):
        body = '# Examples\n\nAn illustrative account has ten records.\n'
        text, report = self.transform(body)
        self.assertEqual(text, HEADER + body)
        self.assertEqual(report['findings'][0]['action'], 'review')

    def test_generic_base_prompt_advice_is_not_blindly_removed(self):
        body = '# Rules\n\nAlways verify permissions before writing.\n\nBe clear and concise.\n'
        self.assertEqual(self.transform(body)[0], HEADER + body)

    def test_idempotence(self):
        text, _ = self.transform('# History\n\nThis began as a student experiment.\n\n# Workflow\n\nRun the tool.\n')
        again, _ = optimize(parse_skill(text, "sample"), TokenCounter(), experimental_cuts=True)
        self.assertEqual(text, again)

    def test_adjacent_duplicate_prose_only(self):
        text, _ = self.transform('# Notes\n\nA record represents an account.\n\nA record represents an account.\n\nRun the tool.\n\nRun the tool.\n')
        self.assertEqual(text.count('A record represents an account.'), 1)
        self.assertEqual(text.count('Run the tool.'), 2)

    def test_frontmatter_preserved_verbatim_including_extensions(self):
        original = HEADER.replace('allowed-tools: Read', 'allowed-tools: Read\nx-client:\n  enabled: true\n# comment') + '# Workflow\n\nRun the tool.\n'
        text, _ = optimize(parse_skill(original, 'sample'), TokenCounter(), experimental_cuts=True)
        self.assertEqual(text, original)

    def test_multiline_description_and_crlf(self):
        original = '---\r\nname: sample\r\ndescription: >-\r\n  Extract CSV records\r\n  when preparing reports.\r\n---\r\n# Workflow\r\n\r\nRun the tool.\r\n'
        skill = parse_skill(original, 'sample')
        self.assertIn('when preparing', skill.metadata['description'])
        self.assertEqual(optimize(skill, TokenCounter(), experimental_cuts=True)[0], original)

    def test_invalid_frontmatter(self):
        cases = [
            'plain markdown', '---\nname: sample\n',
            HEADER.replace('name: sample', 'name: Sample'),
            HEADER.replace('name: sample', 'name: sample--name'),
            HEADER.replace('name: sample', 'name: sample\nname: sample'),
            HEADER.replace('owner: "team"', 'owner: 12'),
            HEADER.replace('allowed-tools: Read', 'compatibility: 12'),
            HEADER.replace('description: Extract records from CSV files when preparing a report.', 'description: []'),
        ]
        for original in cases:
            with self.subTest(original=original), self.assertRaises(SkillError):
                parse_skill(original, 'sample')

    def test_default_preserves_domain_facts_and_greetings(self):
        original = HEADER + '# Overview\n\nProduction credentials live in the west region.\n\nWelcome to billing. Refunds expire in thirty days.\n'
        optimized, report = optimize(parse_skill(original, 'sample'), TokenCounter())
        self.assertEqual(optimized, original)
        self.assertTrue(all(f['action'] == 'review' for f in report['findings']))

    def test_name_matches_folder(self):
        with self.assertRaises(SkillError):
            parse_skill(HEADER, 'wrong')

    def test_finding_line_numbers(self):
        original = HEADER + '# History\n\nThis project began decades ago.\n'
        _, report = optimize(parse_skill(original, 'sample'), TokenCounter(), experimental_cuts=True)
        finding = report['findings'][0]
        self.assertEqual(original.splitlines()[finding['start_line'] - 1], 'This project began decades ago.')
        self.assertEqual(finding['start_line'], finding['end_line'])


class CliTests(unittest.TestCase):
    def setUp(self):
        scratch = Path(__file__).resolve().parents[1] / '.test-output'
        scratch.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'collection'
        skill = self.source / 'sample'
        (skill / 'scripts').mkdir(parents=True)
        (skill / 'SKILL.md').write_text(HEADER + '# History\n\nThis project began many decades ago.\n\n# Workflow\n\nRun `scripts/tool.py`.\n', encoding='utf-8')
        (skill / 'scripts' / 'tool.py').write_bytes(b'print("hello")\r\n')

    def invoke(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main([str(arg) for arg in args])
        return code, out.getvalue(), err.getvalue()

    def test_preview_does_not_mutate(self):
        before = {p: p.read_bytes() for p in self.source.rglob('*') if p.is_file()}
        code, out, err = self.invoke(self.source, '--json')
        self.assertEqual(code, 0, err)
        report = json.loads(out)
        self.assertEqual(report['totals']['skills'], 1)
        self.assertIsNone(report['output'])
        self.assertEqual(before, {p: p.read_bytes() for p in before})

    def test_export_preserves_resources_and_source(self):
        original = (self.source / 'sample' / 'SKILL.md').read_bytes()
        destination = self.root / 'optimized'
        report = self.root / 'report.json'
        code, _, err = self.invoke(self.source, '--experimental-cuts', '--output', destination, '--report', report)
        self.assertEqual(code, 0, err)
        self.assertEqual((self.source / 'sample' / 'SKILL.md').read_bytes(), original)
        self.assertEqual((destination / 'sample' / 'scripts' / 'tool.py').read_bytes(), b'print("hello")\r\n')
        self.assertNotIn('began many', (destination / 'sample' / 'SKILL.md').read_text())
        self.assertTrue(json.loads(report.read_text())['skills'][0]['diff'])

    def test_single_skill_file_export_retains_folder_name(self):
        destination = self.root / 'sample'
        code, _, err = self.invoke(self.source / 'sample' / 'SKILL.md', '-o', destination)
        self.assertEqual(code, 0, err)
        parse_skill((destination / 'SKILL.md').read_text(), destination.name)

    def test_single_skill_cannot_export_to_invalid_folder_name(self):
        code, _, _ = self.invoke(self.source / 'sample', '-o', self.root / 'renamed')
        self.assertEqual(code, 2)
        self.assertFalse((self.root / 'renamed').exists())

    def test_invalid_skill_aborts_entire_export(self):
        invalid = self.source / 'invalid'
        invalid.mkdir()
        (invalid / 'SKILL.md').write_text('broken')
        destination = self.root / 'optimized'
        code, _, _ = self.invoke(self.source, '-o', destination)
        self.assertEqual(code, 2)
        self.assertFalse(destination.exists())

    def test_overlaps_existing_output_and_reports_rejected(self):
        existing = self.root / 'existing'
        existing.mkdir()
        for args in [('-o', self.source / 'nested'), ('-o', self.root), ('-o', existing), ('--report', self.source / 'report.json')]:
            with self.subTest(args=args):
                self.assertEqual(self.invoke(self.source, *args)[0], 2)

    def test_non_skills_and_empty_collections_rejected(self):
        other = self.root / 'README.md'
        other.write_text('hello')
        empty = self.root / 'empty'
        empty.mkdir()
        self.assertEqual(self.invoke(other)[0], 2)
        self.assertEqual(self.invoke(empty)[0], 2)

    def test_symlink_resource_rejected(self):
        target = self.root / 'external.txt'
        target.write_text('outside')
        link = self.source / 'sample' / 'external.txt'
        try:
            link.symlink_to(target)
        except OSError:
            self.skipTest('Creating symbolic links requires OS privileges')
        self.assertEqual(self.invoke(self.source)[0], 2)


if __name__ == '__main__':
    unittest.main()
