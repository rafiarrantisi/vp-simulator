// ── Physical-examination step (Aug 2026) ─────────────────────────────────────
// Inserted between the anamnesis chat and the assessment in OSCE mode:
//   1. The student selects which areas they examine + writes what they do/expect.
//   2. "Reveal findings" -> POST /api/v2/sessions/{id}/pf returns the patient's
//      findings for the EXAMINED areas only (isolation rule).
//   3. The revealed data + notes travel with the score request (pf_notes/pf_areas).
// Uses React.createElement (legacy Babel-standalone bundle) + design tokens only.

function QV2PhysicalExam({ caseSummary, sessionId, language, onBack, onContinue }) {
  const [areas, setAreas] = React.useState([]);
  const [notes, setNotes] = React.useState('');
  const [findings, setFindings] = React.useState(null); // {area: text} | null (not yet revealed)
  const [busy, setBusy] = React.useState(false);
  const [err, setErr] = React.useState('');
  const isId = language === 'id';

  const AREA_DEFS = [
    ['general', 'General appearance', 'Pemeriksaan umum'],
    ['skin', 'Skin', 'Kulit'],
    ['head_neck', 'Head & neck', 'Kepala & leher'],
    ['chest', 'Chest', 'Dada'],
    ['abdomen', 'Abdomen', 'Perut'],
    ['limbs', 'Limbs', 'Ekstremitas'],
    ['neuro', 'Neurological', 'Neurologis'],
  ];

  const toggleArea = (k) => setAreas((cur) => cur.indexOf(k) >= 0 ? cur.filter((x) => x !== k) : cur.concat([k]));

  async function reveal() {
    if (!areas.length) {
      setErr(isId ? 'Pilih minimal satu area yang kamu periksa terlebih dahulu.' : 'Select at least one area you examined first.');
      return;
    }
    setBusy(true); setErr('');
    try {
      const d = await qv2Fetch('/api/v2/sessions/' + sessionId + '/pf', { method: 'POST', body: { notes: notes.trim(), areas: areas } });
      setFindings((d && d.findings) ? d.findings : {});
    } catch (e) { setErr(String(e.message || e)); }
    setBusy(false);
  }

  const label = (k) => { const d = AREA_DEFS.find((x) => x[0] === k); return d ? (isId ? d[2] : d[1]) : k; };

  return React.createElement('div', { className: 'au', style: { maxWidth: 'min(680px, calc(100% - 16px))', margin: '0 auto', padding: 16 } },
    React.createElement('button', { onClick: onBack, style: { marginBottom: 14, padding: '6px 12px', borderRadius: 10, border: '1px solid var(--border)', background: 'var(--surface)', fontSize: 12, color: 'var(--text-2)', fontFamily: 'Poppins', cursor: 'pointer' } }, isId ? '← Kembali ke wawancara' : '← Back to interview'),
    React.createElement('div', { style: { fontSize: 20, fontWeight: 800, color: 'var(--text-1)', marginBottom: 4 } }, isId ? '🩺 Pemeriksaan Fisik' : '🩺 Physical Examination'),
    React.createElement('div', { style: { fontSize: 13, color: 'var(--text-2)', marginBottom: 18, lineHeight: 1.6 } },
      isId
        ? 'Tuliskan pemeriksaan fisik yang kamu lakukan — area mana yang kamu periksa dan temuan apa yang kamu harapkan temukan. Setelah itu tekan "Lihat hasil" untuk mendapatkan data temuan pasien.'
        : 'State which areas you examine and what you expect to find. Press "Reveal findings" to get the patient\'s actual findings.'),

    // Area chips
    React.createElement('div', { style: { fontSize: 13, fontWeight: 700, color: 'var(--text-1)', marginBottom: 8 } }, isId ? 'Area yang kamu periksa' : 'Areas you examine'),
    React.createElement('div', { style: { display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 16 } },
      AREA_DEFS.map(function (d) {
        var k = d[0], active = areas.indexOf(k) >= 0;
        return React.createElement('button', { key: k, onClick: () => toggleArea(k), style: {
          padding: '8px 14px', borderRadius: 999, fontSize: 12.5, fontFamily: 'Poppins', cursor: 'pointer', fontWeight: active ? 700 : 500,
          border: '1px solid ' + (active ? 'var(--primary)' : 'var(--border)'),
          background: active ? 'var(--primary-l)' : 'var(--surface)',
          color: active ? 'var(--primary)' : 'var(--text-2)',
        } }, (active ? '✓ ' : '') + (isId ? d[2] : d[1]));
      })),

    // Notes
    React.createElement('div', { style: { fontSize: 13, fontWeight: 700, color: 'var(--text-1)', marginBottom: 8 } }, isId ? 'Catatan pemeriksaan' : 'Examination notes'),
    React.createElement('textarea', {
      value: notes, onChange: (e) => setNotes(e.target.value),
      placeholder: isId ? 'Contoh: palpasi dada kanan, auskultasi jantung, periksa leher — ekspektasi ada pembengkakan...' : 'e.g. palpate the right chest, auscultate the heart, examine the neck — expecting a lump...',
      style: { width: '100%', minHeight: 90, padding: '11px 13px', borderRadius: 12, border: '1px solid var(--border)', background: 'var(--surface)', fontSize: 13.5, fontFamily: 'Poppins', color: 'var(--text-1)', resize: 'vertical', boxSizing: 'border-box' },
    }),

    err && React.createElement('div', { style: { color: 'var(--red-d)', fontSize: 12, marginTop: 10 } }, err),

    React.createElement('button', { onClick: reveal, disabled: busy, style: { width: '100%', marginTop: 16, padding: 13, borderRadius: 12, border: '1px solid var(--primary)', background: 'var(--primary-l)', color: 'var(--primary)', fontSize: 14, fontWeight: 700, fontFamily: 'Poppins', cursor: 'pointer', opacity: busy ? 0.7 : 1 } },
      busy ? (isId ? 'Mengungkap…' : 'Revealing…') : (isId ? '🔍 Lihat hasil pemeriksaan →' : '🔍 Reveal findings →')),

    // Revealed findings
    findings && React.createElement('div', { style: { marginTop: 20 } },
      React.createElement('div', { style: { fontSize: 13, fontWeight: 800, color: 'var(--text-1)', marginBottom: 10 } }, isId ? '📋 Temuan pasien' : '📋 Patient findings'),
      Object.keys(findings).length === 0
        ? React.createElement('div', { style: { fontSize: 12.5, color: 'var(--text-3)', padding: '14px', borderRadius: 12, border: '1px dashed var(--border)', background: 'var(--surface-2)' } },
            isId ? 'Tidak ada temuan tercatat untuk area yang kamu pilih. Periksa kembali area yang dipilih.' : 'No recorded findings for the areas you selected. Review your area choices.')
        : AREA_DEFS.filter((d) => findings[d[0]]).map((d) =>
            React.createElement('div', { key: d[0], style: { padding: 12, borderRadius: 12, background: 'var(--surface-2)', border: '1px solid var(--border)', marginBottom: 10 } },
              React.createElement('div', { style: { fontSize: 12, fontWeight: 700, color: 'var(--primary)', marginBottom: 5 } }, isId ? d[2] : d[1]),
              React.createElement('div', { style: { fontSize: 13, color: 'var(--text-1)', lineHeight: 1.55 } }, findings[d[0]])))),

    // Continue
    React.createElement('button', { onClick: () => onContinue({ notes: notes.trim(), areas: areas }), disabled: busy, style: { width: '100%', marginTop: 20, padding: 13, borderRadius: 12, border: 'none', background: 'var(--primary)', color: '#fff', fontSize: 14, fontWeight: 700, fontFamily: 'Poppins', cursor: 'pointer', opacity: busy ? 0.7 : 1 } },
      isId ? 'Lanjut ke penilaian →' : 'Continue to assessment →'));
}
