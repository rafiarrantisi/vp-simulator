// ============================================================
// Qora — i18n translations helper (EN + ID)
// ------------------------------------------------------------
// Simple key-value translation map. Loaded after region detection.
// Exposes window.__t(key) -> localized string; falls back to English.
// Add languages by extending the TRANSLATIONS map.
// ============================================================

window.QORA_LOCALE = 'en'; // set by region detection

window.QORA_TRANSLATIONS = {
  // ── Dashboard ──
  'dashboard.title': { en: 'Dashboard', id: 'Beranda' },
  'dashboard.welcome': { en: 'Welcome back', id: 'Selamat datang kembali' },
  'dashboard.your_progress': { en: 'Your progress', id: 'Progres Anda' },
  'dashboard.cases_completed': { en: 'Cases completed', id: 'Kasus selesai' },
  'dashboard.sessions': { en: 'Sessions', id: 'Sesi' },
  'dashboard.streak': { en: 'Day streak', id: 'Streak hari' },
  'dashboard.xp': { en: 'XP earned', id: 'XP diperoleh' },
  'dashboard.avg_score': { en: 'Average score', id: 'Rata-rata skor' },
  'dashboard.continue_practising': { en: 'Continue practising', id: 'Lanjutkan latihan' },
  'dashboard.browse_cases': { en: 'Browse cases', id: 'Lihat kasus' },
  'dashboard.skill_breakdown': { en: 'Skill breakdown', id: 'Rincian kemampuan' },
  'dashboard.recent_sessions': { en: 'Recent sessions', id: 'Sesi terbaru' },
  'dashboard.no_sessions': { en: 'No sessions yet — start your first case!', id: 'Belum ada sesi — mulai kasus pertama Anda!' },
  'dashboard.dim_history_coverage': { en: 'History', id: 'Anamnesis' },
  'dashboard.dim_red_flags': { en: 'Red flags', id: 'Red flag' },
  'dashboard.dim_ice_fife': { en: 'ICE/FIFE', id: 'ICE/FIFE' },
  'dashboard.dim_questioning_technique': { en: 'Questioning', id: 'Teknik bertanya' },
  'dashboard.dim_communication': { en: 'Communication', id: 'Komunikasi' },
  'dashboard.dim_diagnostic_reasoning': { en: 'Reasoning', id: 'Penalaran' },
  'dashboard.dim_investigations': { en: 'Investigations', id: 'Pemeriksaan' },
  'dashboard.dim_management': { en: 'Management', id: 'Tatalaksana' },
  'dashboard.dim_clinical_safety': { en: 'Safety', id: 'Keamanan' },
  'dashboard.start_new_case': { en: 'Start new case', id: 'Mulai kasus baru' },
  'dashboard.level_progress': { en: 'Your progress', id: 'Progres kamu' },
  'dashboard.to_next_level': { en: '{n} XP to next level', id: '{n} poin ke tingkat berikutnya' },
  'dashboard.xp_in_level': { en: '/ 200 XP', id: '/ 200 poin' },
  // ── FASE 9 study cockpit (all numbers come from /api/v2/progress) ──
  'dashboard.next_focus': { en: 'Next focus', id: 'Fokus berikutnya' },
  'dashboard.find_case': { en: 'Find a case', id: 'Cari kasus' },
  'dashboard.based_on': { en: 'Based on {n} sessions', id: 'Berdasarkan {n} sesi' },
  'dashboard.developing': { en: 'Developing', id: 'Berkembang' },
  'dashboard.needs_session': { en: 'Needs one more session', id: 'Butuh satu sesi lagi' },
  'dashboard.onboarding_title': { en: 'Build your clinical profile', id: 'Bangun profil klinismu' },
  'dashboard.onboarding_body': { en: 'Complete your first cases to build your clinical profile. Your skills, coverage and readiness will appear here.', id: 'Selesaikan kasus pertamamu untuk membangun profil klinis. Kemampuan, cakupan, dan kesiapanmu akan muncul di sini.' },
  'dashboard.readiness': { en: 'Readiness', id: 'Kesiapan' },
  'dashboard.confidence_low': { en: 'Low confidence', id: 'Keyakinan rendah' },
  'dashboard.confidence_medium': { en: 'Medium confidence', id: 'Keyakinan sedang' },
  'dashboard.confidence_high': { en: 'High confidence', id: 'Keyakinan tinggi' },
  'dashboard.skill_detail': { en: 'Skill detail', id: 'Rincian kemampuan' },
  'dashboard.achievements': { en: 'Achievements', id: 'Pencapaian' },
  'dashboard.coverage': { en: 'Specialty coverage', id: 'Cakupan spesialisasi' },
  'dashboard.no_coverage': { en: 'No specialties practised yet.', id: 'Belum ada spesialisasi yang dilatih.' },
  'dashboard.continue_journey': { en: 'Continue journey', id: 'Lanjutkan perjalanan' },
  'dashboard.day_of': { en: 'Day {a} of {b}', id: 'Hari {a} dari {b}' },
  'dashboard.today': { en: 'Today', id: 'Hari ini' },
  'dashboard.yesterday': { en: 'Yesterday', id: 'Kemarin' },
  'dashboard.in_progress': { en: 'In progress', id: 'Sedang berjalan' },
  'dashboard.resume': { en: 'Continue', id: 'Lanjutkan' },
  'dashboard.view_all': { en: 'View all', id: 'Lihat semua' },

  // ── Catalogue / Cases ──
  'cases.title': { en: 'Case library', id: 'Pustaka kasus' },
  'cases.filter_all': { en: 'All', id: 'Semua' },
  'cases.search': { en: 'Search cases…', id: 'Cari kasus…' },
  'cases.no_results': { en: 'No cases match your filter.', id: 'Tidak ada kasus yang sesuai.' },
  'cases.start': { en: 'Start case', id: 'Mulai kasus' },
  'cases.difficulty_1': { en: 'Pre-clinical', id: 'Preklinik' },
  'cases.difficulty_2': { en: 'Clinical', id: 'Koas' },
  'cases.difficulty_3': { en: 'Advanced', id: 'PPDS' },

  // ── Session ──
  'session.ask_question': { en: 'Ask the patient a question…', id: 'Tanyakan pada pasien…' },
  'session.send': { en: 'Send', id: 'Kirim' },
  'session.assess': { en: 'Assess →', id: 'Nilai →' },
  'session.assess_tab_conversation': { en: 'Conversation', id: 'Percakapan' },
  'session.assess_tab_investigations': { en: 'Investigations', id: 'Pemeriksaan' },
  'session.assess_tab_diagnosis': { en: 'Diagnosis', id: 'Diagnosis' },
  'session.assess_tab_therapy': { en: 'Therapy', id: 'Terapi' },
  'session.select_investigations': { en: 'Select the investigations you would order (up to {max}). Choose deliberately — over-ordering is not rewarded.', id: 'Pilih pemeriksaan penunjang (maks. {max}). Pilih secara selektif.' },
  'session.select_therapy': { en: 'Select your management plan.', id: 'Pilih rencana tatalaksana.' },
  'session.working_diagnosis': { en: 'Working diagnosis', id: 'Diagnosis kerja' },
  'session.score_retry_hint': { en: 'The score request did not return in time. Try again.', id: 'Permintaan nilai tidak selesai tepat waktu. Coba lagi.' },
  'session.require_working_dx': { en: 'A working diagnosis is required before submitting the answer key.', id: 'Diagnosis kerja wajib diisi sebelum mengunci jawaban.' },
  'session.safety_gates': { en: '⚠️ Safety flags', id: '⚠️ Peringatan keselamatan' },
  'session.safety_missed_critical_red_flag': { en: 'Missed critical red flag', id: 'Red-flag kritis terlewat' },
  'session.safety_unsafe_management': { en: 'Unsafe management', id: 'Tatalaksana tidak aman' },
  'session.safety_failed_urgent_referral': { en: 'Missed urgent referral', id: 'Rujukan mendesak terlewat' },
  'session.differential_2': { en: 'Differential 2', id: 'Diagnosis banding 2' },
  'session.differential_3': { en: 'Differential 3', id: 'Diagnosis banding 3' },
  'session.clinical_reasoning': { en: 'Clinical reasoning', id: 'Penalaran klinis' },
  'session.patient_education': { en: 'Patient education & safety-netting', id: 'Edukasi pasien & safety-netting' },
  'session.your_assessment': { en: 'Your assessment', id: 'Penilaian Anda' },

  // ── Setup / Prep ──
  'setup.get_ready': { en: 'Get ready for your session', id: 'Siapkan sesi Anda' },
  'setup.choose_mode': { en: 'Choose a mode', id: 'Pilih mode' },
  'setup.choose_language': { en: 'Choose session language', id: 'Pilih bahasa sesi' },
  'setup.practice': { en: 'Practice', id: 'Latihan' },
  'setup.practice_title': { en: 'Anamnesis practice', id: 'Latihan anamnesis' },
  'setup.practice_desc': { en: 'Relaxed learning. A task guide and history hints help you along. The timer is optional.', id: 'Belajar santai. Panduan tugas dan petunjuk membantu Anda. Timer opsional.' },
  'setup.osce': { en: 'OSCE', id: 'OSCE' },
  'setup.osce_title': { en: 'OSCE exam', id: 'Ujian OSCE' },
  'setup.osce_desc': { en: 'Exam conditions — no hints. A countdown runs; when it ends you finish or continue for a penalty.', id: 'Kondisi ujian — tanpa petunjuk. Hitung mundur berjalan; setelah habis selesai atau lanjut dengan penalti.' },
  'setup.mic_title': { en: 'Microphone access', id: 'Akses mikrofon' },
  'setup.mic_desc': { en: 'Optional — talk to the patient by voice. You can always type instead.', id: 'Opsional — bicara dengan pasien via suara. Bisa juga mengetik.' },
  'setup.start_session': { en: 'Start session →', id: 'Mulai sesi →' },

  // ── Profile ──
  'profile.title': { en: 'Profile', id: 'Profil' },
  'profile.edit': { en: 'Edit profile', id: 'Edit profil' },
  'profile.save': { en: 'Save', id: 'Simpan' },
  'profile.name': { en: 'Full name', id: 'Nama lengkap' },
  'profile.email': { en: 'Email', id: 'Email' },
  'profile.school': { en: 'School / Institution', id: 'Sekolah / Institusi' },
  'profile.year': { en: 'Year / Stage', id: 'Tahun / Tahap' },
  'profile.badges': { en: 'Badges', id: 'Lencana' },
  'profile.settings': { en: 'Settings', id: 'Pengaturan' },
  'profile.language': { en: 'Preferred language', id: 'Bahasa preferensi' },
  'profile.region': { en: 'Region', id: 'Region' },
  'profile.billing': { en: 'Billing & plan', id: 'Tagihan & paket' },
  'profile.plan': { en: 'Current plan', id: 'Paket saat ini' },

  // ── Billing ──
  'billing.success': { en: 'Payment successful!', id: 'Pembayaran berhasil!' },
  'billing.failed': { en: 'Payment not completed', id: 'Pembayaran belum selesai' },

  // ── Result / Debrief ──
  'result.title': { en: 'Session complete!', id: 'Sesi selesai!' },
  'result.overall_score': { en: 'Overall score', id: 'Skor total' },
  'result.per_item': { en: 'Per-item breakdown', id: 'Rincian per-item' },
  'result.answer_key': { en: 'Answer key', id: 'Kunci jawaban' },
  'result.try_again': { en: 'Try another case', id: 'Coba kasus lain' },
  'result.back_to_library': { en: 'Back to library', id: 'Kembali ke pustaka' },

  // ── General / Common ──
  'common.log_in': { en: 'Log in', id: 'Masuk' },
  'common.sign_up': { en: 'Sign up', id: 'Daftar' },
  'common.log_out': { en: 'Log out', id: 'Keluar' },
  'common.loading': { en: 'Loading…', id: 'Memuat…' },
  'common.error': { en: 'Error', id: 'Error' },
  'common.back': { en: 'Back', id: 'Kembali' },
  'common.save': { en: 'Save', id: 'Simpan' },
  'common.cancel': { en: 'Cancel', id: 'Batal' },

  // ── Mentor (PRD_QORA_MENTOR) ──
  'mentor.title': { en: 'My Mentor', id: 'Mentor Saya' },
  'mentor.subtitle': { en: 'Tell Qora about your exam — it will build a structured learning journey, track your progress, and tell you when you are ready.', id: 'Ceritain ujian kamu ke Qora — dia susun rencana belajar terstruktur, ingetin progress, dan kasih tau kapan kamu siap.' },
  'mentor.tell_qora': { en: 'Tell Qora', id: 'Ceritain ke Qora' },
  'mentor.chat_placeholder': { en: 'Tell Qora: what exam, when, where you struggle…', id: 'Ceritain ke Qora: ujian apa, kapan, masih kurang di mana…' },
  'mentor.send': { en: 'Send', id: 'Kirim' },
  'mentor.thinking': { en: 'Mentor is building your journey…', id: 'Mentor sedang menyusun rencana belajarmu…' },
  'mentor.cancel': { en: 'Cancel', id: 'Batal' },
  'mentor.your_journey': { en: 'Your Learning Journey', id: 'Rencana Belajar Kamu' },
  'mentor.days': { en: '{d} days · ~{m} min/day', id: '{d} hari · ~{m} menit/hari' },
  'mentor.target_readiness': { en: 'Target', id: 'Target' },
  'mentor.readiness_start': { en: 'Estimated readiness now', id: 'Estimasi kesiapan sekarang' },
  'mentor.locked': { en: 'Complete Day {d} to unlock', id: 'Selesaikan Hari {d} untuk membuka' },
  'mentor.available_now': { en: 'Available now', id: 'Tersedia sekarang' },
  'mentor.reasoning': { en: 'Why this plan', id: 'Alasan rencana ini' },
  'mentor.accept': { en: 'Accept Journey', id: 'Mulai Journey' },
  'mentor.customize': { en: 'Customize', id: 'Sesuaikan' },
  'mentor.customize_feedback': { en: 'Feedback: e.g. "Day 3 → different case"', id: 'Feedback: mis. "hari 3 ganti kasus lain"' },
  'mentor.changes': { en: 'Changes', id: 'Perubahan' },
  'mentor.progress': { en: 'Day {d} of {n} ({p}%)', id: 'Hari {d} dari {n} ({p}%)' },
  'mentor.readiness': { en: 'Readiness', id: 'Kesiapan' },
  'mentor.today': { en: "Today's case", id: 'Kasus hari ini' },
  'mentor.start_case': { en: 'Start Case', id: 'Mulai Kasus' },
  'mentor.abandon': { en: 'Abandon journey', id: 'Hentikan journey' },
  'mentor.view_report': { en: 'Readiness Report', id: 'Laporan Kesiapan' },
  'mentor.back_to_journey': { en: 'Back to journey', id: 'Kembali ke journey' },

  // ── Mentor: autopsy (PRD §4.2) ──
  'mentor.autopsy_title': { en: 'Clinical Reasoning Autopsy', id: 'Autopsi Penalaran Klinis' },
  'mentor.autopsy_tab_pathway': { en: 'Your Pathway', id: 'Jalur Kamu' },
  'mentor.autopsy_tab_expert': { en: 'Expert', id: 'Ahli' },
  'mentor.autopsy_tab_errors': { en: 'Errors', id: 'Kesalahan' },
  'mentor.autopsy_your_pathway': { en: 'Your reasoning pathway', id: 'Jalur penalaran kamu' },
  'mentor.autopsy_expert_pathway': { en: 'Expert pathway (gold standard)', id: 'Jalur ahli (standar emas)' },
  'mentor.autopsy_no_errors': { en: 'No reasoning errors detected — well structured!', id: 'Tidak ada kesalahan penalaran — struktur bagus!' },
  'mentor.autopsy_pearl': { en: 'Clinical Pearl', id: 'Mutiara Klinis' },
  'mentor.autopsy_readiness_impact': { en: 'Readiness impact', id: 'Dampak kesiapan' },

  // ── Mentor: continuity (PRD §4.3) ──
  'mentor.returning_patient': { en: 'Returning Patient', id: 'Pasien Kembali' },
  'mentor.story_so_far': { en: 'Story so far', id: 'Cerita sejauh ini' },
  'mentor.new_complaint': { en: 'New complaint', id: 'Keluhan baru' },
  'mentor.start_visit': { en: 'Start Visit {n}', id: 'Mulai Kunjungan {n}' },

  // ── Mentor: readiness (PRD §4.4) ──
  'mentor.readiness_report': { en: 'Readiness Report', id: 'Laporan Kesiapan' },
  'mentor.confidence': { en: 'Confidence', id: 'Tingkat keyakinan' },
  'mentor.sessions': { en: 'sessions', id: 'sesi' },
  'mentor.dimension_breakdown': { en: 'Dimension breakdown', id: 'Rincian dimensi' },
  'mentor.weakest_area': { en: 'Critical: Weakest area', id: 'Kritis: Area terlemah' },
  'mentor.weakest_text': { en: '{d} is your weakest dimension ({p}%). Focus here before your exam.', id: '{d} adalah dimensi terlemah kamu ({p}%). Fokus di sini sebelum ujian.' },
  'mentor.recommended_actions': { en: 'Recommended actions', id: 'Aksi yang disarankan' },
  // ── FASE 10 guided journey (mission / insight / timeline / verdict) ──
  'mentor.mission': { en: "Today's Mission", id: 'Misi Hari Ini' },
  'mentor.mission_meta': { en: '{n} encounter · ~{m} min', id: '{n} encounter · ~{m} mnt' },
  'mentor.why_this_case': { en: 'Why this case', id: 'Kenapa kasus ini' },
  'mentor.coach_insight': { en: 'Coach Insight', id: 'Catatan Coach' },
  'mentor.timeline': { en: 'Journey Timeline', id: 'Linimasa Perjalanan' },
  'mentor.goal_line': { en: '{goal} · {d} days', id: '{goal} · {d} hari' },
  'mentor.journey_report': { en: 'Journey Report', id: 'Laporan Perjalanan' },
  'mentor.next_recommendation': { en: 'Next recommendation', id: 'Rekomendasi berikutnya' },
  'mentor.verdict_ready': { en: 'Exam ready', id: 'Siap ujian' },
  'mentor.verdict_completed': { en: 'Plan complete', id: 'Rencana selesai' },
  'mentor.recap': { en: 'Recap', id: 'Rekap' },
  'mentor.stop_journey': { en: 'Stop journey', id: 'Hentikan perjalanan' },
};

// Simple translation function. Usage: window.__t('dashboard.title')
// Returns the string in the current locale, falls back to English, then returns the key.
window.__t = function (key, vars) {
  var entry = window.QORA_TRANSLATIONS[key];
  if (!entry) return key;
  var text = entry[window.QORA_LOCALE] || entry['en'] || key;
  // Simple variable substitution: replace {var} with provided values
  if (vars) {
    for (var k in vars) {
      text = text.replace(new RegExp('\\{' + k + '\\}', 'g'), vars[k]);
    }
  }
  return text;
};

// Set locale based on detected region
window.__setLocale = function (region) {
  window.QORA_LOCALE = (region === 'indo') ? 'id' : 'en';
};

// If region was already detected, apply it
try {
  var cached = localStorage.getItem('qora_region');
  if (cached) window.__setLocale(cached);
} catch (e) {}
