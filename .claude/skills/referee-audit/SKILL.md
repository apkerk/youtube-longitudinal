---
name: referee-audit
description: Run a systematic Referee 2 audit on empirical research - code audit, cross-language replication, directory audit, output automation, econometrics audit
user-invocable: true
argument-hint: "[path to project or paper]"
---

Run the Referee 2 systematic audit protocol on the specified research project.

See `referee2.md` in this skill directory for the full audit framework.

The audit covers 5 areas:
1. **Code Audit** — missing values, merge diagnostics, variable construction
2. **Cross-Language Replication** — replicate in R, Stata, AND Python (validate to 6 decimal places)
3. **Directory Audit** — folder structure, relative paths, replication-package readiness
4. **Output Automation** — are tables/figures generated programmatically?
5. **Econometrics Audit** — identification, estimating equations, standard errors, robustness

CRITICAL: Referee 2 NEVER modifies author code. It only creates its own replication scripts.

Target project: $ARGUMENTS
