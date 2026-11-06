"""Preview or export an independently usable collection of skills."""

from __future__ import annotations

import argparse
import difflib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

from . import __version__
from .core import SkillError, TokenCounter, optimize, parse_skill


def _within(path: Path, parent: Path) -> bool:
    return path == parent or parent in path.parents


def _source(path: Path) -> tuple[Path, list[Path]]:
    if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()):
        raise SkillError("Source must not be a symbolic link or junction")
    source = path.resolve()
    if source.is_file():
        if source.name != "SKILL.md":
            raise SkillError("Only SKILL.md files or skill directories are supported")
        root, skills = source.parent, [source]
    elif source.is_dir():
        root = source
        skills = sorted(source.rglob("SKILL.md"))
    else:
        raise SkillError(f"Source does not exist: {source}")
    # Copying only regular files prevents a skill from exporting external content.
    for current, directories, files in os.walk(root, followlinks=False):
        for name in directories + files:
            item = Path(current) / name
            if item.is_symlink() or (hasattr(item, "is_junction") and item.is_junction()):
                raise SkillError(f"Links/junctions are not supported: {item}")
            if not item.is_dir() and not item.is_file():
                raise SkillError(f"Only regular files/directories are supported: {item}")
    if not skills:
        raise SkillError("No SKILL.md files found")
    return root, skills


def run(args) -> dict:
    root, paths = _source(Path(args.source))
    output = Path(args.output).resolve() if args.output else None
    report_path = Path(args.report).resolve() if args.report else None
    if output and (_within(output, root) or _within(root, output)):
        raise SkillError("Output and source must be separate, non-overlapping directories")
    if output and output.exists():
        raise SkillError("Output already exists; choose a new directory")
    if output and (root / "SKILL.md") in paths and output.name != root.name:
        raise SkillError(f"A single-skill output directory must retain the name '{root.name}'")
    if report_path and (_within(report_path, root) or (output and _within(report_path, output))):
        raise SkillError("Report must be outside source and output directories")
    if report_path and report_path.exists():
        raise SkillError("Report already exists; choose a new file")
    counter = TokenCounter(args.encoding)
    reports, changes = [], []
    for path in paths:
        # Preserve frontmatter, newlines, and auxiliary files byte-for-byte.
        with path.open(encoding="utf-8", newline="") as handle:
            original = handle.read()
        skill = parse_skill(original, path.parent.name)
        optimized, report = optimize(skill, counter, experimental_cuts=args.experimental_cuts)
        parse_skill(optimized, path.parent.name)
        relative = path.relative_to(root)
        report["path"] = relative.as_posix()
        report["diff"] = "".join(difflib.unified_diff(original.splitlines(keepends=True), optimized.splitlines(keepends=True), fromfile=f"before/{relative.as_posix()}", tofile=f"after/{relative.as_posix()}"))
        reports.append(report)
        changes.append((relative, optimized))
    before = sum(report["before_tokens"] for report in reports)
    after = sum(report["after_tokens"] for report in reports)
    result = {
        "version": __version__, "source": str(root), "output": str(output) if output else None,
        "token_counter": counter.label, "skills": reports,
        "totals": {"skills": len(reports), "before_tokens": before, "after_tokens": after,
                   "saved_tokens": before - after,
                   "reduction_percent": round((before - after) / before * 100, 2) if before else 0},
        "limitations": "Heuristic cuts require review. Token savings do not demonstrate preserved task success or improved routing. Only SKILL.md tokens are counted; auxiliary resources are unchanged.",
    }
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        # Stage and validate the entire collection before making it visible.
        staging = Path(tempfile.mkdtemp(prefix=".skilltrim-", dir=output.parent))
        try:
            shutil.copytree(root, staging, dirs_exist_ok=True)
            for relative, optimized in changes:
                with (staging / relative).open("w", encoding="utf-8", newline="") as handle:
                    handle.write(optimized)
            if output.exists():
                raise SkillError("Output appeared during export; refusing to overwrite it")
            staging.rename(output)
        finally:
            if staging.exists():
                shutil.rmtree(staging)
    if report_path:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with report_path.open("x", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Analyze Agent Skills; preview by default, export copies with --output.")
    parser.add_argument("--experimental-cuts", action="store_true", help="Apply unverified heuristic cuts; review every diff before adoption")
    parser.add_argument("source", help="SKILL.md, a skill folder, or a collection of skills")
    parser.add_argument("--output", "-o", help="New destination directory; never modifies the source")
    parser.add_argument("--report", help="Write detailed JSON with findings and unified diffs to a new file")
    parser.add_argument("--json", action="store_true", help="Print machine-readable report")
    parser.add_argument("--diff", action="store_true", help="Show proposed unified diffs")
    parser.add_argument("--encoding", help="Exact tiktoken encoding (e.g. cl100k_base); requires [tokens] extra")
    parser.add_argument("--version", action="version", version=f"skilltrim {__version__}")
    args = parser.parse_args(argv)
    try:
        result = run(args)
    except (SkillError, OSError, UnicodeError) as exc:
        print(f"skilltrim: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        total = result["totals"]
        print(f"skilltrim: {total['skills']} skill(s) | {result['token_counter']}")
        print(f"{total['before_tokens']} -> {total['after_tokens']} tokens ({total['reduction_percent']:.1f}% reduction)")
        for report in result["skills"]:
            removed = sum(f["action"] == "remove" for f in report["findings"])
            review = len(report["findings"]) - removed
            print(f"  {report['name']}: {report['reduction_percent']:.1f}% | routing {report['routing']['score']}/100 | {removed} cuts, {review} review items")
            for suggestion in report["routing"]["suggestions"]:
                print(f"    Routing: {suggestion}")
            if report["routing"]["proposed_description"]:
                print(f"    Proposed description: {report['routing']['proposed_description']}")
            for finding in report["findings"]:
                print(f"    Lines {finding['start_line']}-{finding['end_line']}: {finding['action']} ({finding['category']}): {finding['reason']}")
            if args.diff:
                print(report["diff"], end="")
        print(f"Exported to {result['output']}" if result["output"] else "Preview only. Use --output NEW_DIRECTORY to export.")
        print(result["limitations"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
