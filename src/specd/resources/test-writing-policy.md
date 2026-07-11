# Tests and specs

This policy is meant to keep specs current by mandating a link between specs and tests.

## Assumptions
This policy assumes that:
1. all project functionality will be recorded in a `specs/<scope>.md` file
2. specs are itemized lists describing functionality and interfaces

The test-writer will not need to create those spec files; they should exist before writing tests.

## Rules
1. Tests refer to spec items from spec files by including a citation in the form:
   `Spec: <the untruncated verbatim spec line item> [the_relevant_file.md]`
{%- if include_python %}
   - In Python, citations go in the test function's docstring
{%- endif %}
{%- if include_js_ts %}
   - In JavaScript/TypeScript, citations go in `//` comments inside the test body
{%- endif %}
2. Every item in the specs must be associated with at least one test
3. Every test must relate to at least one item in the specs
4. Multiple tests can relate to the same spec item
5. A single test can relate to multiple spec items
6. Only add a spec item to a test if the test is aimed at testing the item, not if it merely tests something incidentally

**For clarity:** These rules do not mandate that the structure of spec files must match the structure of test files or code modules.
- One spec file can cover functionality that is implemented by more than one file and that has more than one test file.
- And the tests in one test file can relate to specs from multiple different spec files, where appropriate, though that will be less common.

## Conventions
- Write newlines in specs and spec-citations as `\\n`, which ensures the parsers will recognise a match.

## Enforcement
Check for compliance by running `specd validate` from the project root:
```
specd validate
specd validate -s path/to/specs --tests path/to/tests
```

`specd validate` checks three things: tests without valid spec citations, spec items without related tests, and phantom citations (citations whose text does not appear verbatim in the named spec file). It exits with code 1 if any violations are found.

## Example
### Spec for logging
- always log timestamp, status, and message
- optionally accept a command line arg for case_id and script
- write to logs.json (append only)
- exit 0 on success
- exits non-zero on error
{%- if include_python %}

### Python tests for logging
```python
def test_log_w_no_args():
    """
    Spec: always log timestamp, status, and message [log.md]
    """
    # ...

def test_log_case_id_w_arg():
    """
    Spec: optionally accept a command line arg for case_id and script [log.md]
    """
    # ...

def test_log_script_w_arg():
    """
    Spec: optionally accept a command line arg for case_id and script [log.md]
    """
    # ...
# and so on...
```
{%- endif %}
{%- if include_js_ts %}

### JavaScript/TypeScript tests for logging
```javascript
test("logs with no args", () => {
  // Spec: always log timestamp, status, and message [log.md]
  // ...
});

test("logs with case_id arg", () => {
  // Spec: optionally accept a command line arg for case_id and script [log.md]
  // ...
});
// and so on...
```
{%- endif %}

In this example, the spec item "exit 0 on success" may only need one related test. But the spec item "exits non-zero on error" may have five related tests for five separate error paths. 

Though this example doesn't suggest a need for one test to reference more than one spec item, some integration tests could be structured to intentionally test a related set of spec items and functionality. But do not cast the net of relevance too broadly when relating tests to specs: If a test only tests something incidentally, do not relate it to the incidentally-relevant spec item; relate it only to the one that the test is aimed at.

## Implementation notes
- Use this policy to prevent spec drift and to guide meaningful test creation.
- While this policy promotes both thoughtful additions to, and deletions from, tests as specs evolve, it does *not* prevent the preservation of meaningful regression tests. However, a regression test that catches a specific bug should have a corresponding spec item.
- Working within the policy will often reveal gaps in specs and in tests. Point out gaps to me:
  - where a meaningful test does not have a suitable spec item; or
  - where a spec item is insufficiently tested.

Running tests should NEVER affect actual files in the filesystem, under any cirumstances.
