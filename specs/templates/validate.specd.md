{% set ENTIRE_VERBATIM_SPEC_ITEM = 'entire verbatim spec line item excluding "- "' %}

{% set PATH_TO_TEST = "path from tests/ with `::` for internal resource delimiters" %}

# Validate test-spec-matching

Validates compliance with test-to-spec matching policy.

# CLI

- `validate` is a valid positional argument to the `specd` command line entrypoint
- When the user calls `validate`, a report is printed showing the results of spec-test matching
- If there are no tests without specs, specs without tests, or phantom citations, the exit code is 0
- If there are any tests without specs, specs without tests, or phantom citations, the exit code is 1

# Test/spec discovery

- A spec item is any line that starts with "- " in a .md file located anywhere under the specd `specs` directory
- A line item in the form of a spec item but inside a comment delineated by `<!-- -->` is not a spec item

# Python test/spec discovery
- a python test file is a file named test_*.py located anywhere under the specd `tests` directory 
- a python test is a function or method with a name in the form `test_*`
- python functions or methods validly cite specs by placing the references on their own lines in the docstring
- python discoverability patterns apply by default

# Javascript and Typescript test/spec discovery
- a JS/TS test file is a file named *.test.{js,jsx,ts,tsx} located anywhere under the specd `tests` directory
- a JS/TS test is a call to a `test()` or `it()` function
- JS/TS functions validly cite specs by placing the references on their own lines in `//` line comments or `/* */` block comments
- JS discoverability patterns only apply if the JS parser is enabled

# Test-to-Spec matching

- A spec is only cited by a test if the citation is in the form `Spec: <{{ENTIRE_VERBATIM_SPEC_ITEM}}> [<spec file name>]`
- Representations of newlines in specs as `\\n` will match up with the same in test-to-spec references

# Report output

- The report starts with the main title "\\n=== Spec Compliance Report ===\\n\\n"

## The tests without specs section

- The main title is followed by a heading: `TESTS WITHOUT VALID SPEC ITEMS (<num>)\\n\\n`
- The tests without specs heading is followed by a list of all functions or methods that do not have valid spec citations
- The list of tests without valid specs is number sequentially
- Each function or method that does not have a valid spec citation is shown on its own line as: `<n>. <{{PATH_TO_TEST}}>`
- If there are no tests without valid spec citations, the report skips that section entirely

## The specs without tests section

- The tests without specs section is followed by a heading: `SPEC ITEMS NOT CITED BY TESTS (<num>)\\n\\n`
- The specs without tests heading is followed by a list of all spec items that are not cited by tests
- The list of uncited specs is number sequentially
- Each spec line item that is not cited by a test is shown on its own line as: `<n>. <spec file name>: <{{ENTIRE_VERBATIM_SPEC_ITEM}}>`
- If there are no uncited specs, the report skips that section entirely

## The phantom citations section

- The specs without tests section is followed by a heading: `PHANTOM CITATIONS (<num>)\\n\\n`
- The phantom citations heading is followed by a list of all test-to-spec references that do not correctly cite a spec
- a test fails to correctly cite a spec if it contains a reference in the form `Spec: <purported_spec> [<purported_file>]` but content of either the `purported_spec` or the file name does not match to an actual spec item or spec file
- The list of phantom citations is number sequentially
- Each function or method that contains a test-to-spec reference that do not correctly cite a spec is shown on its own lines as: `<n>. <{{PATH_TO_TEST}}>\\n   - <the verbatim phantom citation> [<spec file name>]\\n   - <reason>`
- The `reason` for inclusion of a test-to-spec reference in the phantom citations section will be either `spec file not found` or `spec item not found in file`
- If there are no phantom citations, the report skips that section entirely

## The summary

- The phantom citations section is followed by a summary, opening with: `=== Summary ===\\n\\n`
- The summary heading is followed by a summary report
- The first summary line is: `Tests checked:   <n>`
- The second summary line is: `Tests with valid spec items:   <n>`
- The third summary line is: `Tests without valid spec items:   <n>`
- The fourth summary line is: `Spec items without related tests:   <n>`
- The fifth summary line is: `Phantom citations:   <n>`
- The first digits of the numbers of each line of the summary report represented by `<n>` line up
