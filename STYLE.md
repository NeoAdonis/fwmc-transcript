# Style guide

The following style guide is intended to be a reference for contributors to this code base. Contributions are expected to follow these guidelines, which help maintain consistency and readability in the code and content. Deviations are accepted when there's a good reason for them, and minor ones don't block a contribution on their own; they may be pointed out during review and fixed later.

## Writing

The following conventions apply to all written content, such as transcripts, summaries and documentation:

- Use proper capitalization for proper nouns. Use the [hololive Talent page](https://hololive.hololivepro.com/en/talents/) as reference for talent and generation names.
- Separate Japanese honorifics with a hyphen (e.g., Tanigo-san, Moco-chan).
- Do not introduce intentional misspellings unless it's relevant to the context of the content. For example, avoid spelling 'Ruffians' as 'Wuffians'.

## Formatting

This code base is formatted with [Ruff](https://docs.astral.sh/ruff/), following the [Ruff Formatter Style Guide](https://docs.astral.sh/ruff/formatter/#style-guide), which is designed to be a drop-in replacement for [Black](https://black.readthedocs.io/en/stable/the_black_code_style/current_style.html). Because it uses the default settings, `ruff format` can be called as-is to ensure that the code format is in good shape.

Important conventions:

- 4 space indentation, no tabs.
- Maximum line width of 88 characters, including indentation.
- Double quotes for strings, unless using single quotes avoids escaping.
- Two blank lines around top-level functions and classes, and one blank line around methods. At most two blank lines in a row at module level and one inside functions and classes.
- Trailing commas in comma-separated lists split across multiple lines. A trailing comma in a list that fits on one line (the "magic trailing comma") keeps it split, one element per line.
- No trailing whitespace on the end of any line.
- Each decorator on its own line, indented to the level of the decorated item.

The formatter doesn't sort imports. To sort them, run `ruff check --select I --fix` before `ruff format`.

Comments should follow [PEP 8](https://peps.python.org/pep-0008/#comments) recommendations. The formatter fixes some spacing issues, but it doesn't wrap or reflow comments, so take special care when writing them. In short:

- A single space must be placed after the `#`.
- Prefer to put a comment on its own line. If put after code, it must be separated by two spaces.
- Comments should be complete sentences; they should start with a capital letter and end with a period.
- Comment lines never go beyond the 88-character line limit.

Additionally, the following conventions should be followed for docstrings, as described in [PEP 257](https://peps.python.org/pep-0257/):

- Docstrings use triple double quotes (`"""`).
- First line should consist of a brief summary as its own paragraph, ending with a period. One line if possible; two lines at most.
- Separate each paragraph by a single blank line.
- Module docstrings, if any, go at the top of the file, before the imports.

Refer to the [Ruff Formatter Style Guide](https://docs.astral.sh/ruff/formatter/#style-guide) for more details. In the rare cases where the formatted output hurts readability, formatting can be disabled with `# fmt: off`/`# fmt: on` or `# fmt: skip`.

## Linting

Beyond formatting, code should be checked with the [Ruff linter](https://docs.astral.sh/ruff/linter/), which catches common mistakes and non-idiomatic code. The code base uses the default set of rules, so `ruff check` can be called as-is. When a rule doesn't apply to a specific case, it can be silenced on the affected line with a `# noqa: <code>` comment (e.g., `# noqa: F841`).

## Commit messages

Commit messages follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification. Older commits don't follow it, as the convention was adopted later in the project's history.

```text
<type>[(optional scope)]: <description>

[optional body]
```

Messages follow the 50/72 rule: the subject line is at most 50 characters long, and body lines are wrapped at 72 characters. If the subject can't fit all the relevant details, move them to the body.

### Types

- `feat`: a new feature or behavior.
- `fix`: a bug fix.
- `refactor`: a code change that neither fixes a bug nor adds a feature.
- `style`: formatting changes that don't affect the meaning of the code.
- `test`: new or updated tests.
- `docs`: documentation changes only, including docstrings.
- `build`: changes to build systems, dependencies or packaging.
- `chore`: other maintenance tasks, such as configuration or example files.

Mixing several types in a single commit should be avoided whenever possible, so that commits stay focused. When it can't be avoided, the type of the main change is used.

### Scopes

A scope names the part of the code base that a commit changes. It should be short and lowercase, and it's usually one of the following:

- A top-level directory or project area (e.g., `morning`, `songs`).
- A module or script, when the change is limited to it.
- A well-known group of files that spans several directories (e.g., `reqs` for the requirements files).

Before picking a new scope, check the commit history and reuse an existing one if it fits.

A scope should be added whenever possible, as long as the change clearly belongs to a single scope. Small adaptations in other parts are fine. Otherwise, leave the scope out.
