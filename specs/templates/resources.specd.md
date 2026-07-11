# Resources

CLI functionality related to starter-resources for a project.

# CLI

- `resources` is a valid positional argument to the `specd` command line entrypoint
- When the user calls `resources --create`, four documents are created: spec-writing-policy.md, test-writing-policy.md, spec-implementation-policy.md, specd-orientation.md
- When `resources --create` runs without error, there is a message: `The following were created:\\n<list of created files>`
- When `resources --create` runs without error, the message lists created files as `- <target><filename>`

# Target

- If `resources --create` is called without the `--target` option, the resources are created into the cwd
- If `resources --create` is called with the `--target` option, the resources are created at the supplied location
- If the `--target` value supplied does not match an existing directory, there is a warning: `The target directory does not exist. Create it first.\\nThe target was <target sought>`
- If the `--target` value supplied does not match an existing directory, it exits with code 1
- If `--target` is supplied without `--create` there is a message: "--target can only be used with --create"
- If `--target` is supplied without `--create`, it exits with code 1

# --force

- If a document with a name matching a resource that would be created already exists in the target directory, no resources are created
- If a document with a name matching one of the four resources already exists in the target directory, a warning is printed: "\\nThe following files already exist in the target directory:\\n<each existing file name on its own line with "- ">\\nUse --force to overwrite them.\\n"
- If a document with a name matching one of the four resources already exists in the target directory, it exits with code 1
- If a document with a name matching one of the four resources already exists in the target directory and the `--force` option is supplied, any existing same-named documents are overwritten
- If `--force` is supplied without `--create` there is a message: "--force can only be used with --create"
- If `--force` is supplied without `--create`, it exits with code 1

# --list

- When `resources --list` is called, the first line output is `spec-writing: spec-writing-policy.md`
- When `resources --list` is called, the second line output is  `test-writing: test-writing-policy.md`
- When `resources --list` is called, the third line output is `spec-implementation: spec-implementation-policy.md`
- When `resources --list` is called, the fourth line output is `specd-orientation: specd-orientation.md`
- If `resources --list` is called with any other options, a warning is printed: `The --list option can't be combined with other options`
- If `resources --list` is called with any other options, it exits with code 1

# --only

- If `resources --create` is called with `--only <resource key>`, only that resource is created
- If --only is used with an unknown key, a warning is printed: `Unknown resource key: '<key>'. Use --list to get the correct keys.`
- The valid keys for use with `--only` are `spec-writing`, `test-writing`, `spec-implementation`, and `specd-orientation`
- If --only is used with an unknown key, it exits with code 1
- `--only` can be combined with `--target` and `--force`
- If `--only` is supplied without `--create` there is a message: "--only can only be used with --create"
- If `--only` is supplied without `--create`, it exits with code 1

# --help

- Calling `resources` with `--help` or `-h` prints help text
- Help text includes: `usage: specd resources [-h] [--list] [--create] [--only KEY] [--target DIR] [--force]\\n\\n`
- Help text includes: `  -h, --help` + `show this help message and exit`
- Help text includes: `  --list` + `List available resource keys and their filenames`
- Help text includes: `  --create` + `Create resource files in a directory`
- Help text includes: `  --only KEY` + `Create only the named resource (use with --create)`
- Help text includes: `  --target DIR` + `Target directory for --create (default: current working directory)`
- Help text includes: `  --force` + `Overwrite existing files when creating`
- Calling `resources` without options prints the help text

# Content of the created resources

- The created version of spec-writing-policy.md is identical in content to the bundled spec-writing-policy.md
- The created version of spec-implementation-policy.md is identical in content to the bundled spec-implementation-policy.md
- The created version of test-writing-policy.md includes all the static content of the bundled test-writing-policy.md that is unaffected by any jinja syntax
- The created version of specd-orientation.md includes all the static content of the bundled specd-orientation.md that is unaffected by any jinja syntax

