# Laporan Bug

Salin blok di bawah untuk setiap bug. Bagian **Akar masalah** wajib ditulis dengan kata-kata
sendiri dan memakai konsep dari _Crafting Interpreters_ (sebutkan bab). Bagian ini diuji lisan.

---

## Bug 1: (LexError pada test_komentar_block() di test_lexer.py)

**Ditemukan oleh:** (Richard) · **Diperbaiki oleh:** (Richard)

**Gejala.** Saat menjalankan pytest pada bagian test_lexer.py, test_komentar_block() gagal dan memberikan error message "LexError" saat bertemu "/\*".

**Reproduksi minimal.**

```sql
SELECT id /* komentar */ FROM t
```

**Akar masalah.** Di dalam lexer.py, saat lexer menemukan karakter / yang diikuti oleh \*, kode akan memicu bagian kode (stub) yang secara eksplisit melontarkan pengecualian LexError("komentar blok belum didukung", line, col). test_komentar_blok() mengharuskan lexer untuk melewati seluruh blok komentar tersebut, sembari tetap memperbarui jumlah baris dan kolom secara akurat, termasuk untuk komentar yang mencakup beberapa baris.

**Perbaikan.** File yang diubah adalah lexer.py pada fungsi \_scan_token() dikarenakan kode belum lengkap (TODO(T3): dukung komentar blok /\* ... \*/ (SPESIFIKASI.md bagian 2.3)).

**Test regresi.** `test_komentar_block()` di `test_lexer.py`.

**Peran AI.** Bug ditemukan saat menjalankan pytest, peran AI pada bug ini adalah brainstorming dan memahami syntax

---

## Bug 2: (ParseError pada test_insert_select() di test_parser.py)

**Ditemukan oleh:** (Richard) · **Diperbaiki oleh:** (Richard)

**Gejala.** Saat menjalankan pytest pada bagian test_parse.py, test_insert_select() gagal dan memberikan error message ParseError saat membaca keyword SELECT.

**Reproduksi minimal.**

```sql
INSERT INTO arsip SELECT id FROM pesanan
```

**Akar masalah.** Kode lama belum mendukung INSERT INTO ... SELECT ...

**Perbaikan.** parser.py fungsi \_insert() dikarenakan kode belum mendukung INSERT INTO ... SELECT ... seperti di spesifikasi.md poin 3 dan 5.

**Test regresi.** `test_insert_select()` di `test_parser.py`.

**Peran AI.** Bug ditemukan saat menjalankan pytest, peran AI pada bug ini adalah brainstorming dan memahami syntax

---

## Bug 3: Kolom tanpa qualifier belum di-resolve (T2), lalu versi awal melihat semua scope

**Ditemukan oleh:** Richard · **Diperbaiki oleh:** Richard, dikoreksi Afzal

**Gejala.** `test_kolom_tanpa_qualifier_satu_tabel()` gagal karena `_column` hanya berisi
`pass`. Versi perbaikan pertama mencari tabel di **semua** scope sampai ke luar, sehingga
`pelanggan_id` di subquery dilaporkan ambigu, dan kolom yang merujuk subquery di FROM tidak
di-resolve.

**Reproduksi minimal.**

```sql
SELECT p.id FROM pelanggan p WHERE p.id IN (SELECT pelanggan_id FROM pesanan)
```

**Akar masalah.** Kolom tanpa qualifier tidak menyebut tabelnya, dan karena tidak ada skema
database kita tidak tahu tabel mana yang benar-benar punya kolom itu. Spesifikasi 4.3 memilih
aturan sederhana: hanya scope terdalam, yaitu SELECT tempat kolom itu ditulis. Kode awal belum
mengerjakan aturan ini sama sekali. Versi pertama perbaikannya memakai cara pencarian kolom
ber-qualifier (naik lewat rantai induk scope, Bab 11.3), padahal kolom tanpa qualifier tidak
boleh naik. Akibatnya tabel milik query luar ikut terhitung dan kolom di subquery dianggap
ambigu. Versi itu juga hanya menghitung entri yang punya tabel asli, sehingga subquery di FROM
tidak terhitung.

**Perbaikan.** `crud/resolver.py`, `Resolver._column`: hanya `self.scope.entries` (scope
terdalam) yang dihitung, termasuk subquery di FROM (lewat `_target_of`). Satu entri →
`resolved` diisi; lebih dari satu → warning ambigu; nol → warning. Alternatif yang ditolak:
naik ke scope induk (melanggar 4.3 dan membuat hampir semua kolom correlated subquery ambigu).

