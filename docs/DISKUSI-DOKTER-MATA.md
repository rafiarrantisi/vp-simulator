# OphthaSim — Bahan Diskusi dengan Dokter Mata

> **Tujuan dokumen ini.** Lembar ini dibuat sebagai bahan diskusi terstruktur
> antara tim pengembang dan dokter mata (validator klinis). Isinya menjelaskan
> *apa yang sudah dibangun*, *bagaimana cara kerjanya yang sebenarnya*, dan
> *apa yang masih perlu diputuskan* — supaya dokter bisa menilai: apakah
> fiturnya sudah tepat, apakah cara penilaiannya sudah benar secara
> pedagogis/klinis, dan apa yang perlu diperbaiki.
>
> **Cara pakai.** Tiap bagian diakhiri kotak **❓ Untuk didiskusikan** dengan
> ruang **Catatan dokter: ______**. Dokter cukup mengisi/menandai langsung.
> Tidak perlu paham teknis — istilah teknis dijelaskan di **Lampiran A
> (Glosarium)** di akhir.
>
> **Status kejujuran.** Semua konten klinis dalam sistem saat ini adalah
> **draf yang disusun tim pengembang**, **belum tervalidasi dokter**. Dokumen
> ini justru langkah validasi itu. Penanda status dipakai konsisten:
>
> | Tanda | Arti |
> |---|---|
> | ✅ | Sudah dibangun & live (bisa dicoba sekarang) |
> | 🟡 | Usulan / rencana — belum dibangun |
> | ⚠️ | Temuan / celah yang perlu perhatian |
> | ❓ | Pertanyaan untuk dokter |
>
> Versi bahan diskusi: 1.0 · Tanggal: 2026-06-12 · Mengacu sistem v0.16.0
> · Alamat uji coba: https://ophtasim.duckdns.org

---

## Daftar Isi

