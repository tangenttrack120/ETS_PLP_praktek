# Laporan Bug

Salin blok di bawah untuk setiap bug. Bagian **Akar masalah** wajib ditulis dengan kata-kata
sendiri dan memakai konsep dari _Crafting Interpreters_ (sebutkan bab). Bagian ini diuji lisan.

---

## Bug 1: (LexError pada test_komentar_block() di test_lexer.py)

**Ditemukan oleh:** (Richard) · **Diperbaiki oleh:** (Richard)

**Gejala.** Saat menjalankan pytest pada bagian test_lexer.py, test_komentar_block() gagal dan memberikan error message "LexError" saat bertemu "/\*".

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql

```

**Akar masalah.** Di dalam lexer.py, saat lexer menemukan karakter / yang diikuti oleh \*, kode akan memicu bagian kode (stub) yang secara eksplisit melontarkan pengecualian LexError("komentar blok belum didukung", line, col). test_komentar_blok() mengharuskan lexer untuk melewati seluruh blok komentar tersebut, sembari tetap memperbarui jumlah baris dan kolom secara akurat, termasuk untuk komentar yang mencakup beberapa baris.

**Perbaikan.** File yang diubah adalah lexer.py pada fungsi \_scan*token() dikarenakan kode belum lengkap (TODO(T3): dukung komentar blok /* ... \_/ (SPESIFIKASI.md bagian 2.3)).

**Test regresi.** test_komentar_block() di test_lexer.py.

**Peran AI.** Bug ditemukan saat menjalankan pytest, peran AI pada bug ini adalah brainstorming dan memahami syntax

---

## Bug 2: (ParseError pada test_insert_select() di test_parser.py)

**Ditemukan oleh:** (Richard) · **Diperbaiki oleh:** (nama)

**Gejala.** Saat menjalankan pytest pada bagian test_parse.py, test_insert_select() gagal dan memberikan error message ParseError saat membaca keyword SELECT.

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql

```

**Akar masalah.** Mengapa kode lama salah? Konsep apa yang dilanggar?

**Perbaikan.** File dan fungsi yang diubah, serta alasannya. Sebutkan juga perbaikan
alternatif yang kalian pertimbangkan dan alasan tidak memilihnya.

**Test regresi.** Nama test di `tests/test_tambahan.py` yang gagal sebelum perbaikan dan lulus
sesudahnya.

**Peran AI.** Apakah AI membantu menemukan atau memperbaiki bug ini? Bagaimana kalian
memverifikasinya?

---

## Bug 3: (kegagalan pada test_kolom_tanpa_qualifier_satu_tabel() di test_resolver.py)

**Ditemukan oleh:** (Richard) · **Diperbaiki oleh:** (nama)

**Gejala.** test_kolom_tanpa_qualifier_satu_tabel() di test_resolver.py gagal.

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql

```

**Akar masalah.** Mengapa kode lama salah? Konsep apa yang dilanggar?

**Perbaikan.** File dan fungsi yang diubah, serta alasannya. Sebutkan juga perbaikan
alternatif yang kalian pertimbangkan dan alasan tidak memilihnya.

**Test regresi.** Nama test di `tests/test_tambahan.py` yang gagal sebelum perbaikan dan lulus
sesudahnya.

**Peran AI.** Apakah AI membantu menemukan atau memperbaiki bug ini? Bagaimana kalian
memverifikasinya?

---

## Bug 4: (bug)

**Ditemukan oleh:** (nama) · **Diperbaiki oleh:** (nama)

**Gejala.** Input, output yang didapat, dan output yang diharapkan menurut SPESIFIKASI.md
(sebutkan bagiannya).

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql

```

**Akar masalah.** Mengapa kode lama salah? Konsep apa yang dilanggar?

**Perbaikan.** File dan fungsi yang diubah, serta alasannya. Sebutkan juga perbaikan
alternatif yang kalian pertimbangkan dan alasan tidak memilihnya.

**Test regresi.** Nama test di `tests/test_tambahan.py` yang gagal sebelum perbaikan dan lulus
sesudahnya.

**Peran AI.** Apakah AI membantu menemukan atau memperbaiki bug ini? Bagaimana kalian
memverifikasinya?

---
