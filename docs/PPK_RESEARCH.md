# Riset PPK/PNPK Kemenkes & Epidemiologi Kasus Indonesia — Grounding Kasus Qora

> **Tanggal riset:** 9 Agustus 2026 · **Tujuan:** grounding authoring kasus ke dokumen resmi Kemenkes + fokus ke kasus yang sering diujikan/ditemui di Indonesia (Ayyasy, koas FKUI/RSCM: "yang diujikan biasanya yang sering ada kasusnya, kayak TBC").
> **Catatan terminologi:** PPK (Panduan Praktik Klinis) sudah berevolusi menjadi **PNPK (Pedoman Nasional Pelayanan Kedokteran)** yang diterbitkan per Keputusan Menteri Kesehatan (KMK) dan diregistry di JDIH Kemenkes.

---

## 1. Status Akses Sumber (diverifikasi langsung, 9 Agu 2026)

| Sumber | Status | Catatan |
|---|---|---|
| `yankes.kemkes.go.id` | ❌ MATI (NXDOMAIN) | Situs lama sudah tidak ada; URL lama tidak bisa dipakai |
| `registry.ppk.kemkes.go.id` | ❌ Tidak resolve | — |
| `kemkes.go.id` | ✅ Hidup (200) | Portal utama |
| `jdih.kemkes.go.id` | ✅ Hidup (200) | **Sumber utama PNPK** — pencarian Livewire berfungsi penuh |
| `peraturan.bpk.go.id` | ⚠️ 403 ke curl | Akses via browser mungkin jalan |
| Google/Bing | ⚠️ CAPTCHA/lokasi | Jangan dipakai sebagai primary source |

**Tool pencarian JDIH yang terbukti jalan:** `/tmp/jdih_search.py` (scraper Livewire). Pakai:
```bash
python3 /tmp/jdih_search.py "pedoman nasional pelayanan kedokteran" "" 2   # query, tahun, jumlah halaman
# Output TSV: judul \t tipe \t status \t tanggal \t URL \t deskripsi
```
Query `"pedoman nasional pelayanan kedokteran"` melaporkan **60 dokumen PNPK** terindeks (per 9 Agu 2026). Halaman PNPK yang lama (unduhan) tidak ada lagi — semua via JDIH dengan pola URL `https://jdih.kemkes.go.id/documents/<slug>`.

---

## 2. Daftar PNPK per Spesialisasi (terverifikasi di JDIH, 9 Agu 2026)