**Test regresi.** `test_t2_kolom_tanpa_qualifier_ambigu`,
`test_t2_kolom_tanpa_qualifier_hanya_scope_terdalam`, `test_t2_kolom_tanpa_tabel_di_scope`,
`test_t2_kolom_merujuk_subquery_di_from`.

**Peran AI.** Versi awal: AI dipakai untuk brainstorming. Koreksi scope terdalam ditemukan
Claude saat membandingkan kode dengan SPESIFIKASI.md 4.3. Diverifikasi dengan dua test T2 baru
yang gagal di versi awal dan lulus setelah koreksi.

---

## Bug 4: Keyword hanya dikenali jika ditulis huruf besar

**Ditemukan oleh:** Afzal (dengan bantuan Claude) · **Diperbaiki oleh:** Afzal

**Gejala.** `select id from t` menghasilkan token `IDENT 'select'`, bukan `KEYWORD 'SELECT'`,
sehingga parser gagal ("diharapkan awal statement"). Seluruh `pemeliharaan.sql` (huruf kecil)
gagal di-parse. SPESIFIKASI.md 2.2: keyword tidak peka huruf besar/kecil dan nilainya
dinormalisasi ke huruf besar.

**Reproduksi minimal.**

```sql
select id from t
```

**Akar masalah.** Lexer membaca satu kata utuh dulu, baru mengecek apakah kata itu reserved word (Bab 4.7). Pengecekannya memakai teks mentah ke `KEYWORDS` yang isinya huruf besar semua, jadi `select` dan `Select` tidak cocok dan dianggap `IDENT`. Padahal di SQL keyword tidak peka huruf besar/kecil. Seharusnya kata dinormalisasi dulu sebelum dicek, dan nilai token keyword disimpan dalam bentuk huruf besar supaya parser cukup membandingkan dengan satu bentuk.

**Perbaikan.** `crud/lexer.py`, `Lexer._word`: kata dicocokkan dengan `text.upper() in KEYWORDS`
dan nilai token keyword disimpan sebagai `text.upper()`. Alternatif yang ditolak: menambahkan
versi huruf kecil ke `KEYWORDS` (tidak menangani `Select`/`sElEcT`, dan `KEYWORDS` adalah API
publik); menormalisasi di parser (parser jadi harus tahu soal huruf, dan nilai token tetap
melanggar 2.2).

**Test regresi.** `test_bug1_keyword_huruf_campuran_dinormalisasi`

**Peran AI.** Bug ditemukan Claude saat membandingkan kode dengan SPESIFIKASI.md. Perbaikan, bagian akar masalah, dan draft laporan ini dibuat dengan bantuan Claude. Diverifikasi dengan test regresi yang gagal di kode asli dan lulus setelah perbaikan, serta `python evaluate.py`.

---

## Bug 5: Operator `<>` dipecah menjadi `<` dan `>`

**Ditemukan oleh:** Richard · **Diperbaiki oleh:** Afzal

**Gejala.** `a <> b` menghasilkan `OP '<'`, `OP '>'`. Statement baris 3 `laporan_penjualan.sql`
(`o.catatan <> 'FROM rahasia'`) gagal di-parse sehingga tabel `pelanggan` dan `pesanan` hilang
dari matrix. SPESIFIKASI.md 2.5: `<>` satu token (maximal munch).

**Reproduksi minimal.**

```sql
SELECT id FROM t WHERE a <> b
```

**Akar masalah.** Operator dua karakter dikenali dengan `match`, yaitu maju satu karakter hanya kalau karakter berikutnya cocok (Bab 4.5). Cabang untuk `<` hanya mengecek `=`, sedangkan kemungkinan `>` terlupa. Akibatnya `<>` dipotong jadi dua token. Ini melanggar prinsip *maximal munch*: lexer harus mengambil lexeme terpanjang yang sah.

**Perbaikan.** `crud/lexer.py`, `Lexer._scan_token` cabang `<`: setelah `<`, coba `_match("=")`
lalu `_match(">")`. Alternatif yang ditolak: menggabungkan `<` `>` di parser (melanggar 2.5,
dan `a < > b` dengan spasi akan ikut diterima padahal bukan operator yang sah).

**Test regresi.** `test_bug2_operator_tidak_sama_dengan_satu_token`

**Peran AI.** Bug dicatat Richard saat menjalankan pytest dan membaca spesifikasi. Perbaikan, bagian akar masalah, dan draft laporan ini dibuat dengan bantuan Claude. Diverifikasi dengan test regresi yang gagal di kode asli dan lulus setelah perbaikan, serta `python evaluate.py`.

