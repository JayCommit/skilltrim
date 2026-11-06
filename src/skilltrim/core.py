"""Lossless frontmatter handling and deliberately limited Markdown heuristics."""

from __future__ import annotations

import math
import re
from dataclasses import asdict, dataclass

import yaml


class SkillError(ValueError):
    pass


class UniqueLoader(yaml.SafeLoader):
    """Reject ambiguous duplicate keys instead of silently losing metadata."""


def _mapping(loader, node, deep=False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if not isinstance(key, str):
            raise SkillError("Frontmatter keys must be strings")
        if key in result:
            raise SkillError(f"Duplicate frontmatter key: {key}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapping)


@dataclass
class Skill:
    frontmatter: str
    body: str
    metadata: dict
    body_line: int

    def render(self, body: str) -> str:
        return self.frontmatter + body


def parse_skill(text: str, folder_name: str | None = None) -> Skill:
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        raise SkillError("SKILL.md must start with YAML frontmatter (---)")
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        raise SkillError("Missing closing frontmatter delimiter")
    try:
        metadata = yaml.load("".join(lines[1:end]), Loader=UniqueLoader)
    except (yaml.YAMLError, RecursionError) as exc:
        raise SkillError(f"Invalid YAML frontmatter: {exc}") from exc
    if not isinstance(metadata, dict):
        raise SkillError("Frontmatter must be a mapping")
    name = metadata.get("name")
    if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) or len(name) > 64:
        raise SkillError("name must be 1–64 lowercase letters/digits/hyphens, without consecutive hyphens")
    if folder_name is not None and name != folder_name:
        raise SkillError(f"name '{name}' must match parent directory '{folder_name}'")
    description = metadata.get("description")
    if not isinstance(description, str) or not 1 <= len(description.strip()) <= 1024:
        raise SkillError("description must be a non-empty string of at most 1024 characters")
    for field in ("license", "compatibility", "allowed-tools"):
        if field in metadata and not isinstance(metadata[field], str):
            raise SkillError(f"{field} must be a string")
    if "compatibility" in metadata and not 1 <= len(metadata["compatibility"]) <= 500:
        raise SkillError("compatibility must be 1–500 characters")
    extra = metadata.get("metadata", {})
    if not isinstance(extra, dict) or not all(isinstance(v, str) for v in extra.values()):
        raise SkillError("metadata must map strings to strings")
    return Skill("".join(lines[:end + 1]), "".join(lines[end + 1:]), metadata, end + 2)


class TokenCounter:
    def __init__(self, encoding: str | None = None):
        self.encoder = None
        self.label = "estimated-utf8-bytes/4"
        if encoding:
            try:
                import tiktoken
            except ImportError as exc:
                raise SkillError("Exact counting requires pip install 'skilltrim[tokens]'") from exc
            try:
                self.encoder = tiktoken.get_encoding(encoding)
            except (ValueError, OSError) as exc:
                raise SkillError(f"Cannot load token encoding '{encoding}': {exc}") from exc
            self.label = encoding

    def count(self, text: str) -> int:
        if self.encoder:
            return len(self.encoder.encode(text, disallowed_special=()))
        return math.ceil(len(text.encode("utf-8")) / 4)


@dataclass
class Finding:
    start_line: int
    end_line: int
    category: str
    action: str
    reason: str
    text: str


# These signals favor retention. They cannot prove semantic equivalence.
OPERATIONAL = re.compile(
    r"\b(must|never|always|do not|don't|only|unless|before|after|if|when|require\w*|"
    r"run|use|execute|install|check|verify|preserve|avoid|stop|ask|confirm|permission|"
    r"output|input|error|fail\w*|return|keep|write|read|delete|create|ensure|should|"
    r"need\w*|cannot|can't|may not|shall|remember|important|warning|caution)\b", re.I
)
NARRATIVE_HEADING = re.compile(r"^(?:background|history|historical context|motivation|overview|introduction|why .+)$", re.I)
EXAMPLE_HEADING = re.compile(r"\b(examples?|walkthroughs?|tutorials?)\b", re.I)
FILLER = re.compile(
    r"^(?:Welcome to\b|Thank you for\b|Happy (?:coding|building|learning)[!. ]|"
    r"In today's (?:fast-paced|ever-changing)\b|This (?:powerful|comprehensive|amazing) skill\b)", re.I
)


def routing_quality(description: str) -> dict:
    words = description.split()
    checks = {
        "specific_length": 8 <= len(words) <= 80,
        "activation_context": bool(re.search(r"\b(when|for|if)\b", description, re.I)),
        "capability_verb": bool(re.search(r"\b(analy[sz]\w*|compress\w*|optimi[sz]\w*|creat\w*|edit\w*|extract\w*|review\w*|build\w*|debug\w*|convert\w*|deploy\w*|generat\w*|validat\w*|process\w*)\b", description, re.I)),
        "no_catchall": not bool(re.search(r"\b(anything|everything|all tasks|any task|various tasks)\b", description, re.I)),
    }
    hints = {
        "specific_length": "Describe the concrete capability and task in roughly 8–80 words.",
        "activation_context": "State when to activate the skill, using its actual task domain.",
        "capability_verb": "Name the operation the skill performs with a concrete verb.",
        "no_catchall": "Replace broad catchalls with the actual supported task boundary.",
    }
    candidate = re.sub(r"^(?:This skill (?:helps you to|allows you to|can be used to)|A (?:powerful|comprehensive) tool to)\s+", "", description, flags=re.I)
    if candidate:
        candidate = candidate[0].upper() + candidate[1:]
    return {"score": sum(checks.values()) * 25, "checks": checks,
            "suggestions": [hints[key] for key, passed in checks.items() if not passed],
            "proposed_description": candidate if candidate != description else None,
            "note": "Heuristic lint score, not measured agent selection accuracy. Proposals require review."}


def optimize(skill: Skill, counter: TokenCounter, *, experimental_cuts: bool = False) -> tuple[str, dict]:
    lines = skill.body.splitlines(keepends=True)
    findings = []
    output = []
    heading = ""
    fence = None
    index = 0
    previous = None
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        marker = re.match(r"^[ \t]*(?:(?:[-+*]|\d+[.)])[ \t]+|>[ \t]*)?(`{3,}|~{3,})", line)
        if marker:
            token = marker.group(1)
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence) and not line[marker.end():].strip():
                fence = None
            output.append(line)
            previous = None
            index += 1
            continue
        if fence is not None:
            output.append(line)
            index += 1
            continue
        match = re.match(r"^ {0,3}#{1,6}\s+(.+?)\s*#*\s*$", line)
        if match:
            heading = match.group(1)
            output.append(line)
            previous = None
            index += 1
            continue
        if not stripped:
            output.append(line)
            index += 1
            continue
        start = index
        while index < len(lines) and lines[index].strip():
            # A heading/fence without a blank line still starts a new block.
            if index > start and (re.match(r"^ {0,3}#{1,6}\s", lines[index]) or re.match(r"^[ \t]*(?:(?:[-+*]|\d+[.)])[ \t]+|>[ \t]*)?(?:`{3,}|~{3,})", lines[index])):
                break
            index += 1
        block = "".join(lines[start:index])
        protected = bool(OPERATIONAL.search(block) or re.search(r"[`~\[\]<>|]|https?://|^\s*(?:[-*+>] |\d+[.)] | {4}|\t)", block, re.M))
        category = None
        action = "review"
        reason = ""
        if not protected and FILLER.search(block.strip()):
            category, action, reason = "filler", "remove", "Standalone promotional or greeting prose without detected operational signals."
        elif NARRATIVE_HEADING.fullmatch(heading) and not protected:
            category, action, reason = "narrative", "remove", "Prose in a narrative section without detected instructions, code, lists, or links."
        elif previous == block.strip() and not protected:
            category, action, reason = "duplicate", "remove", "Adjacent identical prose paragraph; protected instructions are retained."
        elif EXAMPLE_HEADING.search(heading):
            category, reason = "example", "Review for optional disclosure; examples may encode essential behavior."
        elif NARRATIVE_HEADING.fullmatch(heading):
            category, reason = "protected-context", "Context includes operational or structured content; retain pending semantic review."
        if action == "remove" and not experimental_cuts:
            action = "review"
            reason += " Retained: semantic safety is unverified."
        if category:
            findings.append(Finding(skill.body_line + start, skill.body_line + index - 1, category, action, reason, block))
        if action != "remove":
            output.append(block)
        previous = block.strip()
    body = "".join(output)
    result = skill.render(body)
    before = counter.count(skill.render(skill.body))
    after = counter.count(result)
    report = {
        "name": skill.metadata["name"], "before_tokens": before, "after_tokens": after,
        "saved_tokens": before - after,
        "reduction_percent": round((before - after) / before * 100, 2) if before else 0,
        "routing": routing_quality(skill.metadata["description"]),
        "findings": [asdict(finding) for finding in findings],
    }
    return result, report
