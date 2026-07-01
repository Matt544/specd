{% macro output_format(command) %}
- `{{ command }}` output ends with \\n
- `{{ command }}` separates records with \\n\\n
{% endmacro %}
# Sample

A sample spec demonstrating specd template rendering and validation.

## echo command

- `echo` prints its argument to stdout
{{ output_format("echo") }}

## print command

- `print` prints its argument to stderr
{{ output_format("print") }}