| Kondisi | Nomor KMK | Tanggal | URL JDIH | Relevansi Qora |
|---|---|---|---|---|
| **Stroke** (neuro/emergency) | HK.01.07/MENKES/304/2026 | 17 Apr 2026 | https://jdih.kemkes.go.id/documents/keputusan-menteri-kesehatan-nomor-hk0107menkes3042026 | Link ke `neuro_tia` + landasan kasus baru *stroke akut* |
| **Skizofrenia** (psychiatry) | HK.01.07/Menkes/970/2025 | 10 Okt 2025 | https://jdih.kemkes.go.id/documents/keputusan-menteri-kesehatan-nomor-hk0107menkes9702025 | Link ke kasus psych (tidak ada kasus skizofrenia — kandidat baru) |
| **DM Tipe 2 Dewasa** (internal) | HK.01.07/Menkes/603/2020 | 31 Agu 2020 | https://jdih.kemkes.go.id/documents/keputusan-menteri-kesehatan-nomor-hk0107m6032020 | Link ke `im_new_t2dm` |
| **DM Anak** (paeds) | HK.01.07/Menkes/2009/2024 | 31 Des 2024 | https://jdih.kemkes.go.id/documents/keputusan-menteri-kesehatan-nomor-hk0107menkes20092024 | Kandidat kasus baru |
| **Hipertensi Dewasa** (internal) | HK.01.07/Menkes/4634/2021 | 3 Mei 2021 | https://jdih.kemkes.go.id/documents/keputusan-menteri-kesehatan-nomor-hk0107menkes46342021 | Link `im_ckd` + kasus baru *hipertensi emergensi* |
| **Hipertensi Anak** (paeds) | HK.01.07/Menkes/4613/2021 | 16 Apr 2021 | https://jdih.kemkes.go.id/documents/keputusan-menteri-kesehatan-nomor-hk0107menkes46132021 | Rujukan saja |
| **Osteoporosis** (internal) | HK.01.07/Menkes/2171/2023 | 8 Des 2023 | https://jdih.kemkes.go.id/documents/keputusan-menteri-kesehatan-nomor-hk0107menkes21712023 | Kandidat kasus baru |
| **Perdarahan Saluran Cerna** (internal/emergency) | HK.01.07/Menkes/2162/2023 | 4 Des 2023 | https://jdih.kemkes.go.id/documents/keputusan-menteri-kesehatan-nomor-hk0107menkes21622023 | Kandidat kasus baru (UGIB) |
| **Glaukoma** (ophthalmology) | HK.01.07/Menkes/1488/2023 | 20 Jul 2023 | https://jdih.kemkes.go.id/documents/keputusan-menteri-kesehatan-nomor-hk0107menkes14882023 | Link ke `oph_acute_angle_closure` |
| **Kanker Paru** (internal) | HK.01.07/Menkes/1438/2023 | 23 Jun 2023 | https://jdih.kemkes.go.id/documents/keputusan-menteri-kesehatan-nomor-hk0107menkes14382023 | Rujukan (level PPDS) |
| **Angina Pektoris Stabil** (internal) | HK.01.07/Menkes/1419/2023 | 8 Jun 2023 | https://jdih.kemkes.go.id/documents/keputusan-menteri-kesehatan-nomor-hk0107menkes14192023 | Link/rujukan ACS |
| **Gagal Jantung Anak** (paeds) | HK.01.07/Menkes/85/2023 | 3 Feb 2023 | https://jdih.kemkes.go.id/documents/keputusan-menteri-kesehatan-nomor-hk0107menkes852023 | Kandidat kasus baru |
| **Tuli Sensorineural Kongenital** (ENT) | HK.01.07/Menkes/1989/2022 | 26 Des 2022 | https://jdih.kemkes.go.id/documents/keputusan-menteri-kesehatan-nomor-hk0107menkes19892022 | Rujukan (skrining bayi) |
| **Stunting** (paeds) | HK.01.07/Menkes/1928/2022 | 25 Nov 2022 | https://jdih.kemkes.go.id/documents/keputusan-menteri-kesehatan-nomor-hk0107menkes19282022 | Kandidat kasus baru (sangat relevan Indonesia) |
| **Cedera Otak Traumatik** (emergency/surgery) | HK.01.07/Menkes/1600/2022 | 21 Okt 2022 | https://jdih.kemkes.go.id/documents/keputusan-menteri-kesehatan-nomor-hk0107menkes16002022 | Kandidat kasus baru |
| **Batu Saluran Kemih** (surgery) | HK.01.07/Menkes/1560/2022 | 7 Okt 2022 | https://jdih.kemkes.go.id/documents/keputusan-menteri-kesehatan-nomor-hk0107menkes15602022 | Link ke `surg_renal_colic` |
| **Komplikasi Kehamilan** (obgyn) | HK.01.07/Menkes/91/2017 | 17 Feb 2017 | https://jdih.kemkes.go.id/documents/keputusan-menteri-kesehatan-nomor-hk0107menkes912017 | Link ke `og_pre_eclampsia` / `og_early_pregnancy_bleeding` |
| **Penyakit Pulpa & Periradikuler** (dental) | HK.01.07/Menkes/1492/2023 | 20 Jul 2023 | https://jdih.kemkes.go.id/documents/keputusan-menteri-kesehatan-nomor-hk0107menkes14922023 | Di luar 10 spesialisasi Qora |

**Kondisi penting yang BELUM ada PNPK-nya di JDIH (query 9 Agu 2026):** DBD (hanya SK KLB 406/2004), demam tifoid (Pedoman Pengendalian 364/2006), TB paru (dokumen PNPK tidak ditemukan — yang ada SK program/konsorsium; panduan utama = program nasional TB, rujukan WHO), asma, pneumonia, diare, leptospirosis, meningitis, kejang demam. → **Jangan mengarang isi PNPK untuk kondisi ini**; pakai referensi standar (WHO, GINA, guideline internacional) + panduan program Kemenkes, dan catat di `source_refs`.

---

## 3. 15 Kasus Prioritas IGD/Indonesia — Pola Presentasi untuk Authoring

> Format: pola presentasi khas sebagai panduan authoring (bukan kutipan PPK). Detail per kasus WAJIB diverifikasi ke dokumen PNPK/link saat authoring.

