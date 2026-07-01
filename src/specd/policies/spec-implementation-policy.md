# Implementing Specs

This policy sets guidelines for agents implementing a spec.

## Workflow

Read the relevant spec file(s) before reading any existing code or tests. Write code aimed at implementing the spec cleanly and correctly. Design decisions not addressed by the spec are yours to make; prefer simplicity and maintainability.

Once an initial implementation is in place, run the test suite. Treat the tests as a correctness check, not as a primary guide to implementation. If tests fail, diagnose and resolve.

Do NOT read the tests for the spec you are implementing until you have written the first draft of an implementation and have run the test suite. Your design choices for implementation should not be affected by presumptions written into tests.

Note: this workflow is a deliberate departure from classic TDD, suited to multi-agent development where spec-writing, test-writing, and may be implementation are handled separately and in sequence.

## Issues surfaced during imeplementation

If you notice that a prior architectural or design decision in the codebase is in tension with the correct or idiomatic approach for the new code, stop and raise the conflict with the user before continuing. Do not hack around it; that risks compounding and entrenching a previous mistake.

During spec implementations, agents are free to consider alternatives implementations of existing code, where a refactor would benefit the codebase. But those alternatives should be raised with the user before acting on them.

## Gaps to flag

Before finishing, note and report to the developer:
- any spec item that seems ambiguous or incomplete given functionality being built
- any spec item that appears to have no or insufficient test coverage
- any functionality you implemented that lacks a corresponding spec item or adequate tests
- any functionality you did not implement but that should be implemented and included in the specs
- any test that that is inadequate, testing the wrong thing, or testing with the wrong approach