## Dynamic content in test-writing-policy.md
{%- set if_testing_policy = 'If test-writing-policy.md will be created' %}
{% set citation_rule_for_python = "- In Python, citations go in the test function's docstring" %}
{% set citation_rule_for_js = "- In JavaScript/TypeScript, citations go in `//` comments inside the test body" %}
{% set not_languages_config = 'there is not a pyproject.toml that includes a tool.specd "languages" key' %}
{% set python_tests_example_heading = "### Python tests for logging" %}
{% set js_tests_example_heading = "### JavaScript/TypeScript tests for logging" %}

{% macro config_languages_includes(language) %}
there is a pyproject.toml that includes {{language}} under its tool.specd "languages" key
{%- endmacro %}
{% macro config_languages_does_not_include(language) %}
there is a pyproject.toml that includes a tool.specd "languages" key without {{language}}
{%- endmacro %}

### Python content included by configuration and by default

- {{if_testing_policy}} and {{config_languages_includes("`python`")}}, point 1 of the `## Rules` section includes: `{{citation_rule_for_python}}`
- {{if_testing_policy}} and {{config_languages_includes("`python`")}}, the file includes `{{python_tests_example_heading}}`

- {{if_testing_policy}} and {{not_languages_config}}, point 1 of the `## Rules` section includes `{{citation_rule_for_python}}`
- {{if_testing_policy}} and {{not_languages_config}}, the file includes `{{python_tests_example_heading}}`

### Python content excluded by configuration

- {{if_testing_policy}} and {{config_languages_does_not_include("`python`")}}, point 1 of the `## Rules` section does not include `{{citation_rule_for_python}}`
- {{if_testing_policy}} and {{config_languages_does_not_include("`python`")}}, the file does not include `{{python_tests_example_heading}}`

### JS/TS content included by configuration and according to installation

- {{if_testing_policy}} and {{config_languages_includes("`javascript` or `typescript`")}}, point 1 of the `## Rules` section includes: `{{citation_rule_for_js}}`
- {{if_testing_policy}} and {{config_languages_includes("`javascript` or `typescript`")}}, the file includes `{{js_tests_example_heading}}` 

- {{if_testing_policy}} and {{not_languages_config}}, and if the `specd[js]` optional dependencies are installed, then point 1 of the `## Rules` section includes `{{citation_rule_for_js}}`
- {{if_testing_policy}} and {{not_languages_config}}, and if the `specd[js]` optional dependencies are installed, the file includes `{{js_tests_example_heading}}`

### JS/TS content excluded by configuration

- {{if_testing_policy}} and {{config_languages_does_not_include("`javascript` or `typescript`")}}, point 1 of the `## Rules` section does not include `{{citation_rule_for_js}}`
- {{if_testing_policy}} and {{config_languages_does_not_include("`javascript` or `typescript`")}}, the file does not include `{{js_tests_example_heading}}`

### JS/TS content excluded according to installation

- {{if_testing_policy}} and {{not_languages_config}}, and if the `specd[js]` optional dependencies are not installed, then point 1 of the `## Rules` section does not include `{{citation_rule_for_js}}`
- {{if_testing_policy}} and {{not_languages_config}}, and if the `specd[js]` optional dependencies are not installed, the file does not include `{{js_tests_example_heading}}`

## Dynamic content in specd-orientation.md
{% set the_orientation_file_contains = "the rendered specd-orientation.md contains" %}

{%- macro when_has_configured_dir(dir) %}
When pyproject.toml provides a `{{ dir }}` dir
{%- endmacro %}

{%- macro when_no_configured_dir(dir) %}
When pyproject.toml does not provide a `{{ dir }}` dir
{%- endmacro %}

{%- macro configured_dir_location_reference(dir) %}
the configured `{{ dir }}` dir + one '/'
{%- endmacro %}

{%- macro default_dir_location_reference(dir) %}
the default `{{ dir }}` dir
{%- endmacro %}