---

## Bug 6: Kutip ganda `''` di dalam string tidak didukung

**Ditemukan oleh:** Richard · **Diperbaiki oleh:** Afzal

**Gejala.** `'O''Brien'` menjadi dua token `STRING 'O'` dan `STRING 'Brien'`, sehingga statement
baris 3 dan 8 `pemeliharaan.sql` gagal di-parse. SPESIFIKASI.md 2.4: `''` mewakili satu kutip,
hasilnya satu token bernilai `O'Brien`.

**Reproduksi minimal.**

```sql
SELECT id FROM t WHERE nama = 'O''Brien'
```

**Akar masalah.** String adalah lexeme panjang: lexer maju terus sampai menemukan kutip penutup (Bab 4.6). Masalahnya, kode lama langsung menganggap setiap `'` sebagai penutup tanpa mengintip karakter sesudahnya. Di SQL, `''` artinya satu karakter kutip di dalam string. Tanpa lookahead satu karakter, lexer tidak bisa membedakan kutip penutup dari kutip yang di-escape, jadi string terpotong di tengah.

**Perbaikan.** `crud/lexer.py`, `Lexer._string`: saat menemukan `'`, intip karakter berikutnya.
Jika `'` juga, tambahkan satu kutip ke nilai dan lanjutkan; jika bukan, string selesai.
Alternatif yang ditolak: mengganti `''` dengan `'` lewat `str.replace` sebelum lexing (merusak
kolom token dan mengubah string kosong `''`).

**Test regresi.** `test_bug3_kutip_ganda_dalam_string`

**Peran AI.** Bug dicatat Richard saat menjalankan pytest dan membaca spesifikasi. Perbaikan, bagian akar masalah, dan draft laporan ini dibuat dengan bantuan Claude. Diverifikasi dengan test regresi yang gagal di kode asli dan lulus setelah perbaikan, serta `python evaluate.py`.

---

## Bug 7: Error recovery membuang semua token sampai akhir file

**Ditemukan oleh:** Richard · **Diperbaiki oleh:** Afzal

**Gejala.** Pada `campuran_error.sql`, setelah error di baris 4, statement `UPDATE` (baris 6)
dan `DELETE` (baris 8) yang valid ikut hilang. SPESIFIKASI.md 6: buang token sampai dan
termasuk `;` berikutnya, lalu lanjutkan.

**Reproduksi minimal.**

```sql
SELECT id nama, FROM t;
DELETE FROM u;
```

**Akar masalah.** Panic mode (Bab 6.3.3) berarti setelah error, parser membuang token sampai titik aman, lalu lanjut parsing. Tujuannya supaya satu error tidak menimbulkan error beruntun, dan statement valid sesudahnya tetap diproses. Kode lama tidak punya kondisi berhenti, jadi titik amannya baru tercapai di EOF dan seluruh sisa file ikut terbuang. Di SQL, batas statement yang pasti adalah `;`, jadi sinkronisasi harus berhenti tepat setelah `;`.

**Perbaikan.** `crud/parser.py`, `Parser._synchronize`: berhenti setelah meng-*advance* token
`SEMICOLON`. Alternatif yang ditolak: sinkronisasi di keyword awal statement (`SELECT`, dst.),
karena `SELECT` juga muncul di dalam subquery dan `INSERT ... SELECT`, sehingga parser bisa
melanjutkan di tengah statement rusak dan menghasilkan lebih dari satu error.

**Test regresi.** `test_bug4_error_recovery_lanjut_setelah_titik_koma`

**Peran AI.** Bug dicatat Richard saat menjalankan pytest dan membaca spesifikasi. Perbaikan, bagian akar masalah, dan draft laporan ini dibuat dengan bantuan Claude. Diverifikasi dengan test regresi yang gagal di kode asli dan lulus setelah perbaikan, serta `python evaluate.py`.

---

## Bug 8: `AND` dan `OR` berada di tingkat presedensi yang sama

**Ditemukan oleh:** Afzal (dengan bantuan Claude) · **Diperbaiki oleh:** Afzal

**Gejala.** `a = 1 OR b = 2 AND c = 3` di-parse menjadi `(a = 1 OR b = 2) AND c = 3`.
SPESIFIKASI.md 3.1: `AND` lebih kuat, seharusnya `a = 1 OR (b = 2 AND c = 3)`. CRUD matrix
tidak berubah, tetapi AST salah (lihat `--ast` pada `audit.sql` baris 2 dan `pemeliharaan.sql`
baris 3).

**Reproduksi minimal.**

