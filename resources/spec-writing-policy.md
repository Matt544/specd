# Writing Specs

This policy sets rules and goals for the process of creating spec files.

# Rules
Spec files should:
1. be named in the form `<scope>.md`, under the `specs/` directory
2. contain a title, which would generally reflect the file name (e.g. the file is `specs/logging.md`, the title would likely be "Logging")
3. contain an introductory line at the top of the file describing the domain or context for the spec, but without enumerating or summarising spec items. For example: *"Functionality for selecting and moving case files between the Depot and the Processor."* describes the domain; *"This spec covers case selection, copying, and the casesout REPL command."* would violate the rule by enumerating.
4. contain an itemized list describing the relevant scope of functionality, with list items in the form `- <concise description of some functionality>`.

Spec files live under `specs/` at the project root.

# Conventions
- Always represent newlines in program output using `\\n` (a literal backslash followed by `n`) in spec item text. `specd validate` compares spec item text to test citations as raw text — no escape processing is applied on either side. Test citations must use the same `\\n` convention, regardless of language.
- Group spec items in a way that aids understanding, using headings. Headings are not part of the spec that must be referenced in tests. They are for the benefit of readers, only.

## The purpose
This policy is meant to:
- promote a methodical approach to development that splits code-creation into three distinct steps: (1) spec development; (2) test writing; and (3) spec implementation.
- leave subsequent workers with spec files that preserve work across sessions and accurately record high-level descriptions of system functionality.

The benefits of spec files include that they:
- set the scope for tests, guiding the development of meaningful tests
- represent a resource for agents that introduces them to the system's functionality without asking them to read and interpret any code files, limiting complexity and context window bloat.
- enable agents to pick up where others left off, such that different agents can continue development building on the work of prior agents:
  - Each step can start with a fresh context window, well out of the 'dumb zone'
  - The spec-writer doesn't have to write the tests or implementation
  - The test-writer doesn't need to work through the spec but can rely on its spec `.md` file
  - The implementor can implement the spec without first reading the tests, thus avoiding the temptation to prefer tactical implementations aimed foremost at getting tests to pass, but leaving it with the tests as a resource to check correctness post hoc

# Implementation notes

## Specs are a foundation
Spec files will provide a touch point for subsequent steps in the development process. They should be complete enough to ground an adequate test suite and set the scope of work for implementation. The implementor should not have to make assumptions about what essential functionality should be. 

Make specs thorough with respect to interfaces and intended functionality. All observable behaviour of significance should be specced. For required inputs or preconditions, spec both the success behavior and the failure/error behavior.

A separate test-writing policy mandates that all tests should be related to at least one spec item and will explicitly quote relevant spec items verbatim in their citations. Each spec item should be an accurate, focused, independent, and implementable description of some discrete element of the relevant functionality. Generally, statements that should be tested separately should be separate line items in the spec.

## Specs should avoid constraining design
Spec files should generally be created before any code is written and before architectural and design decisions are made.

They may contain some commitments about what resources will exist and what their interfaces will be, and those might have implications for system design and architecture. But generally specs should avoid constraining design, architecture or implementation decisions for project code or project tests any more than necessary to achieve the functionality specified. Agents implementing the specs should remain free to make design decisions that are right for the codebase. Similarly, spec file structure is not required to mirror other aspects of the project structure, files or modules.

The specs are permitted and expected to evolve. They should improve over time as users and agents learn about the system through its iterative development. Spec titles, file names, intro lines, items, and item organization should all change whenever a change is appropriate. Spec items may be moved between different files; and spec files may be combined or split apart as the project evolves. Such changes should not automatically mandate matching changes in project code implementation. Such changes will sometimes force downstream changes to test suites that are coupled to the specs, but that is by design and encourages agents and users to do the work of keeping tests relevant to the evolving specs. What matters is that the code implements all relevant spec items, not that the code does so within particular design constraints.

## Feedback is permitted
Agents who feel the policy to be an unhelpful constraint or see ways that it is discouraging healthy change in the codebase should voice their opinions. 
