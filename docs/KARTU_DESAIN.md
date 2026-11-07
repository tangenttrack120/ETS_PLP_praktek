# Kartu Desain

Tuliskan lima keputusan desain penting dalam pekerjaan kalian. Untuk tiap keputusan, sebutkan
alternatif yang ditolak dan alasannya. Contoh topik (boleh memilih yang lain):

- bagaimana parser membedakan `*` sebagai "semua kolom" dan sebagai perkalian;
- di mana dan bagaimana presedensi `AND`/`OR` dinyatakan;
- mengapa error recovery berhenti di `;`, bukan di keyword `SELECT` berikutnya;
- urutan pencarian scope dan akibatnya pada shadowing serta correlated subquery;
- mengapa kolom tanpa qualifier hanya dilihat di scope terdalam, dan apa kelemahannya;
- bagaimana implementasi `INSERT ... SELECT` atau komentar blok kalian.

| No | Keputusan | Alternatif yang ditolak | Alasan |
| --- | --- | --- | --- |
| 1 | Presedensi `AND`/`OR` dinyatakan lewat struktur fungsi: `_or` memanggil `_and`, `_and` memanggil `_not`. Operator yang lebih kuat ada di fungsi yang lebih "dalam" (Bab 6.2). | Satu fungsi `_logical` untuk `AND` dan `OR` (kode lama), atau tabel presedensi (precedence climbing / Pratt parser). | Satu fungsi membuat `AND` dan `OR` sama kuat (Bug 5). Tabel presedensi benar, tetapi tidak lagi berpadanan satu-satu dengan aturan grammar `or_expr`/`and_expr`, sehingga sulit dicocokkan dengan spesifikasi. |
| 2 | Error recovery (panic mode) membuang token sampai dan termasuk `;` berikutnya (Bab 6.3.3). | Sinkronisasi di keyword awal statement (`SELECT`, `INSERT`, `UPDATE`, `DELETE`) seperti di buku. | Di SQL, `SELECT` juga muncul di dalam subquery dan `INSERT ... SELECT`. Jika berhenti di `SELECT`, parser bisa lanjut di tengah statement yang rusak dan menghasilkan error beruntun, padahal spesifikasi 6 meminta tepat satu error per statement rusak. `;` adalah batas statement yang pasti. |
| 3 | Qualifier dicari dari scope terdalam ke luar melalui rantai `parent` (Bab 11.3, seperti `resolveLocal`). | Mencari dari scope terluar ke dalam (kode lama), atau menggabungkan semua scope menjadi satu dict. | Terluar-dulu merusak shadowing (Bug 7). Satu dict menghilangkan struktur bersarang dan membuat alias statement lama terlihat. Terdalam-dulu sekaligus memberi shadowing (alias dalam menang) dan tetap mendukung correlated subquery (alias luar tetap ditemukan jika tidak ada di dalam). |
| 4 | Kolom tanpa qualifier hanya dicocokkan dengan scope terdalam: satu tabel di-resolve, lebih dari satu memberi warning ambigu, nol memberi warning (T2). | Naik ke scope induk seperti kolom ber-qualifier. | Tanpa skema database kita tidak tahu tabel mana yang punya kolom itu. Kolom tanpa qualifier di subquery hampir selalu milik tabel subquery itu sendiri. Kalau naik ke luar, hampir semua kolom di correlated subquery jadi ambigu. Kelemahannya: kolom luar yang ditulis tanpa qualifier di dalam subquery akan salah di-resolve ke tabel dalam. |
| 5 | Komentar blok ditangani di lexer: setelah `/*`, maju dengan `_advance` sampai bertemu `*` yang diikuti `/` (lookahead dua karakter), dan `LexError` jika input habis (T3). | Menghapus komentar dengan regex sebelum lexing. | Regex pra-proses akan ikut menghapus `/*` di dalam string dan membuat baris/kolom token bergeser. Di lexer, `_advance` tetap menghitung baris, jadi posisi token sesudah komentar tetap benar. Lookahead dua karakter perlu agar `*` biasa di dalam komentar tidak dianggap penutup. |

Keputusan tambahan (cadangan untuk demo): `*` dibedakan oleh **parser**, bukan lexer. Lexer
selalu mengeluarkan `STAR`; `_select_list` mengartikannya "semua kolom" jika berada di awal
daftar, sedangkan `_multiplicative` mengartikannya perkalian. Lexer tidak tahu konteks
(posisi dalam grammar), jadi keputusan ini harus diambil parser.