1. [Gambaran besar: apa itu OphthaSim](#1-gambaran-besar-apa-itu-ophthasim)
2. [Anatomi satu kasus (format & isi)](#2-anatomi-satu-kasus-format--isi)
3. [Matriks Penilaian Anamnesis — INTI DISKUSI](#3-matriks-penilaian-anamnesis--inti-diskusi)
4. [Case Builder — fitur pembuat kasus untuk dokter](#4-case-builder--fitur-pembuat-kasus-untuk-dokter)
5. [Validasi konten klinis 9 kasus aktif](#5-validasi-konten-klinis-9-kasus-aktif)
6. [Topik lain untuk didiskusikan](#6-topik-lain-untuk-didiskusikan)
7. [Ringkasan keputusan terbuka (lembar centang)](#7-ringkasan-keputusan-terbuka-lembar-centang)
- [Lampiran A — Glosarium istilah teknis](#lampiran-a--glosarium-istilah-teknis)
- [Lampiran B — Contoh laporan penilaian](#lampiran-b--contoh-laporan-penilaian-yang-dilihat-mahasiswa)

---

## 1. Gambaran besar: apa itu OphthaSim

✅ **OphthaSim adalah simulator pasien virtual untuk latihan anamnesis
oftalmologi.** Mahasiswa kedokteran "mewawancarai" seorang pasien yang
diperankan oleh AI (kecerdasan buatan), seperti chat. Tujuannya melatih
keterampilan menggali riwayat penyakit (history taking) sebelum bertemu
pasien sungguhan.

**Alur satu sesi latihan (4 tahap):**

```
┌─────────────┐   ┌──────────────┐   ┌──────────────────┐   ┌──────────────┐
│ 1. ANAMNESIS│ → │ 2. DIAGNOSIS │ → │ 3. RENCANA       │ → │ 4. DEBRIEF   │
│ (wawancara  │   │   BANDING    │   │   TATALAKSANA    │   │ (penilaian + │
│  pasien AI) │   │  (DDx, 1-3)  │   │ (penunjang/      │   │  umpan balik)│
│             │   │              │   │  terapi/edukasi) │   │              │
└─────────────┘   └──────────────┘   └──────────────────┘   └──────────────┘
```

1. **Anamnesis** — Mahasiswa mengetik pertanyaan; pasien AI menjawab sesuai
   persona (orang awam, tidak tahu istilah medis). Bisa banyak giliran
   tanya-jawab.
2. **Diagnosis Banding (DDx)** — Mahasiswa menuliskan 1–3 dugaan diagnosis +
   alasan klinisnya.
3. **Rencana Tatalaksana** — Mahasiswa menuliskan usulan pemeriksaan
   penunjang, terapi, dan edukasi/rujukan.
4. **Debrief (Penilaian)** — AI menilai keseluruhan sesi dan memberi: skor,
   hal yang sudah baik, hal yang terlewat, dan ringkasan naratif saran
   perbaikan.

**Hal penting yang membedakan dari chatbot biasa:** ✅ pasien AI **tidak
membocorkan semua gejala sekaligus**. Ia hanya menjawab yang ditanya, lalu
berhenti — meniru pasien sungguhan. Mahasiswa harus aktif menggali. (Ini
disebut *answer restraint*, dibahas di Bagian 2.)

**Tingkat pengguna saat ini:** ✅ ada 2 kelompok kasus —
- **Preklinik / Latihan** (9 kasus aktif, berbasis PPK Kemenkes) — yang
  sekarang bisa dimainkan.
- **Koas** (22 kasus lama) — sementara **dikunci** (tampil tapi belum bisa
  dimainkan), menunggu penyelarasan.

> ### ❓ Untuk didiskusikan (Bagian 1)
> 1. Apakah **alur 4 tahap** ini sesuai dengan cara Anda mengajar anamnesis?
>    Adakah tahap yang kurang (mis. *informed consent*, cuci tangan,
>    membangun rapport di awal)?
> 2. Apakah pemisahan **Preklinik vs Koas** masuk akal? Apa pembeda
>    ekspektasi keterampilan di dua level itu menurut Anda?
> 3. Untuk anamnesis oftalmologi, apakah ada **kekhasan** yang wajib ada
>    dibanding anamnesis umum (mis. selalu tanya riwayat kacamata/lensa
>    kontak, trauma, riwayat operasi mata, silau/halo, dll)?
>
> **Catatan dokter:** ______________________________________________

---

## 2. Anatomi satu kasus (format & isi)

Setiap kasus adalah satu berkas terstruktur dengan **dua bagian terpisah**
yang punya peran berbeda:

### 2.1 BAGIAN A — Data Medis (untuk sistem & penilaian)

Fakta medis objektif. **Tidak pernah ditampilkan ke mahasiswa.** Dipakai
sistem sebagai rujukan kebenaran & dasar penilaian.

Untuk **9 kasus PPK baru** (yang aktif), Bagian A berisi 6 sub-bagian:

| # | Sub-bagian | Isi |
|---|---|---|
| 1 | Diagnosis Kerja | Diagnosis + definisi + tingkat kemampuan SKDI |
| 2 | Patofisiologi & Etiologi | Mekanisme & penyebab |
| 3 | Faktor Risiko | Daftar faktor risiko |
| 4 | Temuan Klinis Objektif | Hasil **pemeriksaan fisik** (visus, slit-lamp, dll) |
| 5 | Komplikasi | Komplikasi bila tak ditangani |
| 6 | Tatalaksana | Edukasi, medikamentosa, kriteria rujukan |

⚠️ **Perhatikan:** Bagian A kasus baru **tidak punya** sub-bagian khusus
"daftar pertanyaan anamnesis yang seharusnya ditanyakan" maupun "daftar red
flag yang harus disingkirkan". (22 kasus lama **punya** — lihat 2.3.) Ini
sangat relevan untuk penilaian — dibahas tuntas di **Bagian 3**.

### 2.2 BAGIAN B — Persona Pasien (untuk AI berperan)

Skenario karakter pasien. Inilah yang membuat AI "menjadi" pasien. Berisi 10
sub-bagian:

| # | Sub-bagian | Contoh isi (kasus dry-eye) |
|---|---|---|
| 1 | Identitas & Profil | "Mbak Sinta, 28th, UI/UX designer, kerja depan komputer 10–12 jam" |
| 2 | Aturan Komunikasi | "Anda orang awam, tidak tahu istilah 'dry eye'/'Schirmer'…" |
| 3 | Keluhan Utama | "Mata sepet, perih, kayak berpasir, sudah 2 bulan" |
| 4 | Riwayat Penyakit Sekarang (SOCRATES) | Lokasi, onset, sifat, penyerta, waktu, pemberat/peringan, derajat |
| 5 | Tinjauan Sistem (ROS) | Mulut kering? Nyeri sendi? (untuk skrining Sjögren) |
| 6 | Riwayat Penyakit Dahulu | "Minus 2 sejak SMA, tak pernah operasi mata" |
| 7 | Riwayat Pengobatan | "Sering pakai Insto/Rohto, seger sebentar lalu perih lagi" |
| 8 | Riwayat Keluarga | "Mama pakai kacamata baca" |
| 9 | Riwayat Sosial & Lingkungan | "Kantor AC kencang, lembur, tidur 5–6 jam" |
| 10 | FIFE (Perspektif Pasien) | Feeling/Idea/Function/Expectation |

### 2.3 Konsep "Answer Restraint" (pasien menahan jawaban)

✅ Ini fitur inti yang (menurut catatan proyek) **3 dokter penguji** anggap
krusial: sistem lama gagal karena pasien membocorkan semua gejala. Sekarang
AI diberi aturan tegas:

- Jawab **hanya** dimensi yang ditanya, lalu **berhenti**.
- Saat hanya **disapa** → balas sapaan, **jangan** sebut keluhan.
- Keluhan utama hanya muncul saat ditanya keluhannya.
- Tidak menyebut diagnosis sendiri; tidak memakai istilah medis kecuali
  dokter menyebut lebih dulu; kalau tidak tahu → bilang tidak tahu (tidak
  mengarang).

### 2.4 "Disclosure Layers" (lapisan pengungkapan) 🟡 sebagian

Konsep tambahan: informasi pasien dibagi lapisan — *yang sukarela
diceritakan* vs *baru muncul kalau ditanya langsung* vs *tersembunyi
(hanya keluar bila digali sangat spesifik)*. Ini membuat clue diagnostik
"mahal" — mahasiswa harus pintar bertanya.

- ✅ Untuk 22 kasus lama: ada 6 draf lapisan ini (kasus 01, 02, 09, 10, 16, 17).
- ⚠️ Untuk 9 kasus baru aktif: **belum ada lapisan eksplisit**; namun
  persona (Bagian B) sudah memuat aturan menahan jawaban, jadi perilaku
  dasar tetap jalan.

> ### ❓ Untuk didiskusikan (Bagian 2)
> 1. **Realisme persona.** Apakah cara pasien menjawab (lihat contoh
>    dry-eye di Lampiran/uji coba) terasa seperti pasien nyata? Terlalu
>    pintar? Terlalu banyak cerita? Terlalu sedikit?
> 2. **Kelengkapan riwayat.** Untuk tiap kasus, apakah 10 sub-bagian Bagian
>    B sudah memuat semua yang relevan? Adakah yang biasanya Anda tanyakan
>    tapi tak ada datanya (mis. riwayat penggunaan obat tetes steroid,
>    paparan, pekerjaan spesifik)?
> 3. **Clue tersembunyi.** Untuk tiap penyakit, apa **satu-dua clue kunci**
>    yang seharusnya *tidak* langsung diberikan pasien dan hanya muncul bila
>    mahasiswa bertanya tepat? (Ini bahan untuk "disclosure layers".)
> 4. **Istilah & dialek.** Pasien sekarang berbahasa Indonesia kasual
>    (gaya Jakarta). Apakah perlu variasi (pasien desa, lansia, anak via
>    orang tua)?
>
> **Catatan dokter:** ______________________________________________

---

## 3. Matriks Penilaian Anamnesis — INTI DISKUSI

Bagian ini menjawab pertanyaan Anda: **"matriksnya sudah benar belum, dan
sebenarnya bagaimana cara kerjanya?"**

### 3.1 Rubrik penilaian (bobot)

✅ Skor akhir 0–100, terbagi 4 dimensi:

| Dimensi | Bobot | Yang dinilai |
|---|---:|---|
| **Coverage Anamnesis** | **40** | Seberapa lengkap mahasiswa menggali riwayat (keluhan utama, OLDCARTS/SOCRATES, ROS, riwayat dahulu/obat/keluarga/sosial) |
| **FIFE** | **20** | Apakah menggali perspektif pasien: Feeling (perasaan), Idea (anggapan penyebab), Function (dampak ke aktivitas), Expectation (harapan) |
| **Red Flag Screening** | **20** | Apakah menanyakan tanda bahaya yang relevan untuk menyingkirkan kondisi gawat |
| **Komunikasi** | **20** | Empati, urutan logis, tidak memotong, bahasa jelas |

✅ **Bobot ini sama persis dengan dokumen rujukan** proyek (rencana
strategis RAG §8.1). Jadi "sudah sesuai rujukan" — **benar**. Yang belum
divalidasi adalah apakah rujukan itu sendiri sesuai standar penilaian OSCE
yang Anda pakai.

### 3.2 Bagaimana penilaian benar-benar bekerja (jujur, apa adanya)

1. Penilaian dilakukan **setelah sesi selesai** (bukan real-time), supaya
   tak mengganggu alur percakapan.
2. Sistem mengambil **transkrip percakapan** + **DDx & rencana tatalaksana**
   yang ditulis mahasiswa.
3. Sistem mengambil sebuah **"checklist"** dari Bagian A kasus tersebut.
4. Semua itu dikirim ke sebuah **AI penilai** (model terpisah, lebih murah)
   dengan instruksi: *"Kamu penilai OSCE anamnesis. Nilai berdasarkan
   checklist & log percakapan. Beri skor coverage 0–40, FIFE 0–20, red flags
   0–20, komunikasi 0–20, plus daftar yang terlewat, yang sudah baik, dan
   ringkasan saran."*
5. AI penilai mengembalikan skor + umpan balik → ditampilkan di Debrief.

➡️ **Konsekuensi penting yang harus Anda tahu:** penilaian dilakukan oleh
**AI**, bukan oleh aturan kaku/manusia. Kelebihannya: fleksibel, paham
parafrase ("kapan mulai?" = "sejak kapan?"). Kekurangannya: **bisa tidak
konsisten** — sesi yang sama bisa diberi skor sedikit berbeda; AI bisa
"murah hati" atau "pelit". Ini batas yang jujur kami sampaikan.

### 3.3 ⚠️ TEMUAN PENTING — checklist penilaian untuk 9 kasus aktif tidak tepat

Saat menelaah kode untuk dokumen ini, kami menemukan celah nyata:

- Mekanisme penilaian mencari, di Bagian A, sub-bagian yang **bernama
  "Anamnesis"** untuk dijadikan checklist "apa yang seharusnya ditanyakan".
- **22 kasus lama** punya sub-bagian itu: *"### 4. Temuan Klinis —
  Anamnesis"*, lengkap dengan **"Gejala Khas"** + **"Red Flags yang Harus
  Ditanyakan"**. Untuk kasus-kasus ini, penilaian punya dasar yang benar. ✅
- **9 kasus PPK baru (yang justru aktif sekarang)** **tidak punya**
  sub-bagian "Anamnesis" di Bagian A. Akibatnya sistem **terpaksa memakai
  sub-bagian ke-4 yang ada — yaitu "Temuan Klinis Objektif" (hasil
  pemeriksaan fisik: visus, slit-lamp, Schirmer, TBUT).**

**Artinya:** untuk 9 kasus yang sekarang dimainkan, dimensi **Coverage (40)**
dan **Red Flags (20)** dinilai terhadap **daftar temuan pemeriksaan fisik**,
bukan terhadap **daftar pertanyaan anamnesis yang seharusnya diajukan.** AI
penilai tetap menghasilkan angka (ia masih punya log percakapan + pengetahuan
medis umumnya), tetapi **dasar penilaiannya tidak sepadan** dengan yang kita
maksud. Ini menjelaskan kenapa "kita tidak yakin aslinya bagaimana".

**Kabar baiknya:** ini **bukan** cacat desain matriks (bobot 40/20/20/20
tetap sehat) — ini soal **data kasus yang belum lengkap**. Perbaikannya
jelas: tiap kasus harus memuat **checklist anamnesis eksplisit + daftar red
flag**. Dan di sinilah **Case Builder (Bagian 4)** menjadi solusi alami:
formulirnya bisa **mewajibkan** dokter mengisi dua daftar itu, sehingga
setiap kasus baru otomatis "siap-nilai".

> Catatan: perbaikan teknis ini **belum dikerjakan** — kami menunggu arahan
> Anda soal isi checklist yang benar per penyakit (lihat pertanyaan di bawah),
> karena ini keputusan klinis, bukan sekadar koding.

### 3.4 Apa yang BELUM dinilai (mungkin perlu)

- **Ketepatan diagnosis** tidak punya dimensi skor tersendiri. DDx mahasiswa
  hanya "dipertimbangkan" AI dalam penilaian holistik, tidak diberi poin
  eksplisit. ❓ Perlukah dimensi "ketepatan diagnosis banding"?
- **Ketepatan tatalaksana** juga tidak berdimensi sendiri.
- **Efisiensi** (jumlah pertanyaan, durasi) tidak dinilai.
- **Urutan/struktur** anamnesis hanya masuk lewat "Komunikasi" secara umum.

> ### ❓ Untuk didiskusikan (Bagian 3) — paling penting
> 1. **Bobot.** Apakah 40/20/20/20 (Coverage/FIFE/RedFlag/Komunikasi)
>    sesuai standar penilaian anamnesis yang Anda gunakan? Jika tidak, bobot
>    ideal versi Anda?
> 2. **Dimensi tambahan.** Perlukah skor terpisah untuk **ketepatan
>    diagnosis banding** dan/atau **ketepatan tatalaksana**? Berapa bobotnya?
> 3. **Checklist anamnesis per kasus (krusial).** Untuk tiap penyakit,
>    maukah Anda menetapkan **daftar pertanyaan/poin anamnesis wajib** yang
>    jadi acuan "coverage"? (Ini yang sekarang hilang di 9 kasus baru.)
> 4. **Red flags per kasus (krusial).** Untuk tiap penyakit, apa **daftar
>    red flag** yang seharusnya disingkirkan mahasiswa? (mis. nyeri hebat +
>    penurunan visus → glaukoma akut/keratitis.)
> 5. **Toleransi AI menilai.** Apakah Anda nyaman skor diberikan AI (dengan
>    risiko sedikit tidak konsisten), ataukah untuk ujian resmi perlu mode
>    "checklist kaku" (poin per item, deterministik)?
> 6. **Ambang lulus.** Berapa skor minimal "kompeten" menurut Anda
>    (mis. ≥70)? Perlukah label (Kurang/Cukup/Baik/Sangat Baik)?
>
> **Catatan dokter:** ______________________________________________

---

## 4. Case Builder — fitur pembuat kasus untuk dokter

### 4.1 Kondisi sekarang

✅ Sudah ada **Developer Dashboard** (panel admin) tempat kasus bisa dibuat/
diedit. **Tapi** caranya masih: mengisi metadata + **mengetik langsung teks
markdown** kasus di kotak besar. Artinya **pembuat harus paham format/struktur
berkas** (Bagian A, Bagian B, penomoran sub-bagian, dll). Ini menyulitkan bagi
dokter yang bukan teknis.

### 4.2 🟡 Visi Case Builder (yang Anda maksud)

Sebuah **formulir terpandu**: dokter cukup mengisi kolom-kolom data klinis
(seperti mengisi rekam medis), lalu sistem **otomatis menyusun berkas kasus
dalam format yang benar**. Dokter tak perlu tahu markdown sama sekali.

```
  Dokter mengisi formulir              Sistem meng-generate
  ┌────────────────────────┐          ┌─────────────────────────┐
  │ Diagnosis: ___________ │          │ # KASUS NN: ...         │
  │ ICD-10:    ___________ │          │ ## BAGIAN A             │
  │ Identitas pasien: ____ │   ──►     │   ### 1. Diagnosis ...  │
  │ Keluhan utama: _______ │  (auto)   │   ### 4. Anamnesis ...  │
  │ Onset/sifat/...: _____ │          │ ## BAGIAN B (persona)   │
  │ Red flags wajib: _____ │          │   ### 1..10 ...         │
  │ Checklist anamnesis:__ │          │ + disclosure layers     │
  └────────────────────────┘          └─────────────────────────┘
```

### 4.3 🟡 Usulan field formulir (draf — minta koreksi Anda)

**A. Identitas kasus**
- Judul/diagnosis, diagnosis kerja + definisi singkat
- ICD-10, tingkat kemampuan SKDI, sistem organ, tingkat kesulitan
- Tahap (Preklinik/Koas), tipe (Latihan/OSCE), referensi (mis. PPK Kemenkes)

**B. Profil & persona pasien**
- Nama, usia, jenis kelamin, pekerjaan, pendidikan, status
- Sifat/kepribadian, gaya bicara/dialek
- (Anak/tak mampu menjawab? → mode **alloanamnesis** via orang tua)

**C. Riwayat penyakit sekarang (template SOCRATES/OLDCARTS)**
- Keluhan utama + durasi
- Lokasi, onset, karakter, penjalaran, gejala penyerta, waktu,
  pemberat/peringan, derajat

**D. Riwayat lain**
- ROS terkait, riwayat penyakit dahulu, obat, keluarga, sosial/lingkungan
- FIFE (perasaan / anggapan / dampak / harapan)

**E. Data untuk penilaian (yang sekarang hilang — wajib)**
- **Checklist anamnesis wajib** (daftar poin yang seharusnya digali) → dasar
  skor Coverage
- **Daftar red flags** yang harus disingkirkan → dasar skor Red Flag
- (opsional) **Clue tersembunyi** + pemicunya → disclosure layers

**F. Data pemeriksaan fisik (opsional, untuk fitur lanjutan)**
- Visus, TIO, pupil, slit-lamp, fundus, dll
- Foto mata (bisa diunggah; lihat 6.2)

### 4.4 Pertimbangan

- ✅ **Keuntungan**: konsistensi format terjamin; dokter mandiri menambah
  kasus tanpa tim teknis; setiap kasus otomatis lengkap untuk penilaian.
- ⚠️ **Effort dokter**: makin banyak field, makin lama mengisi. Perlu cari
  titik seimbang (field wajib minimum vs opsional).
- 🟡 **Opsi bantuan AI**: sistem bisa membantu **men-draf** persona dari
  poin-poin singkat dokter, lalu **dokter mengoreksi/menyetujui**. (Tetap:
  AI draf, dokter validasi — tidak pernah AI yang "memutuskan" isi klinis.)

> ### ❓ Untuk didiskusikan (Bagian 4)
> 1. **Field.** Dari daftar 4.3, mana yang **wajib**, mana **opsional**,
>    apa yang **kurang**? Bisakah dipangkas agar tidak melelahkan?
> 2. **Effort.** Berapa lama waktu wajar bagi Anda untuk membuat 1 kasus
>    (5 menit? 20 menit?)? Ini menentukan seberapa "ringkas" formulirnya.
> 3. **Bantuan AI.** Apakah Anda mau sistem **men-draf persona otomatis**
>    dari poin singkat (lalu Anda koreksi), atau Anda lebih suka mengisi
>    semua manual agar kontrol penuh?
> 4. **Alur persetujuan.** Perlukah status "draf → ditinjau → disetujui"
>    sebelum kasus bisa dimainkan mahasiswa? Siapa yang berwenang menyetujui?
> 5. **Prioritas.** Seberapa penting Case Builder dibanding perbaikan lain
>    (mis. memperbaiki checklist penilaian lebih dulu)?
>
> **Catatan dokter:** ______________________________________________

---

## 5. Validasi konten klinis 9 kasus aktif

✅ Sembilan kasus PPK Kemenkes preklinik yang sekarang aktif (disusun tim,
**mohon validasi klinis Anda**):

| ID | Kasus | Tingkat (SKDI) |
|---|---|---|
| 101 | Mata Kering (Dry Eye) | 4A |
| 102 | Buta Senja (Xeroftalmia/defisiensi vit. A) | — |
| 103 | Hordeolum | 4A |
| 104 | Konjungtivitis (bakteri) | 4A |
| 105 | Blefaritis | 4A |
| 106 | Katarak (senilis) | 2 |
| 107 | Glaukoma (akut) | 3B |
| 108 | Episkleritis | 4A |
| 109 | Hifema | — |

Untuk **tiap** kasus, mohon nilai:

1. **Akurasi diagnosis & definisi** — sudah benar?
2. **Persona realistis** — keluhan, gaya bicara, perjalanan penyakit masuk
   akal? (mis. dry-eye dengan "paradoxical tearing" — mata malah berair —
   apakah tepat dipakai sebagai clue?)
3. **Kelengkapan riwayat** — ada yang kurang/janggal?
4. **Checklist anamnesis** — apa poin wajib yang harus digali (untuk skor)?
5. **Red flags** — apa tanda bahaya yang harus disingkirkan?
6. **Tatalaksana** — sesuai PPK/praktik Anda?
7. **Tingkat kesulitan & tahap** — pas untuk preklinik?

> ### ❓ Untuk didiskusikan (Bagian 5)
> - Mana kasus yang **paling siap** dan mana yang **perlu revisi besar**?
> - Apakah ada **diagnosis penting** yang belum ada dan sebaiknya
>   diprioritaskan (mis. uveitis, keratitis, ablasio, kelainan refraksi)?
> - Untuk **22 kasus lama yang dikunci**, apakah perlu diaktifkan kembali,
>   direvisi, atau dipensiunkan?
>
> **Catatan dokter:** ______________________________________________

---

## 6. Topik lain untuk didiskusikan

### 6.1 🟡 Suara (bicara dengan pasien, bukan mengetik)

Arsitektur sudah siap untuk **input suara** (mahasiswa bicara → diubah jadi
teks) dan **output suara** (pasien AI menjawab dengan suara). Saat ini
**sengaja dimatikan**. Pertanyaan: ❓ apakah berbicara (lebih mirip OSCE
nyata) penting, atau mengetik sudah cukup untuk tahap ini?

### 6.2 ✅/❓ Foto kondisi mata

Saat anamnesis, ada tombol **"👁 Lihat Kondisi Mata"** yang bisa menampilkan
foto mata pasien (bila kasus punya foto). ❓ Secara pedagogis: di tahap
anamnesis (sebelum pemeriksaan fisik), **bolehkah** mahasiswa sudah melihat
foto? Atau sebaiknya foto muncul **setelah** mahasiswa "memutuskan
memeriksa"? Foto apa yang Anda anggap layak (tanpa langsung membocorkan
diagnosis)?

### 6.3 🟡 Simulator Pemeriksaan Fisik (dorman)

Pernah dirancang modul simulasi pemeriksaan mata (visus, slit-lamp, RAPD,
funduskopi, dll) tapi **belum diaktifkan**. ❓ Apakah simulasi pemeriksaan
fisik perlu jadi bagian alur, atau fokus dulu ke anamnesis murni?

### 6.4 ❓ Pasien anak / alloanamnesis

Beberapa kasus lama melibatkan pasien anak (anamnesis lewat orang tua).
❓ Seberapa penting skenario ini untuk oftalmologi (mis. leukokoria,
strabismus, ambliopia)?

### 6.5 ❓ Umpan balik ke mahasiswa

Debrief sekarang memberi: skor per dimensi, daftar terlewat, daftar yang
baik, ringkasan naratif (lihat **Lampiran B**). ❓ Apakah ini cukup mendidik?
Perlukah contoh "pertanyaan ideal" yang seharusnya diajukan? Perlukah
perbandingan dengan jawaban pasien yang terlewat?

### 6.6 ❓ Integritas / anti-contek

Persona & jawaban "benar" tak pernah dikirim ke layar mahasiswa (hanya di
server). Namun untuk ujian resmi, ❓ apakah perlu mode terkunci, batas waktu,
atau pengacakan kasus?

### 6.7 ❓ Konteks penggunaan & skala

❓ Untuk siapa terutama (preklinik FK / koas / PPDS)? Dipakai mandiri
(latihan) atau terbimbing (ujian)? Target jumlah kasus (10? 50? 100?) — ini
memengaruhi prioritas Case Builder.

> ### ❓ Catatan bebas dokter (Bagian 6)
> ______________________________________________________________
> ______________________________________________________________

---

## 7. Ringkasan keputusan terbuka (lembar centang)

Ringkasan agar mudah ditindaklanjuti setelah diskusi:

| # | Keputusan | Pilihan/Isian dokter |
|---|---|---|
| K1 | Bobot rubrik 40/20/20/20 disetujui? | ☐ Ya ☐ Ubah: ______ |
| K2 | Tambah dimensi "ketepatan diagnosis"? | ☐ Tidak ☐ Ya, bobot ___ |
| K3 | Tambah dimensi "ketepatan tatalaksana"? | ☐ Tidak ☐ Ya, bobot ___ |
| K4 | Checklist anamnesis wajib per kasus | ☐ Dokter akan susun ☐ Bantu draf AI |
| K5 | Daftar red flags per kasus | ☐ Dokter akan susun ☐ Bantu draf AI |
| K6 | Mode penilaian | ☐ AI fleksibel ☐ Checklist kaku (ujian) |
| K7 | Ambang lulus / label nilai | ______ |
| K8 | Case Builder: prioritas | ☐ Tinggi ☐ Sedang ☐ Nanti |
| K9 | Case Builder: bantuan draf AI | ☐ Ya ☐ Tidak (manual) |
| K10 | Suara (STT/TTS) diaktifkan? | ☐ Ya ☐ Belum perlu |
| K11 | Foto mata saat anamnesis | ☐ Boleh ☐ Setelah "periksa" ☐ Tidak |
| K12 | Simulator pemeriksaan fisik | ☐ Perlu ☐ Tunda |
| K13 | 22 kasus koas lama | ☐ Aktifkan ☐ Revisi ☐ Pensiun |
| K14 | Diagnosis prioritas berikutnya | ______ |

---

## Lampiran A — Glosarium istilah teknis

| Istilah | Arti sederhana |
|---|---|
| **AI / LLM** | Kecerdasan buatan yang bisa "mengobrol" — di sini berperan jadi pasien & jadi penilai |
| **Anamnesis (di sistem)** | Tahap tanya-jawab mahasiswa ↔ pasien AI |
| **Persona** | Skenario karakter pasien yang "dijiwai" AI |
| **Answer restraint** | Aturan agar pasien hanya menjawab yang ditanya, tidak membocorkan semua |
| **Disclosure layers** | Pembagian info pasien jadi lapisan (sukarela / bila ditanya / tersembunyi) |
| **Checklist** | Daftar acuan "apa yang seharusnya ditanyakan" — dasar penilaian coverage |
| **Rubrik** | Pedoman pemberian skor (dimensi + bobot) |
| **LLM-as-judge** | Penilaian sesi dilakukan oleh AI, bukan aturan kaku/manusia |
| **FIFE** | Feeling, Idea, Function, Expectation — perspektif pasien |
| **SOCRATES / OLDCARTS** | Kerangka menggali keluhan (lokasi, onset, sifat, dll) |
| **Red flag** | Tanda bahaya yang wajib disingkirkan |
| **DDx** | Diagnosis banding |
| **SKDI** | Standar Kompetensi Dokter Indonesia (tingkat kemampuan, mis. 4A) |
| **PPK** | Panduan Praktik Klinis (Kemenkes) |
| **Case Builder** | Formulir untuk membuat kasus baru tanpa perlu paham format teknis |
| **Markdown** | Format teks berstruktur tempat kasus disimpan |
| **Developer Dashboard** | Panel admin untuk kelola kasus & foto |
| **PPDS / Koas / Preklinik** | Jenjang pendidikan dokter |

---

## Lampiran B — Contoh laporan penilaian (yang dilihat mahasiswa)

Setelah sesi, mahasiswa melihat kira-kira seperti ini (angka contoh):

```
Skor Total: 74 / 100

  Coverage Anamnesis ............ 32 / 40
  FIFE .......................... 14 / 20
  Red Flag Screening ............ 16 / 20
  Komunikasi .................... 12 / 20

Yang sudah baik:
  • Menggali onset & perjalanan keluhan dengan runtut
  • Menanyakan dampak ke pekerjaan (Function)

Yang terlewat:
  • Tidak menanyakan riwayat penggunaan obat tetes mata
  • Tidak menyingkirkan nyeri hebat / penurunan visus (red flag)
  • Tidak menggali harapan pasien (Expectation)

Ringkasan & saran:
  "Anamnesis cukup terstruktur dan empatik. Penggalian riwayat
   pengobatan dan skrining red flag perlu diperkuat. Diagnosis banding
   sudah mengarah tepat; pertimbangkan menambah pemeriksaan penunjang
   pada rencana tatalaksana."
```

> ❓ **Untuk dokter:** apakah format umpan balik ini sudah mendidik dan
> cukup spesifik? Apa yang ingin Anda tambah/ubah?

---

*Dokumen ini disiapkan sebagai bahan diskusi. Semua konten klinis di dalam
sistem berstatus draf tim pengembang dan menunggu validasi dokter mata.
Hasil diskusi akan dicatat sebagai keputusan resmi dan memandu perbaikan
selanjutnya (termasuk perbaikan checklist penilaian untuk 9 kasus aktif dan
desain Case Builder).*