```sql
SELECT id FROM t WHERE a = 1 OR b = 2 AND c = 3
```

**Akar masalah.** Presedensi dikodekan lewat bertingkatnya aturan grammar (Bab 5.1, 6.1–6.2): satu tingkat presedensi = satu aturan = satu fungsi, dan fungsi untuk operator yang lebih lemah memanggil fungsi untuk operator yang lebih kuat. Kode lama menggabungkan `or_expr` dan `and_expr` ke satu loop, sehingga `AND` dan `OR` dianggap sama kuat. Karena loop-nya asosiatif kiri, ekspresi dibaca begitu saja dari kiri ke kanan: `a OR b AND c` jadi `(a OR b) AND c`. CRUD matrix tidak berubah, tetapi AST-nya salah.

**Perbaikan.** `crud/parser.py`: `_logical` dipecah menjadi `_or` (memanggil `_and`) dan `_and`
(memanggil `_not`), satu fungsi per aturan `or_expr` dan `and_expr`. Alternatif yang ditolak:
tabel presedensi (precedence climbing / Pratt), karena tidak lagi berpadanan satu-satu dengan
grammar di spesifikasi.

**Test regresi.** `test_bug5_and_lebih_kuat_dari_or`

**Peran AI.** Bug ditemukan Claude saat membandingkan kode dengan SPESIFIKASI.md. Perbaikan, bagian akar masalah, dan draft laporan ini dibuat dengan bantuan Claude. Diverifikasi dengan test regresi yang gagal di kode asli dan lulus setelah perbaikan, serta `python evaluate.py`.

---

## Bug 9: `LEFT OUTER JOIN` ditolak parser

**Ditemukan oleh:** Richard · **Diperbaiki oleh:** Afzal

**Gejala.** `LEFT OUTER JOIN` menghasilkan error "diharapkan JOIN, ditemukan 'OUTER'".
Grammar `join` (SPESIFIKASI.md 3): `"LEFT" [ "OUTER" ]`.

**Reproduksi minimal.**

```sql
SELECT a.id FROM a LEFT OUTER JOIN b ON b.a_id = a.id
```

**Akar masalah.** Di recursive descent (Bab 6.2), setiap fungsi parser harus menerima persis kalimat yang diterima aturan grammar-nya. Aturan `join` punya bagian opsional `[ "OUTER" ]` setelah `LEFT`, tetapi `_join` tidak pernah mencoba mencocokkan `OUTER`. Fungsinya jadi menerima lebih sedikit daripada grammar, dan query yang sah ditolak.

**Perbaikan.** `crud/parser.py`, `Parser._join`: setelah `LEFT`, panggil `_match_kw("OUTER")`
(opsional). Alternatif yang ditolak: menjadikan `OUTER` token yang diabaikan lexer (lexer
tidak boleh membuang keyword; `OUTER` di posisi lain harus tetap error).

**Test regresi.** `test_bug6_left_outer_join_diterima`

**Peran AI.** Bug dicatat Richard saat menjalankan pytest dan membaca spesifikasi. Perbaikan, bagian akar masalah, dan draft laporan ini dibuat dengan bantuan Claude. Diverifikasi dengan test regresi yang gagal di kode asli dan lulus setelah perbaikan, serta `python evaluate.py`.

---

## Bug 10: Pencarian alias dimulai dari scope terluar

**Ditemukan oleh:** Afzal (dengan bantuan Claude) · **Diperbaiki oleh:** Afzal

**Gejala.** Di `audit.sql` baris 12, `x.pelanggan_id` di dalam subquery di-resolve ke
`pelanggan` (alias `x` luar), padahal `x` di subquery adalah `pesanan`. SPESIFIKASI.md 4.3:
qualifier dicari dari scope terdalam ke luar (shadowing).

**Reproduksi minimal.**

```sql
SELECT x.id FROM pelanggan x WHERE x.id IN (SELECT x.pelanggan_id FROM pesanan x)
```

**Akar masalah.** Scope bersarang mengikuti struktur query: subquery punya scope sendiri yang induknya scope query luar. Saat mencari nama, scope terdekat harus menang, ini yang disebut shadowing (Bab 8.5). Di buku, `resolveLocal` mencari mulai dari scope paling dalam lalu keluar (Bab 11.3). Kode lama membalik urutannya (`reversed(chain)`), jadi yang ditemukan duluan selalu scope terluar. Alias `x` di subquery tertutup oleh `x` di query luar.

