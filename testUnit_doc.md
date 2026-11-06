# SQL Engine Unit Test Suite Documentation

This document provides detailed coverage analysis, input parameters, tested conditions, and expected outcomes across all unit test suites in the SQL analysis engine.

---

## Suite Overview

| Test Module | Primary Focus | Test Count | Key Features Covered |
| :--- | :--- | :---: | :--- |
| **`test_analyzer.py`** | CRUD Matrix & Statement Analysis | 5 | Table-level CRUD, multi-statement file matrix aggregation |
| **`test_lexer.py`** | Scanner & Tokenizer | 9 | Token types, case normalization, position tracking, comments, errors |
| **`test_parser.py`** | Recursive Descent AST Parser | 12 | Statement nodes, expression precedence, subqueries, error tracking |
| **`test_resolver.py`** | Scope & Symbol Resolution | 4 | Qualifier binding, scope inheritance, diagnostic error generation |

---

## 1. CRUD Analyzer Suite — `test_analyzer.py`

This suite validates table-level and file-level **CRUD** (**C**reate, **R**ead, **U**pdate, **D**elete) operation extraction.

### Test Specifications

#### `test_crud_select_join`
* **Target Query**: `SELECT p.id FROM pelanggan p JOIN pesanan o ON o.pelanggan_id = p.id`
* **Condition Tested**: Multi-table `JOIN` expression parsing and table collection.
* **Expected Result**: 
  ```python
  {"pelanggan": {"R"}, "pesanan": {"R"}}
  ```

#### `test_crud_insert_values`
* **Target Query**: `INSERT INTO log (id) VALUES (1)`
* **Condition Tested**: Single-row `INSERT` statement targeted at a standalone log table.
* **Expected Result**: 
  ```python
  {"log": {"C"}}
  ```

#### `test_crud_update_sederhana`
* **Target Query**: `UPDATE produk SET stok = stok - 1 WHERE id = 3`
* **Condition Tested**: `UPDATE` statement containing relative field decrement and primary key filtering.
* **Expected Result**: 
  ```python
  {"produk": {"U"}}
  ```

#### `test_crud_delete`
* **Target Query**: `DELETE FROM sesi WHERE dibuat < :batas`
* **Condition Tested**: Parameterized `DELETE` query with named parameter (`:batas`).
* **Expected Result**: 
  ```python
  {"sesi": {"D"}}
  ```

#### `test_matrix_laporan_penjualan`
* **Target Source**: File execution on `data/sample/laporan_penjualan.sql`
* **Condition Tested**: End-to-end multi-statement script processing, error-free lexing/parsing, and script-level CRUD matrix aggregation.
* **Expected Result**: 
  ```python
  # Lex Errors: None | Parse Errors: []
  matrix == {"arsip_pesanan": "C", "pelanggan": "RU", "pesanan": "RD"}
  ```

---

## 2. Lexical Scanner Suite — `test_lexer.py`

This suite ensures precise character scanning, whitespace/comment handling, and correct line/column coordinate tracking.

```
Source SQL Text ──► Lexer Engine ──► [ Token Stream ] ──► Assert (Type, Value, Line:Col)
```

### Test Specifications

| Test Case | Source Input | Assertion / Verified Condition |
| :--- | :--- | :--- |
| **`test_token_dasar`** | `SELECT id FROM t;` | Sequence matches: `[KEYWORD, IDENT, KEYWORD, IDENT, SEMICOLON, EOF]` |
| **`test_keyword_huruf_kecil`** | `select id from t` | Case-insensitivity verification: `select` ➔ `TokenType.KEYWORD("SELECT")` |
| **`test_operator_multi_karakter`** | `a <= 1 >= 2 != 3` | Multi-char operators extracted: `["<=", ">=", "!="]` |
| **`test_parameter`** | `? :id :batas_awal` | Captures positional (`?`) and named (`:id`, `:batas_awal`) bind parameters |
| **`test_komentar_baris`** | `-- hapus data lama\nSELECT` | Bypasses single-line comments; records `SELECT` at `line=2` |
| **`test_komentar_blok`** | `/* komentar\n dua baris */ SELECT` | Bypasses block comments; correctly tags `SELECT` at `line=2` |
| **`test_string_biasa`** | `'LUNAS'` | Emits `TokenType.STRING` with value `"LUNAS"` |
| **`test_posisi_token`** | `SELECT a\n FROM t` | Validates precise coordinate mapping: `FROM` token line/col `(2, 3)` |
| **`test_karakter_tidak_dikenal`** | `SELECT\n$` | Raises `LexError` specifying exact illegal character location (`line 2`) |

---

## 3. Recursive Descent Parser Suite — `test_parser.py`

This suite validates AST node instantiation (`ast_nodes.py`), operator precedence evaluation, and error recovery.

### Grammar & Clause Verifications

