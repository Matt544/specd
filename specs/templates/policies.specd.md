# Policies

CLI functionality related to starter-policies for a project.

# CLI

- `policies` is a valid positional argument to the `specd` command line entrypoint
- When the user calls `policies --copy`, three documents are created: spec-writing-policy.md, test-writing-policy.md, spec-implementation-policy.md
- The created copy of spec-writing-policy.md is identical in content to the bundled spec-writing-policy.md
- The created copy of test-writing-policy.md is identical in content to the bundled test-writing-policy.md
- The created copy of spec-implementation-policy.md is identical in content to the bundled spec-implementation-policy.md
- When `policies --copy` runs without error, there is a message: `The following were created:\\n<list of created files>`
- When `policies --copy` runs without error, the message lists created files as `- <target><filename>`

# Target

- If `policies --copy` is called without the `--target` option, the policies are created into the cwd
- If `policies --copy` is called with the `--target` option, the policies are created at the supplied location
- If the `--target` value supplied does not match an existing directory, there is a warning: `The target directory does not exist. Create it first.\\nThe target was <target sought>`
- If the `--target` value supplied does not match an existing directory, it exits with code 1
- If `--target` is supplied without `--copy` there is a message: "--target can only be used with --copy"
- If `--target` is supplied without `--copy`, it exits with code 1

# --force

- If a document with a name matching a policy that would be created already exists in the target directory, no policies are created
- If a document with a name matching one of the three policies already exists in the target directory, a warning is printed: "\\nThe following files already exist in the target directory:\\n<each existing file name on its own line with "- ">\\nUse --force to overwrite them.\\n"
- If a document with a name matching one of the three policies already exists in the target directory, it exits with code 1
- If a document with a name matching one of the three policies already exists in the target directory and the `--force` option is supplied, any existing same-named documents are overwritten
- If `--force` is supplied without `--copy` there is a message: "--force can only be used with --copy"
- If `--force` is supplied without `--copy`, it exits with code 1

# --list

- When `policies --list` is called, the first line output is `spec-writing: spec-writing-policy.md`
- When `policies --list` is called, the second line output is  `test-writing: test-writing-policy.md`
- When `policies --list` is called, the third line output is `spec-implementation: spec-implementation-policy.md`
- If `policies --list` is called with any other options, a warning is printed: `The --list option can't be combined with other options`
- If `policies --list` is called with any other options, it exits with code 1

# --only

- If `policies --copy` is called with `--only <policy key>`, only that policy is created
- If --only is used with an unknown key, a warning is printed: `Unknown policy key: '<key>'. Use --list to get the correct keys.`
- The valid keys for use with `--only` are `spec-writing`, `test-writing`, and `spec-implementation`
- If --only is used with an unknown key, it exits with code 1
- `--only` can be combined with `--target` and `--force`
- If `--only` is supplied without `--copy` there is a message: "--only can only be used with --copy"
- If `--only` is supplied without `--copy`, it exits with code 1

# --help

- Calling `policies` with `--help` or `-h` prints help text
- Help text includes: `usage: specd policies [-h] [--list] [--copy] [--only KEY] [--target DIR] [--force]\\n\\n`
- Help text includes: `  -h, --help` + `show this help message and exit`
- Help text includes: `  --list` + `List available policy keys and their filenames`
- Help text includes: `  --copy` + `Copy policy files into a directory`
- Help text includes: `  --only KEY` + `Copy only the named policy (use with --copy)`
- Help text includes: `  --target DIR` + `Target directory for --copy (default: current working directory)`
- Help text includes: `  --force` + `Overwrite existing files when copying`
- Calling `policies` without options prints the help text
