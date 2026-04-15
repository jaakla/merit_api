#!/usr/bin/env python3
"""Generate a method-level test coverage report for merit_api namespaces.

Coverage here means: a namespace method appears to be referenced by tests
(via direct namespace calls or matching endpoint strings in _post calls).
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parent
NAMESPACES_FILE = ROOT / "src/merit_api/namespaces.py"
TESTS_DIR = ROOT / "tests"
REPORT_FILE = ROOT / "reports/method_test_coverage.md"


@dataclass(frozen=True)
class MethodDef:
    namespace: str
    method: str
    endpoint: str
    version: str

    @property
    def fq_name(self) -> str:
        return f"{self.namespace}.{self.method}"


@dataclass
class MethodCoverage:
    method_def: MethodDef
    covered: bool
    evidence: list[str]

    @property
    def capability(self) -> str:
        name = self.method_def.method.lower()
        endpoint = self.method_def.endpoint.lower()
        if name.startswith(("get_", "list")) or endpoint.startswith("get") or endpoint.endswith("list"):
            return "read"
        return "write"


def _extract_endpoint_call(func: ast.FunctionDef) -> tuple[str, str] | None:
    for node in ast.walk(func):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute) or node.func.attr != "_post":
            continue
        if not node.args:
            continue
        endpoint = node.args[0]
        if not isinstance(endpoint, ast.Constant) or not isinstance(endpoint.value, str):
            continue

        version = "v1"
        for kw in node.keywords:
            if kw.arg == "version" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                version = kw.value.value
        return endpoint.value, version
    return None


def parse_namespace_methods() -> list[MethodDef]:
    tree = ast.parse(NAMESPACES_FILE.read_text())
    methods: list[MethodDef] = []

    for node in tree.body:
        if not isinstance(node, ast.ClassDef) or node.name == "Namespace":
            continue
        for class_item in node.body:
            if not isinstance(class_item, ast.FunctionDef):
                continue
            endpoint_call = _extract_endpoint_call(class_item)
            if endpoint_call is None:
                continue
            endpoint, version = endpoint_call
            methods.append(MethodDef(node.name, class_item.name, endpoint, version))
    return methods


def _walk_calls(tree: ast.AST) -> Iterable[ast.Call]:
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            yield node


def parse_test_references() -> tuple[set[str], set[str], dict[str, list[str]]]:
    namespace_calls: set[str] = set()
    endpoint_calls: set[str] = set()
    evidence: dict[str, list[str]] = {}

    for test_file in sorted(TESTS_DIR.glob("test_*.py")):
        tree = ast.parse(test_file.read_text())
        for node in _walk_calls(tree):
            if isinstance(node.func, ast.Attribute):
                # client.<namespace>.<method>(...)
                outer = node.func.value
                if isinstance(outer, ast.Attribute) and isinstance(outer.value, ast.Name) and outer.value.id == "client":
                    key = f"{outer.attr}.{node.func.attr}"
                    namespace_calls.add(key)
                    evidence.setdefault(key, []).append(test_file.name)

                # client._post("endpoint", ...)
                if (
                    isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "client"
                    and node.func.attr == "_post"
                    and node.args
                    and isinstance(node.args[0], ast.Constant)
                    and isinstance(node.args[0].value, str)
                ):
                    endpoint = node.args[0].value
                    endpoint_calls.add(endpoint)
                    evidence.setdefault(f"endpoint:{endpoint}", []).append(test_file.name)

    return namespace_calls, endpoint_calls, evidence


def build_coverage() -> list[MethodCoverage]:
    methods = parse_namespace_methods()
    namespace_calls, endpoint_calls, evidence = parse_test_references()

    coverage_rows: list[MethodCoverage] = []
    for m in methods:
        key = f"{m.namespace.lower()}.{m.method}"
        endpoint_key = f"endpoint:{m.endpoint}"

        hits = []
        if key in namespace_calls:
            hits.extend(evidence.get(key, []))
        if m.endpoint in endpoint_calls:
            hits.extend(evidence.get(endpoint_key, []))

        unique_hits = sorted(set(hits))
        coverage_rows.append(MethodCoverage(method_def=m, covered=bool(unique_hits), evidence=unique_hits))

    return coverage_rows


def render_report(rows: list[MethodCoverage]) -> str:
    read_rows = [row for row in rows if row.capability == "read"]
    write_rows = [row for row in rows if row.capability == "write"]

    def section(title: str, section_rows: list[MethodCoverage]) -> str:
        total = len(section_rows)
        covered = sum(1 for row in section_rows if row.covered)
        pct = (covered / total * 100) if total else 0

        lines = [f"## {title}", "", f"Coverage: **{covered}/{total} ({pct:.1f}%)**", ""]
        lines.append("| Method | Endpoint | Version | Covered by tests | Evidence |")
        lines.append("|---|---|---|---|---|")
        for row in sorted(section_rows, key=lambda r: r.method_def.fq_name):
            md = row.method_def
            evidence = ", ".join(row.evidence) if row.evidence else "—"
            lines.append(
                f"| `{md.fq_name}` | `{md.endpoint}` | `{md.version}` | {'✅' if row.covered else '❌'} | {evidence} |"
            )
        lines.append("")
        return "\n".join(lines)

    overall_total = len(rows)
    overall_covered = sum(1 for row in rows if row.covered)
    overall_pct = (overall_covered / overall_total * 100) if overall_total else 0

    report = [
        "# Merit API method test coverage (read/write)",
        "",
        "This report is generated by static inspection of namespace methods and tests.",
        "A method is marked covered if tests reference the namespace call or matching `_post` endpoint.",
        "",
        f"Overall coverage: **{overall_covered}/{overall_total} ({overall_pct:.1f}%)**",
        "",
        section("Read capabilities", read_rows),
        section("Write capabilities", write_rows),
    ]
    return "\n".join(report)


def main() -> None:
    rows = build_coverage()
    report = render_report(rows)
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text(report)
    print(f"Wrote {REPORT_FILE}")


if __name__ == "__main__":
    main()
