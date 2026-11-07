# Laporan Akhir

## 1. Hasil evaluasi

Tempel keluaran `python evaluate.py` setelah `data/ground_truth.csv` dilengkapi.

```text
Dievaluasi: audit.sql, campuran_error.sql, laporan_penjualan.sql, pemeliharaan.sql (27 triple)

Metode   Precision  Recall     F1
parser        1.00    1.00   1.00
regex         0.65    0.81   0.72

[regex]
  salah ditemukan (FP): ('audit.sql', 16, 'sesi', 'R')
  salah ditemukan (FP): ('campuran_error.sql', 4, 'pesanan', 'R')
  salah ditemukan (FP): ('campuran_error.sql', 8, 'keranjang', 'R')
  salah ditemukan (FP): ('laporan_penjualan.sql', 2, 'pelanggan', 'D')
  salah ditemukan (FP): ('laporan_penjualan.sql', 2, 'pelanggan', 'R')
  salah ditemukan (FP): ('laporan_penjualan.sql', 2, 'pesanan', 'R')
  salah ditemukan (FP): ('laporan_penjualan.sql', 2, 'rahasia', 'R')
  salah ditemukan (FP): ('laporan_penjualan.sql', 15, 'pesanan', 'R')
  salah ditemukan (FP): ('pemeliharaan.sql', 2, 'crm.alamat', 'R')
  salah ditemukan (FP): ('pemeliharaan.sql', 2, 'crm.pelanggan', 'R')
  salah ditemukan (FP): ('pemeliharaan.sql', 2, 'pelanggan_lama', 'U')
  salah ditemukan (FP): ('pemeliharaan.sql', 15, 'crm.alamat', 'R')
  terlewat (FN):       ('audit.sql', 2, 'pesanan', 'R')
  terlewat (FN):       ('laporan_penjualan.sql', 3, 'pelanggan', 'R')
  terlewat (FN):       ('laporan_penjualan.sql', 3, 'pesanan', 'R')
  terlewat (FN):       ('pemeliharaan.sql', 3, 'crm.alamat', 'R')
  terlewat (FN):       ('pemeliharaan.sql', 3, 'crm.pelanggan', 'R')
```

Sebagai pembanding, parser **sebelum** perbaikan: precision 0.91, recall 0.37, F1 0.53
(banyak statement gagal di-parse karena keyword huruf kecil, `<>`, `''`, komentar blok,
`LEFT OUTER JOIN`, `INSERT ... SELECT`, dan error recovery yang membuang sisa file).

## 2. Tiga kasus di mana regex salah

Untuk tiap kasus: SQL-nya, kesalahan regex, dan mengapa parser benar (kaitkan dengan konsep
lexing, parsing, atau resolusi).

1. **Keyword di dalam komentar.** `laporan_penjualan.sql` baris 2:
   `-- DELETE FROM pelanggan` dan `pemeliharaan.sql` baris 2:
   `Catatan lama: UPDATE pelanggan_lama ...` di dalam `/* ... */`.
   Regex tidak mengenal komentar, jadi menemukan `pelanggan` (D, R) dan `pelanggan_lama` (U)
   yang palsu. Akibat tambahannya, awal statement terdeteksi di baris komentar (baris 2),
   sehingga tabel yang benar pun tercatat di baris yang salah (FN di baris 3).
   Parser benar karena **lexer** (Bab 4) membuang komentar sebelum parsing; komentar tidak
   pernah menjadi token.

2. **Keyword di dalam string literal.** `laporan_penjualan.sql` baris 6:
   `o.catatan <> 'FROM rahasia'`. Regex melihat `FROM rahasia` dan mencatat tabel `rahasia`
   (R). Parser benar karena lexer membaca `'FROM rahasia'` sebagai **satu token `STRING`**
   (lexeme panjang, Bab 4.6). Di parser token itu menjadi `Literal`, bukan `table_ref`.

