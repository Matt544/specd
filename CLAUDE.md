# A typical session

Sessions that involve writing code will generally the following distinct steps: 
1. discuss and work out the spec 
2. discuss and work out the tests 
3. write the tests 
4. write the implementation code (i.e. code that implements the spec) 

Do not combine those steps in one prompt response. We will move from one step to the next what I say so.

# Coding style

Most of our code will be written in python.

- Format python code in Black's style with a line length of 88 characters.
- Add spaces before and after all blocks
- Prefer semantically meaningful variable names, even if they are long. E.g.: `avg_pct` is unacceptable; `avgerage_percent` or `avg_percent` are. When an abbreviated name is *highly* conventional, it's fine to use it. E.g. `with open('file.txt', 'r') as f:`, where `f` is conventional and clear. `std` will almost always be wrong, except in a very conventional case like `stdout`.
- In docstrings, always place comments on their own lines, never sharing a line with the opening or closing `"""`.

Documentation:
- Write docstrings for all public modules, functions and classes
- Make those docstrings sufficient but concise 
- Write docstrings also for private modules, functions and classes whenever they would assist a human reader or AI, but keep them sparse 
- Leave brief explanatory comments in the code itself, where it would help

Human and Agent readers will not have the context that you had when writing code. Documentation should supply the context they need to understand and continue the work you started, but not more than that.

Markdown files will use wrapping; don't shorten lines with newlines in `.md` files. 

# Coding approach

Write code for maintainability and extensibility. The project will be evolving iteratively. Implementations must leave us free to swap out different approaches for different parts of the code base, so minimize coupling across parts.

Typically new code can start with simple functions. But don't hesitate to move quickly into an object-oriented style, as soon as you think it would make the code cleaner and more maintainable. You may adopt a functional programming style when you think appropriate, but eschew cleverness.

Lean towards the approach recommended by John Ousterhout in "A Philosophy of Software Design", including preferring deep modules over shallow ones, information hiding and abstraction, and creating narrow APIs.

After writing implementation code, always check if tests are passing. You should run tests liberally as you write code, without checking in with me first.

When changing code, always check whether any documentation or comments need to be updated, as well.

Do not:
- write or refactor beyond scope
- create unrequested files
- add error handling, validation, or defensive code for scenarios that can't occur or aren't part of the spec

If at any point you see a significant gap in the spec that was not discussed, ask me and we will sort it out. That can include defensive measures, feature extensions, or anything else you think I should consider. Point those things out succinctly at the appropriate moment.

# Tests

When I ask you to *recommend* tests:
  - only do that; do not also write tests.
  - first consider changes that can be made to existing tests to bring them into line with anticipated new interfaces; then recommend new tests, only if changes to existing tests are not sufficient.
  - Generally only test interfaces and functionality. Do not recommend tests of implementation details, unless you feel that a particular implementation detail warrants an exception to that rule.
  - default to suggesting tests by method name and a brief description.

When I ask you to *write* tests:
  - only do that; do not also update or write new implementation code.
  - ensure the tests are failing for the right reasons.

# Devaite when told otherwise

Specific instructions in a prompt trump these generic instructions.

---

Read project.md for an orientation.
