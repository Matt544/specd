"""
Tests for the `specd resources` command.
"""

import importlib.resources
import re
import subprocess
import sys
from pathlib import Path

SPECD = [sys.executable, "-m", "specd.cli"]

ALL_RESOURCE_FILES = (
    "spec-writing-policy.md",
    "test-writing-policy.md",
    "spec-implementation-policy.md",
    "specd-orientation.md",
)


def _run(*args, cwd=None):
    """Run specd resources with the given arguments and return CompletedProcess."""
    return subprocess.run(
        SPECD + ["resources"] + list(args),
        capture_output=True,
        text=True,
        cwd=str(cwd) if cwd else None,
    )


def _bundled_content(filename):
    """Return the bytes content of a bundled resource file."""
    resources_dir = importlib.resources.files("specd") / "resources"
    return (resources_dir / filename).read_bytes()


class TestResourcesSubcommand:

    def test_resources_is_valid_subcommand(self):
        """
        Spec: `resources` is a valid positional argument to the `specd` command line entrypoint [resources.md]
        """
        result = subprocess.run(
            SPECD + ["resources", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0


class TestResourcesCopy:

    def test_copy_creates_four_files(self, tmp_path):
        """
        Spec: When the user calls `resources --create`, four documents are created: spec-writing-policy.md, test-writing-policy.md, spec-implementation-policy.md, specd-orientation.md [resources.md]
        """
        result = _run("--create", "--target", str(tmp_path))
        assert result.returncode == 0
        for filename in ALL_RESOURCE_FILES:
            assert (tmp_path / filename).exists(), f"{filename} was not created"

    def test_copy_file_contents_match_bundled(self, tmp_path):
        """
        Spec: The created version of spec-writing-policy.md is identical in content to the bundled spec-writing-policy.md [resources.md]
        Spec: The created version of spec-implementation-policy.md is identical in content to the bundled spec-implementation-policy.md [resources.md]
        Spec: The created version of specd-orientation.md is identical in content to the bundled specd-orientation.md [resources.md]
        """
        _run("--create", "--target", str(tmp_path))
        static_resources = [
            f for f in ALL_RESOURCE_FILES if f != "test-writing-policy.md"
        ]
        for filename in static_resources:
            created = (tmp_path / filename).read_bytes()
            assert created == _bundled_content(filename), (
                f"{filename} content differs from bundled version"
            )

    def test_copy_success_message_with_target(self, tmp_path):
        """
        Spec: When `resources --create` runs without error, there is a message: `The following were created:\\n<list of created files>` [resources.md]
        Spec: When `resources --create` runs without error, the message lists created files as `- <target><filename>` [resources.md]
        """
        result = _run("--create", "--target", str(tmp_path))
        assert "The following were created:" in result.stdout
        listed = [
            line[2:]
            for line in result.stdout.splitlines()
            if line.startswith("- ")
        ]
        for filename in ALL_RESOURCE_FILES:
            expected_path = str(tmp_path / filename)
            assert expected_path in listed, (
                f"Expected '- {expected_path}' in output; got: {listed}"
            )

    def test_copy_success_message_without_target(self, tmp_path):
        """
        Spec: When `resources --create` runs without error, there is a message: `The following were created:\\n<list of created files>` [resources.md]
        Spec: When `resources --create` runs without error, the message lists created files as `- <target><filename>` [resources.md]
        """
        result = _run("--create", cwd=tmp_path)
        assert "The following were created:" in result.stdout
        listed = [
            line[2:]
            for line in result.stdout.splitlines()
            if line.startswith("- ")
        ]
        for filename in ALL_RESOURCE_FILES:
            assert filename in listed, (
                f"Expected '- {filename}' (bare name, no path) in output; got: {listed}"
            )


class TestResourcesTarget:

    def test_copy_with_target_places_files_at_location(self, tmp_path):
        """
        Spec: If `resources --create` is called with the `--target` option, the resources are created at the supplied location [resources.md]
        """
        target = tmp_path / "destination"
        target.mkdir()
        result = _run("--create", "--target", str(target))
        assert result.returncode == 0
        for filename in ALL_RESOURCE_FILES:
            assert (target / filename).exists()

    def test_copy_without_target_places_files_in_cwd(self, tmp_path):
        """
        Spec: If `resources --create` is called without the `--target` option, the resources are created into the cwd [resources.md]
        """
        result = _run("--create", cwd=tmp_path)
        assert result.returncode == 0
        for filename in ALL_RESOURCE_FILES:
            assert (tmp_path / filename).exists()

    def test_nonexistent_target_warns_and_exits_1(self, tmp_path):
        """
        Spec: If the `--target` value supplied does not match an existing directory, there is a warning: `The target directory does not exist. Create it first.\\nThe target was <target sought>` [resources.md]
        Spec: If the `--target` value supplied does not match an existing directory, it exits with code 1 [resources.md]
        """
        nonexistent = tmp_path / "no_such_dir"
        result = _run("--create", "--target", str(nonexistent))
        assert result.returncode == 1
        combined = result.stdout + result.stderr
        assert "The target directory does not exist. Create it first." in combined
        assert str(nonexistent) in combined

    def test_target_without_copy_warns_and_exits_1(self, tmp_path):
        """
        Spec: If `--target` is supplied without `--create` there is a message: "--target can only be used with --create" [resources.md]
        Spec: If `--target` is supplied without `--create`, it exits with code 1 [resources.md]
        """
        result = _run("--target", str(tmp_path))
        assert result.returncode == 1
        combined = result.stdout + result.stderr
        assert "--target can only be used with --create" in combined


class TestResourcesForce:

    def test_existing_file_blocks_copy_and_exits_1(self, tmp_path):
        """
        Spec: If a document with a name matching a resource that would be created already exists in the target directory, no resources are created [resources.md]
        Spec: If a document with a name matching one of the four resources already exists in the target directory, it exits with code 1 [resources.md]
        """
        (tmp_path / "spec-writing-policy.md").write_text("existing", encoding="utf-8")
        result = _run("--create", "--target", str(tmp_path))
        assert result.returncode == 1
        assert not (tmp_path / "test-writing-policy.md").exists()
        assert not (tmp_path / "spec-implementation-policy.md").exists()

    def test_existing_file_warning_format(self, tmp_path):
        """
        Spec: If a document with a name matching one of the four resources already exists in the target directory, a warning is printed: "\\nThe following files already exist in the target directory:\\n<each existing file name on its own line with "- ">\\nUse --force to overwrite them.\\n" [resources.md]
        """
        (tmp_path / "spec-writing-policy.md").write_text("existing", encoding="utf-8")
        (tmp_path / "test-writing-policy.md").write_text("existing", encoding="utf-8")
        result = _run("--create", "--target", str(tmp_path))
        combined = result.stdout + result.stderr
        assert "The following files already exist in the target directory:" in combined
        assert "- spec-writing-policy.md" in combined
        assert "- test-writing-policy.md" in combined
        assert "Use --force to overwrite them." in combined

    def test_only_existing_selected_file_blocks_copy(self, tmp_path):
        """
        Spec: If a document with a name matching a resource that would be created already exists in the target directory, no resources are created [resources.md]
        """
        # A non-selected resource exists — should NOT block --only spec-writing
        (tmp_path / "test-writing-policy.md").write_text("existing", encoding="utf-8")
        result = _run("--create", "--only", "spec-writing", "--target", str(tmp_path))
        assert result.returncode == 0
        assert (tmp_path / "spec-writing-policy.md").exists()

    def test_force_overwrites_existing(self, tmp_path):
        """
        Spec: If a document with a name matching one of the four resources already exists in the target directory and the `--force` option is supplied, any existing same-named documents are overwritten [resources.md]
        """
        for filename in ALL_RESOURCE_FILES:
            (tmp_path / filename).write_text("old content", encoding="utf-8")
        result = _run("--create", "--force", "--target", str(tmp_path))
        assert result.returncode == 0
        for filename in ALL_RESOURCE_FILES:
            assert (tmp_path / filename).read_bytes() == _bundled_content(filename)

    def test_force_without_copy_warns_and_exits_1(self):
        """
        Spec: If `--force` is supplied without `--create` there is a message: "--force can only be used with --create" [resources.md]
        Spec: If `--force` is supplied without `--create`, it exits with code 1 [resources.md]
        """
        result = _run("--force")
        assert result.returncode == 1
        combined = result.stdout + result.stderr
        assert "--force can only be used with --create" in combined


class TestResourcesList:

    def test_list_output(self):
        """
        Spec: When `resources --list` is called, the first line output is `spec-writing: spec-writing-policy.md` [resources.md]
        Spec: When `resources --list` is called, the second line output is  `test-writing: test-writing-policy.md` [resources.md]
        Spec: When `resources --list` is called, the third line output is `spec-implementation: spec-implementation-policy.md` [resources.md]
        """
        result = _run("--list")
        assert result.returncode == 0
        lines = result.stdout.splitlines()
        assert lines[0] == "spec-writing: spec-writing-policy.md"
        assert lines[1] == "test-writing: test-writing-policy.md"
        assert lines[2] == "spec-implementation: spec-implementation-policy.md"
        assert lines[3] == "specd-orientation: specd-orientation.md"

    def test_list_with_other_options_warns_and_exits_1(self):
        """
        Spec: If `resources --list` is called with any other options, a warning is printed: `The --list option can't be combined with other options` [resources.md]
        Spec: If `resources --list` is called with any other options, it exits with code 1 [resources.md]
        """
        result = _run("--list", "--create")
        assert result.returncode == 1
        combined = result.stdout + result.stderr
        assert "The --list option can't be combined with other options" in combined


class TestResourcesOnly:

    def test_only_creates_single_file(self, tmp_path):
        """
        Spec: If `resources --create` is called with `--only <resource key>`, only that resource is created [resources.md]
        """
        result = _run("--create", "--only", "spec-writing", "--target", str(tmp_path))
        assert result.returncode == 0
        assert (tmp_path / "spec-writing-policy.md").exists()
        assert not (tmp_path / "test-writing-policy.md").exists()
        assert not (tmp_path / "spec-implementation-policy.md").exists()
        assert not (tmp_path / "specd-orientation.md").exists()

    def test_only_each_valid_key(self, tmp_path):
        """
        Spec: The valid keys for use with `--only` are `spec-writing`, `test-writing`, `spec-implementation`, and `specd-orientation` [resources.md]
        """
        key_to_file = {
            "spec-writing": "spec-writing-policy.md",
            "test-writing": "test-writing-policy.md",
            "spec-implementation": "spec-implementation-policy.md",
            "specd-orientation": "specd-orientation.md",
        }
        for key, filename in key_to_file.items():
            target = tmp_path / key
            target.mkdir()
            result = _run("--create", "--only", key, "--target", str(target))
            assert result.returncode == 0, f"--only {key!r} failed: {result.stdout}{result.stderr}"
            assert (target / filename).exists(), (
                f"Expected {filename} to be created for key {key!r}"
            )

    def test_only_unknown_key_warns_and_exits_1(self, tmp_path):
        """
        Spec: If --only is used with an unknown key, a warning is printed: `Unknown resource key: '<key>'. Use --list to get the correct keys.` [resources.md]
        Spec: If --only is used with an unknown key, it exits with code 1 [resources.md]
        """
        result = _run("--create", "--only", "bad-key", "--target", str(tmp_path))
        assert result.returncode == 1
        combined = result.stdout + result.stderr
        assert "Unknown resource key: 'bad-key'. Use --list to get the correct keys." in combined

    def test_only_with_target(self, tmp_path):
        """
        Spec: `--only` can be combined with `--target` and `--force` [resources.md]
        """
        target = tmp_path / "out"
        target.mkdir()
        result = _run("--create", "--only", "test-writing", "--target", str(target))
        assert result.returncode == 0
        assert (target / "test-writing-policy.md").exists()

    def test_only_with_force_overwrites(self, tmp_path):
        """
        Spec: `--only` can be combined with `--target` and `--force` [resources.md]
        """
        resource_file = tmp_path / "spec-writing-policy.md"
        resource_file.write_text("old content", encoding="utf-8")
        result = _run(
            "--create", "--only", "spec-writing", "--force", "--target", str(tmp_path)
        )
        assert result.returncode == 0
        assert resource_file.read_bytes() == _bundled_content("spec-writing-policy.md")

    def test_only_without_copy_warns_and_exits_1(self):
        """
        Spec: If `--only` is supplied without `--create` there is a message: "--only can only be used with --create" [resources.md]
        Spec: If `--only` is supplied without `--create`, it exits with code 1 [resources.md]
        """
        result = _run("--only", "spec-writing")
        assert result.returncode == 1
        combined = result.stdout + result.stderr
        assert "--only can only be used with --create" in combined


class TestResourcesHelp:

    def test_help_flag(self):
        """
        Spec: Calling `resources` with `--help` or `-h` prints help text [resources.md]
        Spec: Help text includes: `usage: specd resources [-h] [--list] [--create] [--only KEY] [--target DIR] [--force]\\n\\n` [resources.md]
        Spec: Help text includes: `  -h, --help` + `show this help message and exit` [resources.md]
        Spec: Help text includes: `  --list` + `List available resource keys and their filenames` [resources.md]
        Spec: Help text includes: `  --create` + `Create resource files in a directory` [resources.md]
        Spec: Help text includes: `  --only KEY` + `Create only the named resource (use with --create)` [resources.md]
        Spec: Help text includes: `  --target DIR` + `Target directory for --create (default: current working directory)` [resources.md]
        Spec: Help text includes: `  --force` + `Overwrite existing files when creating` [resources.md]
        """
        result = _run("--help")
        output = result.stdout + result.stderr
        assert (
            "usage: specd resources [-h] [--list] [--create] [--only KEY] [--target DIR] [--force]"
            in output
        )
        assert "-h, --help" in output
        assert "show this help message and exit" in output
        assert "--list" in output
        assert "List available resource keys and their filenames" in output
        assert "--create" in output
        assert "Create resource files in a directory" in output
        assert "--only KEY" in output
        assert "Create only the named resource (use with --create)" in output
        assert "--target DIR" in output
        assert "Target directory for --create (default: current working directory)" in output
        assert "--force" in output
        assert "Overwrite existing files when creating" in output

    def test_h_flag(self):
        """
        Spec: Calling `resources` with `--help` or `-h` prints help text [resources.md]
        """
        result_h = _run("-h")
        result_help = _run("--help")
        assert result_h.stdout == result_help.stdout

    def test_no_options_prints_help(self):
        """
        Spec: Calling `resources` without options prints the help text [resources.md]
        """
        result = _run()
        output = result.stdout + result.stderr
        assert result.returncode == 0
        assert "usage: specd resources" in output


def _bundled_template_text():
    """Return the raw text of the bundled test-writing-policy.md."""
    resources_dir = importlib.resources.files("specd") / "resources"
    return (resources_dir / "test-writing-policy.md").read_text(encoding="utf-8")


def _static_paragraphs(template_text):
    """
    Split template text on double newlines and return paragraphs that
    contain no Jinja syntax ({{ }}, {% %}).
    """
    jinja_pattern = re.compile(r"\{\{|\}\}|\{%|%\}")
    paragraphs = template_text.split("\n\n")
    return [p for p in paragraphs if p.strip() and not jinja_pattern.search(p)]


def _write_pyproject_toml(directory, languages):
    """Write a pyproject.toml with the given languages list under [tool.specd]."""
    langs = ", ".join(f'"{lang}"' for lang in languages)
    content = (
        "[tool.specd]\n"
        f"languages = [{langs}]\n"
    )
    (Path(directory) / "pyproject.toml").write_text(content, encoding="utf-8")


def _create_and_read_test_writing_policy(cwd):
    """
    Run `specd resources --create` with the given cwd and return the
    content of the created test-writing-policy.md.
    """
    target = Path(cwd) / "output"
    target.mkdir(exist_ok=True)
    result = subprocess.run(
        SPECD + ["resources", "--create", "--target", str(target)],
        capture_output=True,
        text=True,
        cwd=str(cwd),
    )
    assert result.returncode == 0, (
        f"resources --create failed: {result.stdout}{result.stderr}"
    )
    return (target / "test-writing-policy.md").read_text(encoding="utf-8")


def _create_and_read_test_writing_policy_no_js(cwd):
    """
    Run `specd resources --create` in a subprocess that blocks tree_sitter
    imports (simulating specd[js] not installed), and return the content
    of the created test-writing-policy.md.
    """
    target = Path(cwd) / "output"
    target.mkdir(exist_ok=True)
    block_script = (
        "import sys\n"
        "sys.modules['tree_sitter'] = None\n"
        "sys.modules['tree_sitter_javascript'] = None\n"
        "sys.modules['tree_sitter_typescript'] = None\n"
        "from specd.cli import main\n"
        "main()\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", block_script,
         "resources", "--create", "--target", str(target)],
        capture_output=True,
        text=True,
        cwd=str(cwd),
    )
    assert result.returncode == 0, (
        f"resources --create failed: {result.stdout}{result.stderr}"
    )
    return (target / "test-writing-policy.md").read_text(encoding="utf-8")


PYTHON_CITATION_RULE = (
    "- In Python, citations go in the test function's docstring"
)
PYTHON_EXAMPLE_HEADING = "### Python tests for logging"

JS_CITATION_RULE = (
    "- In JavaScript/TypeScript, citations go in `//` comments"
    " inside the test body"
)
JS_EXAMPLE_HEADING = "### JavaScript/TypeScript tests for logging"


class TestTestWritingPolicyContent:

    def test_static_content_preserved(self, tmp_path):
        """
        Spec: The created version of test-writing-policy.md includes all the static content of the bundled test-writing-policy.md that is unaffected by any jinja syntax [resources.md]
        """
        content = _create_and_read_test_writing_policy(tmp_path)
        template_text = _bundled_template_text()
        paragraphs = _static_paragraphs(template_text)
        assert len(paragraphs) > 0, "Expected at least one static paragraph"
        for paragraph in paragraphs:
            assert paragraph in content, (
                f"Static paragraph not found in created file:\n{paragraph}"
            )

    def test_python_included_when_language_configured(self, tmp_path):
        """
        Spec: If test-writing-policy.md will be created and there is a pyproject.toml that includes `python` under its tool.specd "languages" key, point 1 of the `## Rules` section includes: `- In Python, citations go in the test function's docstring` [resources.md]
        Spec: If test-writing-policy.md will be created and there is a pyproject.toml that includes `python` under its tool.specd "languages" key, the file includes `### Python tests for logging` [resources.md]
        """
        _write_pyproject_toml(tmp_path, ["python"])
        content = _create_and_read_test_writing_policy(tmp_path)
        assert PYTHON_CITATION_RULE in content
        assert PYTHON_EXAMPLE_HEADING in content

    def test_python_included_by_default_when_no_pyproject_toml(self, tmp_path):
        """
        Spec: If test-writing-policy.md will be created and there is not a pyproject.toml that includes a tool.specd "languages" key, point 1 of the `## Rules` section includes `- In Python, citations go in the test function's docstring` [resources.md]
        Spec: If test-writing-policy.md will be created and there is not a pyproject.toml that includes a tool.specd "languages" key, the file includes `### Python tests for logging` [resources.md]
        """
        # No pyproject.toml at all
        content = _create_and_read_test_writing_policy(tmp_path)
        assert PYTHON_CITATION_RULE in content
        assert PYTHON_EXAMPLE_HEADING in content

    def test_python_included_by_default_with_pyproject_toml_but_no_languages(
        self, tmp_path
    ):
        """
        Spec: If test-writing-policy.md will be created and there is not a pyproject.toml that includes a tool.specd "languages" key, point 1 of the `## Rules` section includes `- In Python, citations go in the test function's docstring` [resources.md]
        Spec: If test-writing-policy.md will be created and there is not a pyproject.toml that includes a tool.specd "languages" key, the file includes `### Python tests for logging` [resources.md]
        """
        # pyproject.toml exists with [tool.specd] but no languages key
        content = "[tool.specd]\nspecs = \"specs\"\n"
        (tmp_path / "pyproject.toml").write_text(content, encoding="utf-8")
        created = _create_and_read_test_writing_policy(tmp_path)
        assert PYTHON_CITATION_RULE in created
        assert PYTHON_EXAMPLE_HEADING in created

    def test_python_excluded_when_not_in_languages(self, tmp_path):
        """
        Spec: If test-writing-policy.md will be created and there is a pyproject.toml that includes a tool.specd "languages" key without `python`, point 1 of the `## Rules` section does not include `- In Python, citations go in the test function's docstring` [resources.md]
        Spec: If test-writing-policy.md will be created and there is a pyproject.toml that includes a tool.specd "languages" key without `python`, the file does not include `### Python tests for logging` [resources.md]
        """
        _write_pyproject_toml(tmp_path, ["javascript"])
        content = _create_and_read_test_writing_policy(tmp_path)
        assert PYTHON_CITATION_RULE not in content
        assert PYTHON_EXAMPLE_HEADING not in content

    def test_js_included_when_language_configured_javascript(self, tmp_path):
        """
        Spec: If test-writing-policy.md will be created and there is a pyproject.toml that includes `javascript` or `typescript` under its tool.specd "languages" key, point 1 of the `## Rules` section includes: `- In JavaScript/TypeScript, citations go in `//` comments inside the test body` [resources.md]
        Spec: If test-writing-policy.md will be created and there is a pyproject.toml that includes `javascript` or `typescript` under its tool.specd "languages" key, the file includes `### JavaScript/TypeScript tests for logging` [resources.md]
        """
        _write_pyproject_toml(tmp_path, ["javascript"])
        content = _create_and_read_test_writing_policy(tmp_path)
        assert JS_CITATION_RULE in content
        assert JS_EXAMPLE_HEADING in content

    def test_js_included_when_language_configured_typescript(self, tmp_path):
        """
        Spec: If test-writing-policy.md will be created and there is a pyproject.toml that includes `javascript` or `typescript` under its tool.specd "languages" key, point 1 of the `## Rules` section includes: `- In JavaScript/TypeScript, citations go in `//` comments inside the test body` [resources.md]
        Spec: If test-writing-policy.md will be created and there is a pyproject.toml that includes `javascript` or `typescript` under its tool.specd "languages" key, the file includes `### JavaScript/TypeScript tests for logging` [resources.md]
        """
        _write_pyproject_toml(tmp_path, ["typescript"])
        content = _create_and_read_test_writing_policy(tmp_path)
        assert JS_CITATION_RULE in content
        assert JS_EXAMPLE_HEADING in content

    def test_js_included_by_default_when_installed(self, tmp_path):
        """
        Spec: If test-writing-policy.md will be created and there is not a pyproject.toml that includes a tool.specd "languages" key, and if the `specd[js]` optional dependencies are installed, then point 1 of the `## Rules` section includes `- In JavaScript/TypeScript, citations go in `//` comments inside the test body` [resources.md]
        Spec: If test-writing-policy.md will be created and there is not a pyproject.toml that includes a tool.specd "languages" key, and if the `specd[js]` optional dependencies are installed, the file includes `### JavaScript/TypeScript tests for logging` [resources.md]
        """
        # No pyproject.toml; specd[js] is installed in the dev env
        content = _create_and_read_test_writing_policy(tmp_path)
        assert JS_CITATION_RULE in content
        assert JS_EXAMPLE_HEADING in content

    def test_js_excluded_when_not_in_languages(self, tmp_path):
        """
        Spec: If test-writing-policy.md will be created and there is a pyproject.toml that includes a tool.specd "languages" key without `javascript` or `typescript`, point 1 of the `## Rules` section does not include `- In JavaScript/TypeScript, citations go in `//` comments inside the test body` [resources.md]
        Spec: If test-writing-policy.md will be created and there is a pyproject.toml that includes a tool.specd "languages" key without `javascript` or `typescript`, the file does not include `### JavaScript/TypeScript tests for logging` [resources.md]
        """
        _write_pyproject_toml(tmp_path, ["python"])
        content = _create_and_read_test_writing_policy(tmp_path)
        assert JS_CITATION_RULE not in content
        assert JS_EXAMPLE_HEADING not in content

    def test_js_excluded_by_default_when_not_installed(self, tmp_path):
        """
        Spec: If test-writing-policy.md will be created and there is not a pyproject.toml that includes a tool.specd "languages" key, and if the `specd[js]` optional dependencies are not installed, then point 1 of the `## Rules` section does not include `- In JavaScript/TypeScript, citations go in `//` comments inside the test body` [resources.md]
        Spec: If test-writing-policy.md will be created and there is not a pyproject.toml that includes a tool.specd "languages" key, and if the `specd[js]` optional dependencies are not installed, the file does not include `### JavaScript/TypeScript tests for logging` [resources.md]
        """
        # No pyproject.toml; simulate specd[js] not installed
        content = _create_and_read_test_writing_policy_no_js(tmp_path)
        assert JS_CITATION_RULE not in content
        assert JS_EXAMPLE_HEADING not in content
