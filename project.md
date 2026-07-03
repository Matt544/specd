<!-- Intended for agents -->

# Introduction

This project provides resources to facilitate a variation of spec-driven developement using LLMs/agents. The essence of the approach is spec-test-matching: every line item in a spec file is cited by at least one test; and every test cites at least one spec.

# Stack

This is a python project. We will use pytest.

# Project resources

- There is a virtual env at .venv. Use it.
- Tests are under tests/.
- Implementations are under src/.

Do not install packages into the venv. If a packages needs to be installed, tell me, along with the `pip install` command to run.

Agents can run tests with `source .venv/Scripts/activate && pytest tests/` from the project root.

# Current status

This project was written with the human programmer giving directions about functionality and agents writing tests and implementations. It did not follow the spec-test-matching approach that specd itself is designed to facilitate.

The next step is to incrementally bring the codebase into compliance with the specd approach, as set out in the policies at src/specd/policies/ (reproduced at policies/). That will involve:
- Writing specs for functionality that already exists (and potentially tweaking functionality in the process)
- Re-writing tests to comply with the test-writing policy
- Ensuring implementations can run without breaking tests
