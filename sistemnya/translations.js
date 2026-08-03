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
