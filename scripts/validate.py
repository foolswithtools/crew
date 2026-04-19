#!/usr/bin/env python3
"""
Validate archetype files in `personas/` against the format spec.

Usage:
    python3 scripts/validate.py                  # validate every personas/*.md
    python3 scripts/validate.py personas/foo.md  # validate one or more files

Exit codes:
    0 — all checked files pass (warnings allowed)
    1 — at least one error found

Findings are printed in a structured form: each line is
    <severity>  <relative-path>  <code>  <message>

Severities:
    ERROR    — file violates the spec; blocks merge / fails the run
    WARNING  — non-fatal issue (e.g. tag not in controlled vocab)

Layer-1 source of truth (read by this script):
    SCHEMA.md      — format spec
    vocab/*.yml    — controlled vocabularies per facet
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
PERSONAS_DIR = REPO_ROOT / "personas"
VOCAB_DIR = REPO_ROOT / "vocab"

REQUIRED_FRONTMATTER_FIELDS = [
    "name",
    "display_name",
    "exemplars",
    "expertise",
    "function",
    "approach",
    "reviewed",
]

REQUIRED_SECTIONS = [
    "## Exemplars & coherence",
    "## Shared philosophy",
    "## What they push on",
    "## Blind spots",
    "## Not to be confused with",
]

FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n(.*)\Z", re.DOTALL)
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


@dataclass
class Finding:
    severity: str  # "ERROR" or "WARNING"
    path: Path
    code: str
    message: str

    def format(self) -> str:
        rel = self.path.relative_to(REPO_ROOT) if self.path.is_absolute() else self.path
        return f"{self.severity:7s}  {rel}  {self.code}  {self.message}"


def load_vocab(facet: str) -> dict:
    path = VOCAB_DIR / f"{facet}.yml"
    if not path.exists():
        raise SystemExit(f"vocab file missing: {path.relative_to(REPO_ROOT)}")
    with path.open() as f:
        data = yaml.safe_load(f) or {}
    tags = data.get("tags") or {}
    if not isinstance(tags, dict):
        raise SystemExit(f"vocab file malformed (expected `tags:` mapping): {path}")
    return tags


def split_frontmatter(text: str, path: Path) -> tuple[dict | None, str, list[Finding]]:
    findings: list[Finding] = []
    match = FRONTMATTER_RE.match(text)
    if not match:
        findings.append(Finding("ERROR", path, "frontmatter-missing",
                                "file does not start with a YAML frontmatter block"))
        return None, text, findings
    raw_yaml, body = match.group(1), match.group(2)
    try:
        data = yaml.safe_load(raw_yaml)
    except yaml.YAMLError as e:
        findings.append(Finding("ERROR", path, "frontmatter-yaml-error",
                                f"frontmatter is not valid YAML: {e}"))
        return None, body, findings
    if not isinstance(data, dict):
        findings.append(Finding("ERROR", path, "frontmatter-not-mapping",
                                "frontmatter must be a YAML mapping"))
        return None, body, findings
    return data, body, findings


def check_required_fields(meta: dict, path: Path) -> list[Finding]:
    findings: list[Finding] = []
    for field in REQUIRED_FRONTMATTER_FIELDS:
        if field not in meta:
            findings.append(Finding("ERROR", path, "field-missing",
                                    f"required frontmatter field `{field}` is missing"))
    if "name" in meta and not isinstance(meta["name"], str):
        findings.append(Finding("ERROR", path, "field-type",
                                "`name` must be a string (kebab-case slug)"))
    if "name" in meta and isinstance(meta["name"], str) and not SLUG_RE.match(meta["name"]):
        findings.append(Finding("ERROR", path, "name-not-kebab",
                                f"`name` must be kebab-case (got `{meta['name']}`)"))
    if "display_name" in meta and not isinstance(meta["display_name"], str):
        findings.append(Finding("ERROR", path, "field-type",
                                "`display_name` must be a string"))
    if "reviewed" in meta and not isinstance(meta["reviewed"], bool):
        findings.append(Finding("ERROR", path, "field-type",
                                "`reviewed` must be a boolean (`true` or `false`)"))
    for facet in ("exemplars", "expertise", "function", "approach"):
        if facet in meta and not isinstance(meta[facet], list):
            findings.append(Finding("ERROR", path, "field-type",
                                    f"`{facet}` must be a YAML list"))
    if isinstance(meta.get("exemplars"), list):
        n = len(meta["exemplars"])
        if n < 2 or n > 5:
            findings.append(Finding("ERROR", path, "exemplars-count",
                                    f"`exemplars` must have 2-5 entries (got {n})"))
    return findings


def check_filename_matches_name(meta: dict, path: Path) -> list[Finding]:
    if "name" not in meta or not isinstance(meta["name"], str):
        return []
    expected = f"{meta['name']}.md"
    if path.name != expected:
        return [Finding("ERROR", path, "filename-name-mismatch",
                        f"filename `{path.name}` does not match frontmatter name `{meta['name']}` (expected `{expected}`)")]
    return []


def check_tags_against_vocab(meta: dict, path: Path, vocab: dict[str, dict]) -> list[Finding]:
    findings: list[Finding] = []
    for facet, allowed in vocab.items():
        values = meta.get(facet)
        if not isinstance(values, list):
            continue
        for tag in values:
            if not isinstance(tag, str):
                findings.append(Finding("ERROR", path, "tag-type",
                                        f"`{facet}` contains a non-string entry: {tag!r}"))
                continue
            if tag not in allowed:
                findings.append(Finding("WARNING", path, "tag-unknown",
                                        f"`{facet}` tag `{tag}` is not in vocab/{facet}.yml — propose it or pick an existing tag"))
    return findings


def check_required_sections(body: str, meta: dict, path: Path) -> list[Finding]:
    findings: list[Finding] = []
    display = meta.get("display_name") if isinstance(meta.get("display_name"), str) else None
    if display:
        expected_h1 = f"# {display}"
        if expected_h1 not in body:
            findings.append(Finding("ERROR", path, "h1-missing",
                                    f"top-level heading `{expected_h1}` not found"))
    for section in REQUIRED_SECTIONS:
        if section not in body:
            findings.append(Finding("ERROR", path, "section-missing",
                                    f"required section `{section}` not found"))
    return findings


def check_unique_names(metas: list[tuple[Path, dict]]) -> list[Finding]:
    findings: list[Finding] = []
    seen: dict[str, Path] = {}
    for path, meta in metas:
        name = meta.get("name")
        if not isinstance(name, str):
            continue
        if name in seen:
            findings.append(Finding("ERROR", path, "name-duplicate",
                                    f"`name: {name}` is also used by {seen[name].relative_to(REPO_ROOT)}"))
        else:
            seen[name] = path
    return findings


def check_vocab_relationships(vocab: dict[str, dict]) -> list[Finding]:
    """
    SKOS-symmetry check across each facet file:
      - every value in broader/narrower/related must reference a tag in the same facet
      - if A.narrower contains B, then B.broader must contain A (and vice versa)
      - cross_facet_related (P4.5) must reference a known facet + a tag in that facet,
        and must be symmetric across facets (A→B implies B→A)
    Findings are WARNINGs (vocab governance, not a file-format failure).
    """
    findings: list[Finding] = []
    known_facets = set(vocab.keys())
    for facet, tags in vocab.items():
        path = VOCAB_DIR / f"{facet}.yml"
        for tag, meta in tags.items():
            if not isinstance(meta, dict):
                continue
            for rel in ("broader", "narrower", "related"):
                refs = meta.get(rel) or []
                if not isinstance(refs, list):
                    findings.append(Finding("WARNING", path, "vocab-rel-type",
                                            f"`{tag}.{rel}` must be a list in vocab/{facet}.yml"))
                    continue
                for ref in refs:
                    if ref not in tags:
                        findings.append(Finding("WARNING", path, "vocab-rel-unknown",
                                                f"`{tag}.{rel}` references `{ref}` which is not a tag in vocab/{facet}.yml"))
            narrower = meta.get("narrower") or []
            if isinstance(narrower, list):
                for child in narrower:
                    if child not in tags or not isinstance(tags[child], dict):
                        continue
                    child_broader = tags[child].get("broader") or []
                    if tag not in child_broader:
                        findings.append(Finding("WARNING", path, "vocab-rel-asymmetric",
                                                f"`{tag}.narrower` includes `{child}`, but `{child}.broader` does not include `{tag}` in vocab/{facet}.yml"))
            broader = meta.get("broader") or []
            if isinstance(broader, list):
                for parent in broader:
                    if parent not in tags or not isinstance(tags[parent], dict):
                        continue
                    parent_narrower = tags[parent].get("narrower") or []
                    if tag not in parent_narrower:
                        findings.append(Finding("WARNING", path, "vocab-rel-asymmetric",
                                                f"`{tag}.broader` includes `{parent}`, but `{parent}.narrower` does not include `{tag}` in vocab/{facet}.yml"))

            cfr = meta.get("cross_facet_related")
            if cfr is not None and not isinstance(cfr, dict):
                findings.append(Finding("WARNING", path, "vocab-cross-facet-type",
                                        f"`{tag}.cross_facet_related` must be a mapping of target-facet -> tag list in vocab/{facet}.yml"))
                continue
            if not isinstance(cfr, dict):
                continue
            for target_facet, target_tags in cfr.items():
                if target_facet == facet:
                    findings.append(Finding("WARNING", path, "vocab-cross-facet-selfref",
                                            f"`{tag}.cross_facet_related` targets its own facet `{target_facet}` — use `related` for within-facet links in vocab/{facet}.yml"))
                    continue
                if target_facet not in known_facets:
                    findings.append(Finding("WARNING", path, "vocab-cross-facet-unknown-facet",
                                            f"`{tag}.cross_facet_related` targets unknown facet `{target_facet}` in vocab/{facet}.yml"))
                    continue
                if not isinstance(target_tags, list):
                    findings.append(Finding("WARNING", path, "vocab-cross-facet-type",
                                            f"`{tag}.cross_facet_related.{target_facet}` must be a list in vocab/{facet}.yml"))
                    continue
                for ref in target_tags:
                    if ref not in vocab[target_facet]:
                        findings.append(Finding("WARNING", path, "vocab-cross-facet-unknown-tag",
                                                f"`{tag}.cross_facet_related.{target_facet}` references `{ref}` which is not a tag in vocab/{target_facet}.yml"))
                        continue
                    reverse = vocab[target_facet][ref].get("cross_facet_related") if isinstance(vocab[target_facet][ref], dict) else None
                    reverse_list = (reverse or {}).get(facet) or [] if isinstance(reverse, dict) else []
                    if tag not in reverse_list:
                        findings.append(Finding("WARNING", path, "vocab-cross-facet-asymmetric",
                                                f"`{tag}.cross_facet_related.{target_facet}` includes `{ref}`, but `{ref}.cross_facet_related.{facet}` does not include `{tag}` in vocab/{target_facet}.yml"))
    return findings


def check_exemplar_containment(metas: list[tuple[Path, dict]]) -> list[Finding]:
    """Flag any archetype whose exemplar set is a subset of another's."""
    findings: list[Finding] = []
    norm: list[tuple[Path, str, frozenset[str]]] = []
    for path, meta in metas:
        ex = meta.get("exemplars")
        name = meta.get("name") if isinstance(meta.get("name"), str) else path.stem
        if not isinstance(ex, list):
            continue
        normalized = frozenset(e.strip().lower() for e in ex if isinstance(e, str))
        if not normalized:
            continue
        norm.append((path, name, normalized))
    for i, (p_a, n_a, ex_a) in enumerate(norm):
        for j, (p_b, n_b, ex_b) in enumerate(norm):
            if i == j:
                continue
            if ex_a <= ex_b:
                findings.append(Finding("ERROR", p_a, "exemplars-contained",
                                        f"exemplars of `{n_a}` are fully contained in `{n_b}` ({p_b.relative_to(REPO_ROOT)}) — likely duplicate"))
    return findings


