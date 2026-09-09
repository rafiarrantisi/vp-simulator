# content/evidence — PNPK clinical evidence authoring (brief §5, §12)

Draft + approved clinical claims, rubric mappings, rationale templates,
pack definitions, and per-variant release bindings. Compiled by
`backend/pipeline/evidence/compiler.py` into immutable packs under
`build/evidence/<pack_sha256>.json`.

Status: EMPTY (Phase 3 fills pilot drafts for fam_uti / fam_dengue adult).
Nothing here is approved until a clinician signs `approval_record_id` AND
the compiler accepts the pack. Unapproved content never reaches runtime.
