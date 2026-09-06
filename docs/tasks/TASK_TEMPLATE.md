# Task: <short title>

> Use this for substantial work. Delete unused optional prompts rather than filling them with boilerplate. Update the file as discoveries change the plan.

## Goal

What practical outcome should exist when this task is complete?

## Why it matters

Why is this worth changing now? What user or system problem does it solve?

## Current behavior / observed symptom

What happens today? Include reproducible examples, screenshots, logs, IDs, or timestamps when useful. Separate observed facts from assumptions.

## Desired behavior

Describe the observable result. Include FC26/FC27 and market segment where relevant.

## Root-cause findings

What actually causes the behavior, and which layer owns the fix? If not known yet, write the leading hypotheses and what evidence will distinguish them.

## Relevant architecture / files

- `<path>` — why it matters
- `<path>` — why it matters

Name existing abstractions to reuse. Note any dated document that is context rather than current truth.

## Data / control flow

Show the affected path in a few lines, for example:

```text
provider -> raw capture -> normalization -> market-segment observation
         -> feature/service -> FastAPI -> Next.js screen
```

State where validation, persistence, transaction commit, and user/manual action occur.

## Constraints and invariants

- [ ] Existing architecture is preserved unless redesign is explicitly approved.
- [ ] FC26 rehearsal data and applicable upgrade paths are preserved.
- [ ] PC executable evidence remains separate from other/unknown market research.
- [ ] Reference prices are not treated as execution observations or portfolio marks.
- [ ] Raw provenance and point-in-time/knowledge-time correctness are preserved.
- [ ] Provider rights, optionality, quotas, and secret redaction are preserved.
- [ ] EA market execution remains manual.
- [ ] Exact 5% EA tax/accounting semantics are preserved where relevant.

Add only task-specific invariants below; remove checklist items that truly do not apply.

## Non-goals

What nearby work is intentionally excluded?

## Implementation plan

1. Concrete change with responsible layer/file.
2. Concrete change.
3. Tests and runtime verification.

For each step, say what stays unchanged when that is important.

## Risks / edge cases

- Untrusted or malformed provider input
- Wrong/unknown card identity or market segment
- Stale, missing, or conflicting observations
- Retry, rate-limit, partial failure, rollback, or session failure
- Empty data and first-run state
- Duplicate processing versus valid later time-series observations
- Timezone, knowledge-time, and lookahead errors
- Partial portfolio fills/sales and EA tax rounding

Keep only relevant items and add task-specific cases.

## Migration implications (optional)

- Schema/model changes:
- Alembic revision and predecessor:
- Existing-row/backfill behavior:
- Fresh-install behavior:
- Upgrade paths tested:
- Rollback/data-retention decision:

Write “None” only after checking whether persisted contracts change.

## Cross-layer implications (optional)

- API contract:
- Backend/service:
- Frontend/PWA:
- Provider/access/rights:
- Persistence/provenance:
- Scheduler/Redis/Celery:
- Modeling/backtest:
- Deployment/runtime:

Delete irrelevant lines.

## Acceptance criteria

- [ ] Observable outcome written in user language
- [ ] Important invariant proven
- [ ] Failure/empty/stale path proven where relevant
- [ ] Existing data/upgrade behavior proven where relevant
- [ ] No unrelated behavior changed

Replace these prompts with specific, testable criteria.

## Tests / verification

Record commands and actual results. Never mark an unrun check as passing.

| Check | Why | Result |
|---|---|---|
| Targeted regression test | Proves the root-cause fix | Not run |
| `python -m ruff check src tests scripts` | Python static checks | Not run |
| `python -m pytest -q` | Python regression suite | Not run |
| `npm run build` in `web/` | Next.js/TypeScript production build | Not run |
| `alembic upgrade head` | Migration/runtime schema | Not run / not applicable |
| Docker/smoke/provider check | Integrated behavior | Not run / not applicable |

Document environment limitations and any manual verification required.

## Review findings (optional)

| Finding | Decision | Fix / reason |
|---|---|---|
|  |  |  |

Include reviewer, severity, affected file, and rerun checks when useful.

## Final outcome

Complete after implementation: root cause, what changed, why it works, important invariants preserved, and any remaining limitation/follow-up.

## What I should understand

Explain the 1–3 system concepts that help the user supervise this area next time. Prefer cause-and-effect and boundaries over syntax.

## Files worth reading

- `<path>` — what to look for
- `<path>` — what to look for

Choose 2–5 files that reveal the relevant flow; do not list every changed file.