### Location of the templates dir

- {{ when_has_configured_dir("templates") }}, {{ the_orientation_file_contains }}: 'Specs are generated from templates in <{{ configured_dir_location_reference("templates") }}>'
- {{ when_no_configured_dir("templates") }}, {{ the_orientation_file_contains }}: 'Specs are generated from templates in <{{ default_dir_location_reference("templates") }}>'

- {{ when_has_configured_dir("templates") }}, {{ the_orientation_file_contains }}: 'Agents should leave the files under <{{ configured_dir_location_reference("templates") }}> alone'
- {{ when_no_configured_dir("templates") }}, {{ the_orientation_file_contains }}: 'Agents should leave the files under <{{ default_dir_location_reference("templates") }}> alone'

### Location of the specs dir

- {{ when_has_configured_dir("specs") }}, {{ the_orientation_file_contains }}: 'Canonical specs are under <{{ configured_dir_location_reference("specs") }}>'.
- {{ when_no_configured_dir("specs") }}, {{ the_orientation_file_contains }}: 'Canonical specs are under <{{ default_dir_location_reference("specs") }}>'.

- {{ when_has_configured_dir("specs") }}, {{ the_orientation_file_contains }}: 'They are autogenerated into <{{ configured_dir_location_reference("specs") }}>'
- {{ when_no_configured_dir("specs") }}, {{ the_orientation_file_contains }}: 'They are autogenerated into <{{ default_dir_location_reference("specs") }}>'

- {{ when_has_configured_dir("specs") }}, {{ the_orientation_file_contains }}: 'Agents only read spec files under <{{ configured_dir_location_reference("specs") }}>'
- {{ when_no_configured_dir("specs") }}, {{ the_orientation_file_contains }}: 'Agents only read spec files under <{{ default_dir_location_reference("specs") }}>'

- {{ when_has_configured_dir("specs") }}, {{ the_orientation_file_contains }}: 'Do not edit spec files under <{{ configured_dir_location_reference("specs") }}>'
- {{ when_no_configured_dir("specs") }}, {{ the_orientation_file_contains }}: 'Do not edit spec files under <{{ default_dir_location_reference("specs") }}>'

### Location of the tests dir
- {{ when_has_configured_dir("tests") }}, {{ the_orientation_file_contains }}: 'Tests that `specd` is aware of are found under <{{ configured_dir_location_reference("tests") }}>'.
- {{ when_no_configured_dir("tests") }}, {{ the_orientation_file_contains }}: 'Tests that `specd` is aware of are found under <{{ default_dir_location_reference("tests") }}>'.

### Location of the resources dir

- {{ when_has_configured_dir("resources") }}, {{ the_orientation_file_contains }}: '<{{ configured_dir_location_reference("resources") }} + spec-writing-policy.md> (how to write spec items)'
- {{ when_no_configured_dir("resources") }}, {{ the_orientation_file_contains }}: '<{{ default_dir_location_reference("resources") }} + spec-writing-policy.md> (how to write spec items)'

- {{ when_has_configured_dir("resources") }}, {{ the_orientation_file_contains }}: '<{{ configured_dir_location_reference("resources") }} + test-writing-policy.md> (reference format and coverage rules)'
- {{ when_no_configured_dir("resources") }}, {{ the_orientation_file_contains }}: '<{{ default_dir_location_reference("resources") }} + test-writing-policy.md> (reference format and coverage rules)'

- {{ when_has_configured_dir("resources") }}, {{ the_orientation_file_contains }}: '<{{ configured_dir_location_reference("resources") }} + spec-implementation-policy.md> (workflow for implementing specs; unenforced)'
- {{ when_no_configured_dir("resources") }}, {{ the_orientation_file_contains }}: '<{{ default_dir_location_reference("resources") }} + spec-implementation-policy.md> (workflow for implementing specs; unenforced)'
