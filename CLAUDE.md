# CLAUDE.md — weather_analyzer

Guidance for Claude Code when working in this repo.

## Rules

- **Review before committing, and act on it.** Before running `git commit`, always run a
  code review of the staged/working changes first (use the `code-reviewer` agent, or
  `/code-review`). Then **apply every change the reviewer suggests** — fix the issues,
  don't just report them — and only commit after the suggestions are addressed. If a
  suggestion seems wrong or risky, don't silently skip it: make the change or flag it
  explicitly to the user and get agreement before committing. Do not commit unreviewed or
  un-actioned code.

## Conventions

- Record plans in `plans/` and session learnings in `reflections/` (dated filenames,
  `YYYY-MM-DD-topic.md`).
- Target **Python 3.9** — avoid 3.10+ only syntax (`X | Y` runtime unions, `match`) and
  `tomllib`.