3. **Struktur statement: daftar tabel dengan koma dan `DELETE FROM`.**
   `audit.sql` baris 3: `FROM pelanggan p, pesanan o`. Regex hanya mengambil nama pertama
   setelah `FROM`, sehingga `pesanan` terlewat (FN). Sebaliknya `DELETE FROM sesi`
   (`audit.sql` baris 16) cocok dengan pola `DELETE FROM` (D) **dan** pola `FROM` (R), sehingga
   muncul R palsu. Parser benar karena mengikuti **grammar** (Bab 5–6):
   `table_ref { "," table_ref }` menerima banyak tabel, dan `FROM` di dalam `delete_stmt`
   adalah bagian dari aturan DELETE, bukan klausa baca.

## 3. Batas pendekatan kami

Minimal tiga hal yang **tidak bisa** ditangani dengan benar oleh tool ini meskipun semua bug
sudah diperbaiki. Untuk tiap batas: contoh SQL atau situasinya, akibatnya pada CRUD matrix,
dan informasi apa yang dibutuhkan untuk mengatasinya.

1. **Tidak ada skema database.**
   `SELECT nama FROM pelanggan p JOIN pesanan o ON o.pelanggan_id = p.id`: kolom `nama`
   dilaporkan ambigu dan `resolved` tetap `None`, sehingga penggunaan kolom (`--kolom`) tidak
   lengkap. Sebaliknya kolom luar yang ditulis tanpa qualifier di dalam subquery salah
   di-resolve ke tabel subquery. CRUD per tabel tetap benar, tetapi CRUD per kolom tidak.
   Dibutuhkan: skema database (daftar kolom per tabel, misalnya dari `information_schema`).

2. **Objek database yang menyembunyikan akses tabel (view, trigger, stored procedure).**
   `SELECT * FROM v_laporan` atau `DELETE FROM pesanan` yang memicu trigger penulis ke
   `log_hapus`: tool mencatat `v_laporan` sebagai tabel R dan tidak tahu ada C ke `log_hapus`.
   CRUD matrix tidak lengkap atau salah sasaran. Dibutuhkan: definisi view, trigger, dan
   procedure dari katalog database.

3. **Sintaks di luar lingkup grammar.**
   `WITH aktif AS (SELECT ...) SELECT ...`, `UNION`, atau `MERGE`: statement gagal di-parse,
   menghasilkan satu error, dan **tidak dihitung**, sehingga semua tabelnya hilang dari matrix
   (FN). Dibutuhkan: perluasan grammar dan resolver (CTE membuat nama baru di scope).

4. **SQL dinamis di kode aplikasi.**
   `"SELECT * FROM " + nama_tabel` di Java/Python: tool hanya membaca file `.sql`, dan nama
   tabelnya baru diketahui saat runtime. Dibutuhkan: analisis kode aplikasi atau log query.

## 4. Pembagian kerja

Siapa mengerjakan apa, dan bagaimana kalian memastikan keduanya memahami seluruh kode.

- **Richard:** membaca dan mendokumentasikan kode (`CRUD_doc.md`, `testUnit_doc.md`),
  menyelesaikan T3 (komentar blok), T1 (`INSERT ... SELECT`), versi awal T2, dan mencatat bug
  `''`, `<>`, `LEFT OUTER JOIN`, serta panic mode di `LAPORAN_BUG.md`.
- **Afzal:** memperbaiki bug lexer (keyword huruf kecil, `<>`, `''`), parser (panic mode,
  presedensi `AND`/`OR`, `LEFT OUTER JOIN`), resolver (urutan lookup scope, pop scope `DELETE`),
  dan analyzer (subquery di `UPDATE`); mengoreksi T2 agar hanya melihat scope terdalam; menulis
  `test_tambahan.py`, ground truth, kartu desain, dan laporan akhir.
- **Memastikan keduanya paham:** setiap perubahan lewat pull request yang direview anggota lain,
  dan sebelum demo kami saling menjelaskan seluruh perbaikan (termasuk bagian yang dikerjakan
  anggota lain) serta saling memberi pertanyaan prediksi output.