**Perbaikan.** `crud/resolver.py`, `Resolver._lookup`: telusuri `self.scope`, lalu `.parent`,
dan kembalikan entri pertama yang cocok. Alternatif yang ditolak: menggabungkan semua scope
ke satu dict (shadowing dan batas statement hilang).

**Test regresi.** `test_bug7_alias_subquery_menutupi_alias_luar`

**Peran AI.** Bug ditemukan Claude saat membandingkan kode dengan SPESIFIKASI.md. Perbaikan, bagian akar masalah, dan draft laporan ini dibuat dengan bantuan Claude. Diverifikasi dengan test regresi yang gagal di kode asli dan lulus setelah perbaikan, serta `python evaluate.py`.

---

## Bug 11: Scope `DELETE` tidak pernah ditutup

**Ditemukan oleh:** Afzal (dengan bantuan Claude) · **Diperbaiki oleh:** Afzal

**Gejala.** Di `audit.sql`, `SELECT s.id FROM pengguna u` (baris 18) tidak menghasilkan error,
dan `s.id` di-resolve ke `sesi` milik `DELETE` baris 16. SPESIFIKASI.md 4.5: alias statement
sebelumnya tidak boleh terlihat; seharusnya error `alias 's' tidak terdefinisi`.

**Reproduksi minimal.**

```sql
DELETE FROM sesi s WHERE s.id = 1;
SELECT s.id FROM pengguna u;
```

**Akar masalah.** Resolver menyimpan scope sebagai tumpukan (stack): setiap `beginScope` wajib dipasangkan dengan `endScope` (Bab 11.3). `_delete` membuat scope dengan `_push` tetapi tidak pernah `_pop`. Scope DELETE jadi tersisa dan menjadi induk statement berikutnya, sehingga alias `s` masih ditemukan di `SELECT` sesudahnya. Ini melanggar static scope: sebuah nama hanya berlaku di dalam statement tempat ia dideklarasikan.

**Perbaikan.** `crud/resolver.py`, `Resolver._delete`: tambahkan `self._pop()` di akhir.
Alternatif yang ditolak: me-reset `self.scope = None` di `resolve_script` sebelum tiap statement
(menutupi gejala, tetapi pasangan push/pop di `_delete` tetap rusak, misalnya untuk DELETE di
masa depan yang bersarang).

**Test regresi.** `test_bug8_alias_delete_tidak_bocor`

**Peran AI.** Bug ditemukan Claude saat membandingkan kode dengan SPESIFIKASI.md. Perbaikan, bagian akar masalah, dan draft laporan ini dibuat dengan bantuan Claude. Diverifikasi dengan test regresi yang gagal di kode asli dan lulus setelah perbaikan, serta `python evaluate.py`.

---

## Bug 12: Tabel di subquery `UPDATE` ditandai U, bukan R

**Ditemukan oleh:** Afzal (dengan bantuan Claude) · **Diperbaiki oleh:** Afzal

**Gejala.** `laporan_penjualan.sql` baris 12: `pesanan` (hanya dibaca di subquery `WHERE`)
mendapat `U`, sehingga matrix `pesanan` menjadi `RUD` bukan `RD`. SPESIFIKASI.md 5: tabel yang
dibaca lewat subquery selalu R; hanya tabel target yang U.

**Reproduksi minimal.**

```sql
UPDATE pelanggan SET level = 'gold' WHERE id IN (SELECT pelanggan_id FROM pesanan)
```

**Akar masalah.** Saat menelusuri AST (Bab 5), arti sebuah node ditentukan oleh jenis node-nya, bukan oleh statement luarnya. Huruf U hanya milik tabel target `UPDATE`. Kode lama meneruskan parameter `op="U"` ke seluruh sub-pohon `SET` dan `WHERE`, sehingga tabel di dalam subquery ikut ditandai U. Padahal subquery hanya membaca data, jadi selalu R (SPESIFIKASI.md 5).

**Perbaikan.** `crud/analyzer.py`, `analyze_statement` cabang `Update`: `_collect(..., "R")`
untuk nilai `SET` dan `WHERE`. Alternatif yang ditolak: membuang `U` di `format_ops` untuk
tabel non-target (menambal gejala di pipeline, analyzer tetap salah).

**Test regresi.** `test_bug9_subquery_dalam_update_adalah_read`

**Peran AI.** Bug ditemukan Claude saat membandingkan kode dengan SPESIFIKASI.md. Perbaikan, bagian akar masalah, dan draft laporan ini dibuat dengan bantuan Claude. Diverifikasi dengan test regresi yang gagal di kode asli dan lulus setelah perbaikan, serta `python evaluate.py`.

---
