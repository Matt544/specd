{% macro question_arg(method_name) %}
- The `question` arg can be a `Question` id or the first n characters of a `Question.key` (string) (re: `{{ method_name }}`)
- If a string value for `question` matches more than one Question, the report says "The `question` arg matches more than one Question's `key`: {comma separated matching keys}" (re: `{{ method_name }}`)
- If the `question` arg does not match to a Question, there is a ValueError (re: `{{ method_name }}`)
{% endmacro %}
# Demo

A demo spec showing how a Jinja2 template produces a spec file.

## Frequency method

{{ question_arg("frequency") }}

## Data method

{{ question_arg("data") }}

## Datum method

{{ question_arg("datum") }}