| # | Kondisi | Keluhan utama | Poin anamnesis penting | Red flags | Tanda vital khas | Tanda fisik khas | Level | Spesialisasi | Status |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **DBD** | Demam mendadak 2–7 hari, nyeri kepala/otot/persendian, mual | Onset demam, nyeri retro-orbital, rash, perdarahan (gusi/mimisan), BAB hitam, nafsu makan, muntah, nyeri perut, riwayat DBD/tetangga | Nyeri perut hebat, muntah terus, gelisah/letargi, perdarahan, oliguria, syok (fase kritis hari 3–7) | Demam 38–40°C; fase syok: HR↑, TD↓/nadi sempit | Tourniquet test (+), petekie, hepatomegali, muka flushing, asites/rale (kebocoran plasma) | Koas | emergency / paeds | 🆕 **BELUM ADA** (cek `paed_febrile_child` — mungkin kasus generik) |
| 2 | **Demam tifoid** | Demam naik bertahap >7 hari, nyeri perut, nyeri kepala | Pola demam, konstipasi/diare, muntah, anoreksia, batuk, riwayat kontak, higiene/makanan jajan | Perdarahan usus (melena), perforasi (nyeri perut hebat mendadak), penurunan kesadaran | Demam; **bradikardia relatif**, suhu tinggi vs nadi | Lidah kotor (coated tongue), hepatosplenomegali, rose spots (jarang), distensi abdomen | Koas | internal / paeds | 🆕 **BELUM ADA** |
| 3 | **TB paru** | Batuk >2–3 minggu, dahak, kadang darah | Durasi batuk, hemoptisis, demam sore, keringat malam, BB turun, kontak TB, riwayat pengobatan (lengkap/DO?), HIV, DM | Hemoptisis masif, sesak berat, penurunan kesadaran | Sering normal; demam subfebris | Konjungtiva anemis, penurunan BB, ronki/vesikuler melemah, limfadenopati | Koas | internal | ✅ ADA (`im_tuberculosis`) — **verifikasi framing Indonesia + PNPK/program TB** |
| 4 | **ISPA / pneumonia komunitas** | Batuk + demam + sesak | Onset, dahak, sesak progresif, nyeri dada pleuritik, nafsu makan, imunisasi, riwayat asma | **Tarikan dinding dada** (chest indrawing), grunting, sianosis, SpO2 <92%, napas cepat (umur-dependent), tidak mau minum | RR↑ (khas), demam, SpO2↓ | Ronki basah, bronchial breath sound, tarikan subkostal/interkostal | Pre-klinik / Koas | paeds / internal | ✅ ADA (`im_community_acquired_pneumonia`) — cek versi paeds |
| 5 | **Diare akut + dehidrasi** | BAB cair >3x/hari, muntah | Frekuensi/konsistensi/darah-lendir, muntah, demam, **asupan & keluaran urine**, riwayat jajan/air, status imunisasi | Letargi, tidak bisa minum, urine sangat sedikit, kejang, darah di feses | HR↑, TD↓/nadi cepat, demam | **Sunken eyes, turgor kulit ↓, mukosa kering, capillary refill >2s**, ubun-ubun cekung (bayi) | Pre-klinik / Koas | paeds | 🆕 **BELUM ADA** |
| 6 | **Kejang demam** | Kejang saat demam (usia 6 bln–5 th) | Usia, durasi kejang, generalisata/fokal, suhu saat kejang, riwayat kejang sebelumnya, riwayat keluarga, pasca-kejang (postictal), imunisasi, perkembangan | Kejang >15 menit / fokal / berulang (<24 jam) = **kejang demam kompleks**; kekakuan kuduk, fontanel menonjol, kesadaran tidak pulih (→ meningitis/ensefalitis) | Demam (sering 38.5°C+) | Postictal; kaku kuduk jika meningitis, rash (petekie → meningokok/DBD) | Pre-klinik / Koas | paeds | 🆕 **BELUM ADA** (neuro_first_seizure = dewasa?) |
| 7 | **Stroke iskemik akut** | Kelemahan mendadak satu sisi, bicara pelo, wajah mencong | **Waktu onset PERSIS** (window trombolisis 4,5 jam!), kelemahan/tubuh sisi, bicara, pusing/vertigo, trauma, obat antiplatelet/antikoagulan, riwayat stroke/TIA, DM/HTN | Penurunan kesadaran, nyeri kepala hebat mendadak, muntah, kejang | TD↑ (sering), AF (aritmia), SpO2 | Facial droop, hemiparesis, dysarthria, GCS↓; NIHSS-ish | PPDS | neuro / emergency | 🆕 **BELUM ADA** (hanya `neuro_tia`) — PNPK Stroke 304/2026 |
| 8 | **Hipertensi emergensi** | Sakit kepala hebat, penglihatan kabur, nyeri dada, sesak (TD sangat tinggi) | TD baseline, kepatuhan obat, gejala end-organ (neurologis/kardiak/renal), kehamilan, obat simpatomimetik | TD ≥180/120 + gejala end-organ; penurunan kesadaran, kejang (→ ensefalopati), nyeri dada, sesak (→ edema paru) | TD ≥180/120, HR bervariasi | Papiledema (funduskopi), ronki basah, defisit neurologis fokal | Koas / PPDS | internal / emergency | 🆕 **BELUM ADA** — PNPK Hipertensi Dewasa 4634/2021 |
| 9 | **Asma eksaserbasi** | Sesak + mengi + batuk, memburuk | Onset, pemicu (infeksi/udara/olahraga), pemakaian inhaler/obat, riwayat eksaserbasi/ICU, kepatuhan, merokok/lingkungan | **Tidak bisa kalimat utuh**, letargi/silent chest, sianosis, SpO2 <90%, RR >30, nadi paradoksus | RR↑, HR↑, SpO2↓ | Wheeze ekspirasi, retraksi, silent chest (bahaya), penggunaan otot bantu napas | Koas | emergency / paeds | ✅ ADA (`em_status_asthmaticus`, `paed_asthma`) |
| 10 | **Appendisitis akut** | Nyeri perut migrasi dari ulu hati ke kanan bawah | Onset, migrasi nyeri, anoreksia/mual, demam, BAB terakhir, riwayat serupa | Nyeri perut menyebar (→ perforasi/peritonitis), demam tinggi, distensi, syok | Demam ringan-sedang; takikardia | Nyeri tekan McBurney, Rovsing/Obturator/Psoas (+), defans muskular, rebound tenderness | Koas | surgery | ✅ ADA (`im_gi_appendicitis`) |
| 11 | **Leptospirosis** | Demam + nyeri otot (betis) + sakit kepala | Demam mendadak, **nyeri betis**, riwayat banjir/genangan/roda (petugas kebersihan), ikterus, perdarahan, oliguria | Ikterus + perdarahan + gagal ginjal (sindrom Weil), hemoptisis, syok, aritmia | Demam 38–40°C; fase berat: TD↓, HR↑ | **Konjungtiva suffusion** (khas), nyeri tekan betis, hepatomegali, ikterus, petekie | PPDS | emergency / internal | 🆕 **BELUM ADA** |
| 12 | **KAD (Ketoasidosis diabetik)** | Lemas, mual/muntah, napas cepat, nyeri perut, banyak kencing/haus | Onset polidipsi/poliuri, BB turun, riwayat DM/tidak, kepatuhan insulin, infeksi pencetus, muntah, asupan | Gangguan kesadaran, syok, muntah persisten, Kussmaul | **Napas Kussmaul**, RR↑, HR↑, TD↓, dehidrasi | Bau aseton (fruity breath), dehidrasi berat, pernapasan dalam, kesadaran menurun | PPDS | emergency / paeds | ✅ ADA (`em_diabetic_ketoacidosis`) |
| 13 | **Meningitis bakterialis** | Demam tinggi + sakit kepala hebat + kaku kuduk + muntah proyektil | Onset, demam, nyeri kepala, fotofobia, muntah, kejang, kesadaran, ruam, riwayat otitis/sinus, imunisasi | **Kaku kuduk**, penurunan kesadaran, petekie/purpura (meningokok), kejang, fokal deficit, syok | Demam tinggi; fase berat: HR↑ TD↓ | Kaku kuduk, Kernig/Brudzinski (+), fotofobia, petekie; bayi: fontanel menonjol, letargi | PPDS | emergency | 🆕 **BELUM ADA** |
| 14 | **Cedera kepala (TBI)** | Jatuh/kecelakaan, benjol/nyeri kepala, muntah, lupa kejadian | **Mekanisme trauma + waktu**, kehilangan kesadaran (durasi), amnesia, muntah, kejang, obat pengencer darah, alkohol, riwayat neuro | GCS <15, pupil tidak sama, defisit fokal, muntah berulang, kejang, kebocoran CSS (rhinor/otorrhea), racoon eyes/Battle sign | GCS↓, HR↓ TD↑ (Cushing), RR ireguler | Pupil anisokor, lateralisasi, Battle sign, racoon eyes, defisit motorik | Koas / PPDS | emergency / surgery | 🆕 **BELUM ADA** — PNPK TBI 1600/2022 |
| 15 | **Kehamilan ektopik terganggu** | Nyeri perut bawah + perdarahan pervaginam + haid telat | HPHT/amenore, pola nyeri (tajam, satu sisi), perdarahan, mual, riwayat ektopik/PID/IUD/operasi tuba, kontrasepsi | **Syok (TD↓ HR↑ pucat)**, nyeri bahu (iritasi diafragma), pusing saat berdiri, nyeri perut hebat | TD↓, HR↑ (syok hemoragik) | Nyeri tekan adneksa, nyeri goyang porsio (cervical motion tenderness), tanda syok, distensi | PPDS | obgyn | ✅ ADA (`og_early_pregnancy_bleeding`) — verifikasi cakupan |

