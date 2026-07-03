# Specd Markdown

Syntax highlighting for `*.specd.md` files — Markdown with embedded Jinja2 template syntax.

## What it does

Provides combined highlighting for Markdown and Jinja2 constructs (`{% %}` statements, `{{ }}` expressions, `{# #}` comments) in `.specd.md` files. Also highlights angle-bracket placeholders (`<name>`, `<<name>>`), adds auto-closing pairs for Jinja delimiters, block comment toggling with `{# #}`, and folding for Jinja block structures (`{% macro %}...{% endmacro %}`, `{% for %}...{% endfor %}`, etc.).

## Jinja highlighting inside inline code spans

Outside of backtick spans, Jinja syntax is highlighted by the grammar and picks up colours from your theme automatically. Inside backtick spans (e.g. `` `<{{PATH_TO_TEST}}>` ``), VS Code's Markdown tokeniser takes over and would flatten everything to the inline-code colour. The extension works around this with a decoration provider that applies colours directly to Jinja constructs inside inline code.

Two colours are used — one for the delimiters (`{{`, `}}`, `{%`, `%}`, `{#`, `#}`) and one for the content between them. They default to `#89DDFF` (cyan) and `#FFA657` (orange) respectively. To match them to your theme's Jinja colours, use the token inspector:

1. Place the cursor on a Jinja construct *outside* a backtick span (e.g. on the variable name in `{{ MY_VAR }}`).
2. Open the Command Palette (Ctrl+Shift+P) and run `Developer: Inspect Editor Tokens and Scopes`.
3. Note the **foreground** hex value shown — that is the colour your theme assigns to that token.
4. Repeat for the delimiter (`{{`) to get the delimiter colour.

Then set the colours in your `settings.json`:

```json
"specd-md.jinjaDelimiterColor": "#<colour from step 4>",
"specd-md.jinjaContentColor":   "#<colour from step 3>"
```

Changes take effect immediately without reloading.

## Placeholder highlighting

Angle-bracket placeholders are highlighted throughout the file — inside and outside backtick spans — with a consistent colour applied by the decoration provider. Only the brackets themselves are coloured; the placeholder text is left in the default colour.

Supported forms:

- `<name>` — single angle brackets
- `<<name>>` — double angle brackets
- `<name with spaces>` — multi-word placeholders

The content must begin immediately after the opening bracket (no leading space). The default bracket colour is `#98C379` (green). To change it:

```json
"specd-md.placeholderColor": "#<hex colour>"
```

Changes take effect immediately without reloading.

When a placeholder contains a Jinja expression (e.g. `` `<{{VAR}}>` `` inside a backtick span), the angle brackets get the placeholder colour and the Jinja constructs inside get their own Jinja colours.

## Line wrapping for lists

`*.specd.md` files are intended to be edited with word wrap on. To get wrapped lines to visually hang-indent to the level of the list text (rather than wrapping back to column 1), add these to your `settings.json`:

```json
"[specd-md]": {
    "editor.wordWrap": "on",
    "editor.wrappingIndent": "indent"
}
```

`wrappingIndent: "indent"` indents continuation lines by one tab-width beyond the base indentation of the line. For this to align continuation text with the character after a bullet marker (`- `, `* `, `+ `), **`editor.tabSize` must be set to `2`**. With a larger tab size the continuation will overshoot; with `1` it will fall short. Numbered list markers (`1. `, `10. `) are one or two characters wider than bullet markers, so alignment is approximate for those.

## Installation

### Building the VSIX

From the `editor/vscode/` directory:

```
npx @vscode/vsce package --no-dependencies
```

This produces `specd-md-<version>.vsix`.

### Installing the VSIX

**Option A — From within VS Code (recommended):**

Open the Command Palette (Ctrl+Shift+P) and run `Extensions: Install from VSIX...`, then browse to the `.vsix` file. This installs into whatever profile is currently active.

**Option B — From the command line:**

```
code --install-extension specd-md-0.1.0.vsix
```

Then restart VS Code.

### Gotchas

- **VS Code profiles:** If you use VS Code profiles, extensions are installed per-profile. The command-line `code --install-extension` installs into the *default* profile, which may not be the one you're actually using. If the extension doesn't appear after installing from the command line, use Option A instead — installing from within VS Code ensures it goes into the active profile.
- **Restart required:** After installing, you may need to reload the window (Ctrl+Shift+P → `Developer: Reload Window`) or restart VS Code for the grammar to take effect.
