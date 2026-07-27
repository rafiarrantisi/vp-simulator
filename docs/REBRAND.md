# REBRAND.md — OphthaSim → {{PRODUCT_NAME}} inventory & safe plan (§3)

> 255 occurrences of `OphthaSim/ophtha/OPHTHA` across 80 files. They are **not**
> all branding. This document classifies them so the eventual rename is one
> coordinated, low-risk change — and so we do NOT break the live deploy or touch
> clinical content. **Final name is owner's pick (§14.1); until then `{{PRODUCT_NAME}}`.**

---

## Category A — Branding copy (swap when the name is chosen)

User-facing product name in UI copy / titles. Safe to route through one constant.

- Frontend copy: `sistemnya/index.html` (title), `screens.jsx`, `onboarding.jsx`,
  `auth-screens.jsx`, `components.jsx`, `learning-extras.jsx`, `profile-features.jsx`,
  `simulator.jsx`, `tutorial-scripts.js`, `Virtual Patient Simulator.html`.
- Backend: `app/config.py` `app_name` (`"OphthaSim Backend"`) and `llm_app_title`
  (`"OphthaSim"`, sent to OpenRouter).

**Plan:** introduce a single source of truth —
- Backend: add `product_name: str` to `Settings` (env `PRODUCT_NAME`), default
  `"{{PRODUCT_NAME}}"` until chosen; reference it from `app_name`/`llm_app_title`.
- Frontend: one exported constant (e.g. `PRODUCT_NAME` in a small `engine/brand.js`)
  referenced by copy. NB: this is **copy**, not `design.css`/markup geometry, so it
  does not violate the byte-identical design discipline — but re-verify the CSS hash
  (`index-Bj97HpXF.css`) after the swap per the project rule.

Then the final swap = set one env var + one constant.

---

## Category B — Functional identifiers (DO NOT mass-replace; coordinated infra rename only)

These are not branding; renaming them is a breaking, deploy-coupled change. Leave
until a deliberate infra cutover (Phase 6), each done with its migration:

- `OPHTHA_API_BASE` — the `window` global that selects API vs. static engines,
  used across `sistemnya/engine/*.js` + `screens.jsx`. Renaming requires touching
  every consumer + the injection point simultaneously. **High risk; defer.**
- `ophtha-backend.service` (systemd unit), `nginx-ophtha.conf`,
  `nginx-upgrade-map.conf`, `deploy/*.sh`, `docker-compose.yml` service names.
- Live domain `ophtasim.duckdns.org`; dev/prod DB files `ophtha_dev.db` /
  `ophtha_prod.db`.

These can keep the `ophtha` identifier indefinitely without any user-visible
impact. Rename only if/when desired, as a separate migration.

---

## Category C — DO NOT TOUCH (clinical content & taxonomy, §3)

- Legacy `data-kasus/kasus-*.md` — genuine ophthalmology clinical cases.
- Schema-v2 `content/cases/oph_*.md` — the `oph_` prefix is the **specialty code**
  for ophthalmology (see `docs/SCHEMA_v2.md` ID convention), not branding.
- `specialty: ophthalmology`, ICD codes, clinical references — taxonomy, not brand.

The 31 eye cases stay as **one specialty among many** (§3/§5.4).

---

## Category D — Docs (update narrative at rebrand time)

`docs/ARCHITECTURE.md`, `HANDOFF.md`, `AUDIT.md`, `all-plan/*` — historical/contract
docs. Update the product-name references when the name lands; no rush, no runtime impact.

---

## Execution order (when the owner picks a name)

1. Set `PRODUCT_NAME` (backend env + frontend constant).
2. Swap Category A copy to reference it; re-verify FE build + CSS hash unchanged.
3. Update Category D docs.
4. (Optional, Phase 6) Coordinated infra rename of Category B during a maintenance window.
5. Never touch Category C.