---

## 4. Rekomendasi Backlog Kasus Baru (prioritas, grounding PNPK)

**Tier 1 — wajib (kasus IGD/ujian Indonesia yang belum ada):** ✅ GENERATED 10 Agu 2026
1. `em_dengue_001` — DBD fase demam + warning signs (level koas) — guideline WHO dengue; cek overlap `paed_febrile_child`
2. `im_typhoid_001` — demam tifoid (koas) — Pedoman Pengendalian 364/2006
3. `paed_acute_gastroenteritis_001` — diare akut + dehidrasi (pre-klinik/koas)
4. `paed_febrile_seizure_001` — kejang demam (pre-klinik/koas)
5. `neuro_acute_stroke_001` — stroke iskemik akut window trombolisis (PPDS) — **PNPK Stroke 304/2026**
6. `em_hypertensive_emergency_001` — hipertensi emergensi (koas/PPDS) — **PNPK Hipertensi Dewasa 4634/2021**

**Tier 2 — pengayaan:** ✅ GENERATED 10 Agu 2026
7. `em_leptospirosis_001` (PPDS)
8. `em_bacterial_meningitis_001` (PPDS)
9. `em_traumatic_brain_injury_001` (koas/PPDS) — **PNPK TBI 1600/2022**
10. `paed_stunting_001` (koas) — **PNPK Stunting 1928/2022** (kasus anamnesis tumbuh kembang — nilai jual lokal)

