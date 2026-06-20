# content/scaffold — breadth backlog & MLA scaffold (Phase 2, moat P3)

This folder seeds **breadth-at-launch**: the list of cases to author across
specialties (`BUILD_PLAN_pivot_v4.md` §5.4).

## `cases_backlog.csv`
The actionable authoring queue. Columns: `specialty, slug, presentation,
target_condition, difficulty, mode`. Consumed directly by the pipeline:

```bash
cd backend
python -m tools.author_case --batch ../content/scaffold/cases_backlog.csv
```

Each row → one drafted, lint-checked case in `content/cases/<id>.md` at
`status: in_review`. **Requires a real `LLM_API_KEY` (+ optional `AUTHOR_MODEL`)**
— StubLLM cannot author clinical content.

This seed covers **all 10 launch specialties** (28 rows). Combined with the
**10 cases already authored** (9 ophthalmology + 1 internal-medicine appendicitis),
authoring this backlog reaches the **40–60 launch target** (§14.4 — owner confirms
the exact count and whether to add more per specialty).

## MLA scaffold (upstream source)
The master vocabulary for `presentation` / `target_condition` is the **GMC MLA
Content Map** (~212 presentations, ~430 conditions; `gmc-uk.org/mla`). The backlog
above is a curated, MLA-aligned starter subset.

> **TODO (data task):** generate the full `mla_presentations.csv` and
> `mla_conditions.csv` (presentation, condition, area-of-clinical-practice) from
> the official GMC MLA PDF, then expand `cases_backlog.csv` from them. This needs
> the source PDF and is a content task, not a code task.

## Workflow (§5.3)
1. Pick rows from the backlog (or add your own).
2. `author_case --batch` drafts schema-valid cases → `in_review`.
3. Light human review (clinician) edits + sets `status: published`.
4. CI runs `tools/lint_case --all` as the quality gate.
