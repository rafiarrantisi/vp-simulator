# Regression — FASE 3 (V3 compat real-browser canary, exact V2 experience)

Env: isolated sqlite, `CASE_CONTENT_ENGINE=v2` + canary emails
(`canary@t.co`, `legA@t.co`, `legB@t.co`), StubLLM. Default user tetap V2.
Frontend: NOL diff (tidak ada file `sistemnya/*` sumber yang diubah di Fase 3).

## API / contract evidence (`network/`)

- `canary_cards.json`: canary melihat 3 family cards bentuk V2 persis
  (dengue, fever_child, uti); default user 92 V2 (terbukti terpisah).
- Blind `fam_fever_child`: create 200 → turns → resume. Scan token
  (`working_diagnosis`, `answer_key`, `rubric`, `differential`, `icd`,
  `pnpk`, `management`, nama diagnosis) pada card/create/turn/resume:
  **NONE**. Satu-satunya `fam_*` yang kembali adalah `case_id` yang
  diminta (routing/compat, by design). Katalog menampilkan nama penyakit
  (by design — kartu disease memang bernama).
- Error paths: `fam_nope` → 404 jelas; double-score idempoten (0 vs 0,
  stub); stream abort → transkrip utuh (`user,patient,user`, tanpa corrupt);
  flag-off (`V3_COMPAT_TEST_EMAILS=""`) → canary kembali 92 V2, tanpa
  rollback frontend.
- `voice-status` wired (`stt:true, tts:true`); real-mic STT tidak diuji
  headless (sisa manual).

## Browser journey (desktop practice + mobile OSCE, `QoraV2Screen` murni)

Cards → setup → Practice: opening line, typed Q, streaming reply, refresh
→ reply stub SAMA (persona/variant frozen), PF → assess (Dx lock
"working diagnosis required" bekerja) → Finish → Debrief V2 penuh +
answer-key. OSCE: brief → chat → Exam → PF → (assess/score ter-cover API).
Nol `pageerror`, overflow-x 0, CTA dalam viewport.

## Temuan canary (keduanya diperbaiki server-side, FE 0-diff)

1. Blind family 404 padahal card tampil (count 0): presentation family
   mereferensikan variant lintas-family yang tak pernah lolos filter
   `family_id`. Fix: `resolve_start_variants` — count dan start memakai
   kandidat yang SAMA; kosong tetap 404 jelas, tanpa downgrade diam-diam.
2. Pencocokan email canary case-sensitive (`legA@t.co` diam-diam tetap V2).
   Fix: normalisasi `.strip().lower()`.
3. Persona fallback membawa `working_diagnosis` (belum bocor — persona tak
   pernah ke klien — tapi dihapus preventif untuk blind).

## Catatan konten (bukan blocker canary, untuk kurasi Fase 4)

- Blind fever selalu resolve ke `dengue_001_mild` (deterministik; variasi
  via another-patient). Opening-nya dewasa ("young adult") untuk presentasi
  "Demam pada Anak" — butuh kurasi manusia.
- Dengan StubLLM, angka besar Debrief (0) bisa berbeda dari narasi ringkas
  deterministik (43%) — artefak stub, bukan kontrak; kalibrasi judge
  sesungguhnya butuh LLM key + human grades.