def validate_file(path: Path, vocab: dict[str, dict]) -> tuple[dict | None, list[Finding]]:
    findings: list[Finding] = []
    text = path.read_text(encoding="utf-8")
    meta, body, fm_findings = split_frontmatter(text, path)
    findings.extend(fm_findings)
    if meta is None:
        return None, findings
    findings.extend(check_required_fields(meta, path))
    findings.extend(check_filename_matches_name(meta, path))
    findings.extend(check_tags_against_vocab(meta, path, vocab))
    findings.extend(check_required_sections(body, meta, path))
    return meta, findings


def main(argv: list[str]) -> int:
    vocab = {
        "expertise": load_vocab("expertise"),
        "function": load_vocab("function"),
        "approach": load_vocab("approach"),
    }

    if len(argv) > 1:
        files = [Path(a).resolve() for a in argv[1:]]
        cross_file_check = False
    else:
        files = sorted(PERSONAS_DIR.glob("*.md"))
        cross_file_check = True

    if not files:
        print("no archetype files found", file=sys.stderr)
        return 1

    all_findings: list[Finding] = []
    metas: list[tuple[Path, dict]] = []
    for path in files:
        if not path.exists():
            all_findings.append(Finding("ERROR", path, "file-not-found",
                                        "file does not exist"))
            continue
        meta, findings = validate_file(path, vocab)
        all_findings.extend(findings)
        if meta is not None:
            metas.append((path, meta))

    if cross_file_check:
        all_findings.extend(check_unique_names(metas))
        all_findings.extend(check_exemplar_containment(metas))
        all_findings.extend(check_vocab_relationships(vocab))

    errors = [f for f in all_findings if f.severity == "ERROR"]
    warnings = [f for f in all_findings if f.severity == "WARNING"]

    for finding in all_findings:
        print(finding.format())

    print()
    print(f"checked {len(files)} file(s) — {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
