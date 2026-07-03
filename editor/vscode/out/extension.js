"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = require("vscode");
// Matches backtick inline code spans within a single line.
// Group 1: opening backtick(s); group 2: span content.
const INLINE_CODE_RE = /(`+)(.*?)\1/g;
// Matches a complete Jinja construct, capturing delimiter and content separately.
// {{ }} alternative: groups 1 (open), 2 (content), 3 (close).
// {% %} alternative: groups 4, 5, 6.
// {# #} alternative: groups 7, 8, 9.
const JINJA_PARTS_RE = /(\{\{-?)(.*?)(-?\}\})|(\{%-?)(.*?)(-?%\})|(\{#-?)(.*?)(-?#\})/g;
// Matches angle-bracket placeholders: <<content>> or <content>, capturing
// the brackets and content separately so only the brackets are coloured.
// << >> alternative: groups 1 (<<), 2 (content), 3 (>>).
// <  > alternative:  groups 4 (<),  5 (content), 6 (>).
const PLACEHOLDER_RE = /(<<)([^>\s][^>]*)(>>)|(<)([^>\s][^>]*)(>)/g;
let delimDecoration;
let contentDecoration;
let placeholderDecoration;
const DARK_DEFAULTS = {
    jinjaDelimiterColor: '#D7BA7D',
    jinjaContentColor: '#C586C0',
    placeholderColor: '#D7BA7D',
};
const LIGHT_DEFAULTS = {
    jinjaDelimiterColor: '#098658',
    jinjaContentColor: '#AF00DB',
    placeholderColor: '#AF00DB',
};
// Returns the user-set value for a setting, or undefined if not explicitly configured.
// config.get() is unreliable for this — it conflates schema defaults with user values.
function userValue(config, key) {
    const inspected = config.inspect(key);
    return inspected?.globalValue ?? inspected?.workspaceValue ?? inspected?.workspaceFolderValue;
}
function createDecorations() {
    delimDecoration?.dispose();
    contentDecoration?.dispose();
    placeholderDecoration?.dispose();
    const config = vscode.workspace.getConfiguration('specd-md');
    const isLight = vscode.window.activeColorTheme.kind === vscode.ColorThemeKind.Light;
    const defaults = isLight ? LIGHT_DEFAULTS : DARK_DEFAULTS;
    delimDecoration = vscode.window.createTextEditorDecorationType({
        color: userValue(config, 'jinjaDelimiterColor') ?? defaults.jinjaDelimiterColor,
    });
    contentDecoration = vscode.window.createTextEditorDecorationType({
        color: userValue(config, 'jinjaContentColor') ?? defaults.jinjaContentColor,
    });
    placeholderDecoration = vscode.window.createTextEditorDecorationType({
        color: userValue(config, 'placeholderColor') ?? defaults.placeholderColor,
    });
}
function activate(context) {
    createDecorations();
    vscode.window.visibleTextEditors.forEach(updateDecorations);
    let debounce;
    context.subscriptions.push(vscode.window.onDidChangeActiveColorTheme(() => {
        createDecorations();
        vscode.window.visibleTextEditors.forEach(updateDecorations);
    }), vscode.workspace.onDidChangeConfiguration(e => {
        if (e.affectsConfiguration('specd-md')) {
            createDecorations();
            vscode.window.visibleTextEditors.forEach(updateDecorations);
        }
    }), vscode.window.onDidChangeActiveTextEditor(editor => {
        if (editor) {
            updateDecorations(editor);
        }
    }), vscode.workspace.onDidChangeTextDocument(event => {
        clearTimeout(debounce);
        debounce = setTimeout(() => {
            vscode.window.visibleTextEditors.forEach(editor => {
                if (editor.document === event.document) {
                    updateDecorations(editor);
                }
            });
        }, 300);
    }));
}
function deactivate() {
    delimDecoration?.dispose();
    contentDecoration?.dispose();
    placeholderDecoration?.dispose();
}
function updateDecorations(editor) {
    if (editor.document.languageId !== 'specd-md') {
        return;
    }
    const doc = editor.document;
    const delimRanges = [];
    const contentRanges = [];
    const placeholderRanges = [];
    for (let line = 0; line < doc.lineCount; line++) {
        const text = doc.lineAt(line).text;
        // Placeholders: scan the entire line, colouring only the brackets.
        PLACEHOLDER_RE.lastIndex = 0;
        let placeholderMatch;
        while ((placeholderMatch = PLACEHOLDER_RE.exec(text)) !== null) {
            const isDouble = placeholderMatch[1] !== undefined;
            const open = isDouble ? placeholderMatch[1] : placeholderMatch[4];
            const content = isDouble ? placeholderMatch[2] : placeholderMatch[5];
            const close = isDouble ? placeholderMatch[3] : placeholderMatch[6];
            const matchStart = placeholderMatch.index;
            const openEnd = matchStart + open.length;
            const contentEnd = openEnd + content.length;
            const closeEnd = contentEnd + close.length;
            placeholderRanges.push(new vscode.Range(new vscode.Position(line, matchStart), new vscode.Position(line, openEnd)));
            placeholderRanges.push(new vscode.Range(new vscode.Position(line, contentEnd), new vscode.Position(line, closeEnd)));
        }
        // Jinja constructs: scan inside inline code spans only.
        INLINE_CODE_RE.lastIndex = 0;
        let codeMatch;
        while ((codeMatch = INLINE_CODE_RE.exec(text)) !== null) {
            const spanStart = codeMatch.index + codeMatch[1].length;
            const spanContent = codeMatch[2];
            JINJA_PARTS_RE.lastIndex = 0;
            let jinjaMatch;
            while ((jinjaMatch = JINJA_PARTS_RE.exec(spanContent)) !== null) {
                const base = jinjaMatch[1] !== undefined ? 1
                    : jinjaMatch[4] !== undefined ? 4
                        : 7;
                const openDelim = jinjaMatch[base];
                const innerContent = jinjaMatch[base + 1];
                const closeDelim = jinjaMatch[base + 2];
                const matchStart = spanStart + jinjaMatch.index;
                const openEnd = matchStart + openDelim.length;
                const contentEnd = openEnd + innerContent.length;
                const closeEnd = contentEnd + closeDelim.length;
                delimRanges.push(new vscode.Range(new vscode.Position(line, matchStart), new vscode.Position(line, openEnd)));
                contentRanges.push(new vscode.Range(new vscode.Position(line, openEnd), new vscode.Position(line, contentEnd)));
                delimRanges.push(new vscode.Range(new vscode.Position(line, contentEnd), new vscode.Position(line, closeEnd)));
            }
        }
    }
    // Placeholders first, then Jinja — so Jinja colours win where they overlap
    // (e.g. <{{VAR}}> inside a backtick span gets placeholder colour on the
    // angle brackets and Jinja colours on the {{ }} and variable name).
    editor.setDecorations(placeholderDecoration, placeholderRanges);
    editor.setDecorations(delimDecoration, delimRanges);
    editor.setDecorations(contentDecoration, contentRanges);
}
//# sourceMappingURL=extension.js.map