#### `test_select_sederhana`
* **SQL**: `SELECT id, nama FROM pelanggan;`
* **Asserts**: Node is `ast.Select`; targets columns `["id", "nama"]`; source name `"pelanggan"`.

#### `test_alias_dengan_dan_tanpa_as`
* **SQL**: `SELECT p.id FROM pelanggan AS p, pesanan o`
* **Asserts**: Evaluates explicit (`AS p`) and implicit (`o`) table aliases: `[("pelanggan", "p"), ("pesanan", "o")]`.

#### `test_nama_tabel_berskema`
* **SQL**: `SELECT id FROM CRM.Pelanggan`
* **Asserts**: Normalizes schema-qualified identifiers into lowercase target `"crm.pelanggan"`.

#### `test_left_join`
* **SQL**: `SELECT a.id FROM a LEFT JOIN b ON b.a_id = a.id`
* **Asserts**: Constructs `ast.Join` node with `kind="LEFT"` and target table `"b"`.

#### `test_where_and`
* **SQL**: `SELECT id FROM t WHERE a = 1 AND b = 2`
* **Asserts**: Parses logical expressions into `ast.BinaryOp(op="AND")`.

#### `test_star_dan_perkalian`
* **SQL 1**: `SELECT * FROM t` ➔ First column is `ast.Star` instance.
* **SQL 2**: `SELECT harga * qty FROM t` ➔ Column expression is `ast.BinaryOp(op="*")`.

#### `test_insert_values`
* **SQL**: `INSERT INTO log (id, pesan) VALUES (1, 'ok'), (2, 'gagal')`
* **Asserts**: Produces `ast.Insert` node with targeted columns `["id", "pesan"]` and 2 row value arrays.

#### `test_insert_select`
* **SQL**: `INSERT INTO arsip (id) SELECT id FROM pesanan WHERE total > 10`
* **Asserts**: Produces `ast.Insert` node with nested `ast.Select` subquery targeting `"pesanan"`.

#### `test_update`
* **SQL**: `UPDATE pelanggan SET nama = 'x', level = 2 WHERE id = :id`
* **Asserts**: Instantiates `ast.Update` containing `Assignment` nodes for columns `["nama", "level"]`.

#### `test_delete`
* **SQL**: `DELETE FROM sesi s WHERE s.id = ?`
* **Asserts**: Instantiates `ast.Delete` node correctly preserving table alias `"s"`.

#### `test_subquery_in`
* **SQL**: `SELECT id FROM a WHERE id IN (SELECT a_id FROM b)`
* **Asserts**: `WHERE` expression is `ast.InExpr` holding a nested `ast.Select` node for table `"b"`.

#### `test_pesan_error_berisi_baris`
* **SQL**: `SELECT id\nFROM\n;`
* **Asserts**: Traps syntax failure cleanly; appends 1 `ParseError` object pinpointing line 3.

---

## 4. Semantic Resolver Suite — `test_resolver.py`

This suite verifies scope creation, qualifier link resolution (`ColumnRef.resolved`), and diagnostics reporting.

```
Parse Script ──► Resolver Pass ──► Build Scopes ──► Resolve Column Identifiers ──► Emit Diagnostics
```

### Scope & Diagnostics Specifications

| Test Case | Input SQL | Expected Resolution & Diagnostics |
| :--- | :--- | :--- |
| **`test_alias_qualified_teresolusi`** | `SELECT p.nama FROM pelanggan p JOIN pesanan o ON o.pelanggan_id = p.id` | • `p.nama` ➔ `"pelanggan"`<br>• `o.pelanggan_id` ➔ `"pesanan"`<br>• `diagnostics == []` |
| **`test_alias_tidak_terdefinisi`** | `SELECT q.nama FROM pelanggan p` | • Diagnostics level: `["error"]`<br>• Error message includes `'q'` |
| **`test_kolom_tanpa_qualifier_satu_tabel`** | `SELECT nama FROM pelanggan WHERE aktif = 1` | • All column references infer single scope target `"pelanggan"`<br>• `diagnostics == []` |
| **`test_subquery_in_alias_dalam`** | `SELECT p.id FROM pelanggan p WHERE p.id IN (SELECT o.pelanggan_id FROM pesanan o)` | • Inner subquery qualifier `o.pelanggan_id` resolves to `"pesanan"`<br>• Outer scope remains isolated<br>• `diagnostics == []` |

---

## Summary of Asserted Engine Properties

> [!NOTE]
> 1. **Case Normalization**: Keywords, table identifiers, and column names are systematically converted to standard uppercase or lowercase forms across lexing, parsing, and resolving.
> 2. **Error Resilience**: Invalid characters yield detailed location metadata (`LexError`), while syntax anomalies trigger panic-mode synchronization without terminating process execution (`ParseError`).
> 3. **Scope Integrity**: Nested lexical environments ensure inner subquery aliases operate in isolated scopes without leaking into parent SELECT scopes.