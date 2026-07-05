"""
Validate compliance between spec files and test citations.

Checks:
- Every test function has at least one valid Spec: citation
- Every spec item is cited by at least one test
- Every citation resolves to a real spec item (no phantom references)

Language-specific parsing of test files is handled by parser modules
under specd.parsers. This module contains only the language-agnostic
validation logic.
"""

import re
from dataclasses import dataclass
from pathlib import Path

CITATION_RE = re.compile(
    r"^\s*Spec:\s+(.+?)\s+\[([^\]]+\.md)\]\s*$", re.MULTILINE
)
SPEC_ITEM_RE = re.compile(r"^- (.+)")


@dataclass
class TestEntry:
    __test__ = False
    identifier: str
    docstring: str | None


def load_specs(specs_dir):
    """Return a mapping of spec filename to list of spec item texts.

    Discovers .md files recursively. Lines inside HTML comment blocks
    (``<!-- ... -->``) are not treated as spec items.
    """
    specs_dir = Path(specs_dir)
    specs = {}

    for spec_file in sorted(specs_dir.rglob("*.md")):
        items = []
        in_comment = False

        for line in spec_file.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("<!--"):
                in_comment = True
            if in_comment:
                if "-->" in line:
                    in_comment = False
                continue

            match = SPEC_ITEM_RE.match(line)
            if match:
                items.append(match.group(1).strip())

        specs[spec_file.name] = items

    return specs


def parse_citations(docstring):
    """Extract (text, spec_filename) pairs from a docstring."""
    if not docstring:
        return []
    return CITATION_RE.findall(docstring)


def validate(specs, test_entries):
    """
    Check citation validity in both directions.

    Returns:
        uncited_tests: identifiers of tests with no valid citation
        uncited_items: (spec_file, item) pairs with no test citation
        phantoms: (test_id, text, spec_file, reason) for unresolved
                  citations
    """
    cited_items = set()
    tests_with_valid = set()
    phantoms = []

    for entry in test_entries:
        for text, spec_file in parse_citations(entry.docstring):
            if spec_file not in specs:
                phantoms.append(
                    (entry.identifier, text, spec_file, "spec file not found")
                )
            elif text not in specs[spec_file]:
                phantoms.append(
                    (
                        entry.identifier,
                        text,
                        spec_file,
                        "spec item not found in file",
                    )
                )
            else:
                cited_items.add((spec_file, text))
                tests_with_valid.add(entry.identifier)

    uncited_tests = [
        e.identifier for e in test_entries if e.identifier not in tests_with_valid
    ]
    uncited_items = [
        (spec_file, item)
        for spec_file, items in sorted(specs.items())
        for item in items
        if (spec_file, item) not in cited_items
    ]

    return uncited_tests, uncited_items, phantoms


def report(uncited_tests, uncited_items, phantoms, total_tests):
    """Print a compliance report to stdout."""
    print("\n=== Spec Compliance Report ===\n")

    if uncited_tests:
        print(f"TESTS WITHOUT VALID SPEC ITEMS ({len(uncited_tests)})\n")
        for n, identifier in enumerate(uncited_tests, 1):
            print(f"{n}. {identifier}")
        print()

    if uncited_items:
        print(f"SPEC ITEMS NOT CITED BY TESTS ({len(uncited_items)})\n")
        for n, (spec_file, item) in enumerate(uncited_items, 1):
            print(f"{n}. {spec_file}: {item}")
        print()

    if phantoms:
        print(f"PHANTOM CITATIONS ({len(phantoms)})\n")
        for n, (test_id, text, spec_file, reason) in enumerate(phantoms, 1):
            print(f"{n}. {test_id}")
            print(f"   - {text} [{spec_file}]")
            print(f"   - {reason}")
        print()

    tests_with_valid = total_tests - len(uncited_tests)
    print("=== Summary ===\n")
    print(f"  Tests checked:                     {total_tests}")
    print(f"  Tests with valid spec items:       {tests_with_valid}")
    print(f"  Tests without valid spec items:    {len(uncited_tests)}")
    print(f"  Spec items without related tests:  {len(uncited_items)}")
    print(f"  Phantom citations:                 {len(phantoms)}")
    print()
    print(
        'Note: "Tests checked" are counted by function. Parameterized test '
        "functions may run more than once in a test suite, causing the test "
        "runner's count to be higher."
    )
    print()


def run_validation(specs_dir, tests_dir):
    """
    Run the full validation and print a report.

    Discovers test files by iterating over registered parsers and their
    file patterns. Returns 0 if all checks pass, 1 otherwise.
    """
    from specd.parsers import PARSERS

    specs_dir = Path(specs_dir)
    tests_dir = Path(tests_dir)

    specs = load_specs(specs_dir)

    test_entries = []
    for parser in PARSERS:
        for pattern in parser.FILE_PATTERNS:
            for test_file in sorted(tests_dir.rglob(pattern)):
                test_entries.extend(
                    parser.collect_test_entries(test_file, tests_dir)
                )

    uncited_tests, uncited_items, phantoms = validate(specs, test_entries)

    total_tests = len(test_entries)
    report(uncited_tests, uncited_items, phantoms, total_tests)

    return 1 if (uncited_tests or uncited_items or phantoms) else 0
