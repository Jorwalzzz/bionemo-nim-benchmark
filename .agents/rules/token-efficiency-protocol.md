# Token Waste Elimination Protocol

## 1. Simplicity & Minimal Diff Principle
- Solve problems with minimal, high-leverage modifications. Avoid unnecessary abstraction layers or boilerplate.

## 2. Mandatory Line Slicing
- Never view entire source files.
- Always supply `StartLine` and `EndLine` to `view_file` to keep token consumption bounded to the precise region of interest.

## 3. Compact Command Execution
- Do not dump hundreds of lines of terminal output.
- When running tests or tools, focus output on failure snippets or summary pass/fail lines.

## 4. Atomic In-Place Replacements
- Always use `replace_file_content` targeting small, exact anchors rather than rewriting full files.

## 5. Zero Conversational Fluff
- Deliver direct, technical responses formatted in clean GitHub markdown.
- No greetings, pleasantries, or theatrical roleplay.