**Tier 3 — link PNPK ke kasus existing (source_refs, tanpa generate ulang):**
- `im_tuberculosis` → program nasional TB + WHO (catat: PNPK TB tidak ditemukan di JDIH)
- `im_new_t2dm` → PNPK DM T2 Dewasa 603/2020
- `surg_renal_colic` → PNPK Batu Saluran Kemih 1560/2022
- `neuro_tia` → PNPK Stroke 304/2026
- `im_ckd` → PNPK Hipertensi Dewasa 4634/2021 (komorbid)
- `og_pre_eclampsia` / `og_early_pregnancy_bleeding` → PNPK Komplikasi Kehamilan 91/2017
- `oph_acute_angle_closure` → PNPK Glaukoma 1488/2023
- `em_acs` → rujukan PNPK Angina Stabil 1419/2023 + guideline ACS

---

## 5. Cara Pakai Saat Authoring

1. Sebelum generate kasus: cek tabel PNPK di atas; kalau kondisi punya PNPK → **buka dokumennya via URL JDIH** dan jadikan acuan checklist/red flags/management. Jangan mengarang isi PNPK dari judul.
2. Isi `source_refs` di frontmatter dengan `"PNPK Kemenkes: <nama> (KMK No. ..., jdih.kemkes.go.id/documents/<slug>)"`.
3. Kalau tidak ada PNPK (DBD, tifoid, TB, asma, pneumonia, diare, dll) → `source_refs` pakai guideline internasional/WHO + panduan program Kemenkes, dan **tulis statusnya** di review_notes.
4. Nama pasien: Indonesia, sesuai umur (tradisional untuk lansia, modern untuk muda) — sudah jadi aturan author pipeline.
5. Tiap kasus baru wajib punya `## Vital signs` + `## Physical findings` konsisten dengan kondisi (aturan pipeline sudah aktif).
