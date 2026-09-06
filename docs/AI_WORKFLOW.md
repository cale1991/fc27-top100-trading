# AI-assisted development workflow

This workflow keeps the project moving quickly while giving you clear places to supervise decisions. You are not expected to write code to prove that you understand it. Your most valuable checks are whether the goal is right, the proposed behavior makes practical sense, the important rules stay intact, and the evidence really supports “done.”

## Default flow for substantial work

```text
idea or problem
  -> product thinking / research / requirement clarification when useful
  -> repository inspection and repo-grounded plan
  -> docs/tasks/<task-name>.md
  -> bounded implementation
  -> tests and runtime verification
  -> strong review for important or risky work
  -> implementation worker fixes approved findings
  -> plain-English final explanation
  -> commit and push when you authorize it
```

### 1. Shape the request

Use ChatGPT Web when outside research, product thinking, competing UX choices, or requirement clarification would help. It is optional when the request is already concrete.

For this project, make the desired user outcome explicit and name any non-negotiable boundaries: FC26 rehearsal versus FC27 target behavior, PC executability, manual EA market actions, preservation of historical data, and whether external/provider access is permitted.

### 2. Inspect before planning

For substantial work, use Codex Sol or an equivalent strong reasoning agent to inspect the actual repository before planning. It should trace the relevant path rather than rely on a generic architecture guess. Depending on the task, that path may be:

```text
provider -> immutable raw capture -> normalization/identity/market segment
         -> PostgreSQL observation -> point-in-time feature/model
         -> opportunity or portfolio service -> FastAPI -> Next.js PWA
```

The inspection should identify the root cause, affected layers, existing abstraction to reuse, migration needs, provider/rights implications, and existing regression tests. A visible PWA symptom may originate in ingestion, evidence semantics, accounting, or a backend query.

### 3. Make the task contract

Create `docs/tasks/<task-name>.md` from `docs/tasks/TASK_TEMPLATE.md` when work is cross-layer, ambiguous, risky, migration-bearing, provider-facing, or likely to take several implementation steps.

The task file is the shared contract. The most important parts for you to review are:

- Goal and desired behavior: is this the outcome you actually want?
- Constraints and invariants: what must not be broken?
- Non-goals: is scope staying under control?
- Acceptance criteria: what observable evidence will prove completion?
- Risks and migration implications: could existing data, trading logic, or runtime be damaged?

Requirements can be updated as you learn. Important discoveries and changed assumptions should be recorded instead of hidden in chat history.

### 4. Implement the bounded plan

Use Luna or an equivalent cost-efficient implementation agent for a well-specified task. The worker should reuse current services, models, routers, components, configuration, and tests; it should not reinterpret the task as permission to redesign the system.

The lead agent remains responsible for joining the pieces, resolving conflicts, and checking that frontend behavior, backend contracts, migrations, schedules, and persistence semantics agree.

### 5. Verify in layers

Run the cheapest relevant checks first, then the realistic runtime checks the change needs:

- Python: targeted tests while iterating, then `python -m ruff check src tests scripts` and `python -m pytest -q` when relevant.
- Frontend: `npm run build` from `web/`, plus the affected screen/API flow.
- Database: migration-chain inspection and `alembic upgrade head`; test both fresh installation and relevant existing-database upgrade paths.
- Integrated runtime: Docker Compose services, smoke checks, worker/Beat scheduling, and provider behavior when the environment and authorization permit it.
- Phase 2 vacation-PC deployment: `powershell -ExecutionPolicy Bypass -File .\scripts\phase2_runtime_check.ps1`.

Verification must protect the project's special failure boundaries: reference is not execution, markets stay separate, input is point-in-time safe, provider failures remain isolated, existing data survives migrations, and portfolio tax/cost-basis math stays exact.

“Not runnable in this environment” is a valid result, but it must be reported as not run—not converted into a claim of success.

### 6. Review important work

Use Sol or an equivalent strong reviewer for changes involving architecture, database evolution, provider semantics/rights, ingestion and identity, accounting, model/backtest correctness, cross-market behavior, or multiple application layers.

The review should look for concrete defects and regressions, not generate cleanup for its own sake. The implementation worker then fixes findings that the lead accepts, and the affected checks run again. Astra is reserved for exceptional cases where the problem truly needs frontier-level end-to-end reasoning or strong earlier attempts failed.

### 7. Explain and hand off

The final explanation should tell you:

- the root cause;
- what changed and why it works;
- how data/control now moves through the relevant parts;
- what was deliberately kept unchanged;
- which checks ran and their results;
- what would probably fail if the solution were wrong;
- 2–5 files worth reading and what to notice in each.

This is the learning checkpoint. Focus on system boundaries and cause-and-effect before syntax.

### 8. Commit and push

After you accept the outcome, use Git to review the diff, commit a coherent change, and push when authorized. A commit should match the task contract; unrelated cleanup belongs in another task. Never include `.env`, API keys, tokens, raw private evidence, or generated runtime data.

## When a smaller workflow is enough

A small, local, low-risk change—such as wording, a focused configuration correction, or an obvious one-file bug with an existing test—can skip ChatGPT Web, the task file, model delegation, and separate review. It still requires inspection of the relevant code, a scoped change, an appropriate check, and an honest final summary.

Escalate to the full workflow when a “small” change touches persisted data, evidence/execution semantics, provider access, market identity, accounting, scheduling, public posting, or more than one major layer. In this repository, those boundaries create more risk than the number of changed lines suggests.
