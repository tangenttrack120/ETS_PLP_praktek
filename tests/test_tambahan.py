"""Test tambahan buatan kelompok.

Isi dengan:
1. Satu test regresi untuk setiap bug yang kalian perbaiki (gagal sebelum perbaikan,
   lulus sesudahnya). Beri nama yang menjelaskan bug-nya.
2. Lima test kasus tepi, masing-masing dengan komentar singkat mengapa kasus itu berisiko.
"""
import pytest

from crud import ast_nodes as ast
from crud.analyzer import analyze_statement
from crud.lexer import LexError, TokenType as T, tokenize
from crud.parser import parse_sql
from crud.pipeline import analyze_source
from crud.resolver import Resolver


# ---- helper -------------------------------------------------------------
def one(sql):
    script = parse_sql(sql)
    assert script.errors == [], script.errors
    assert len(script.statements) == 1
    return script.statements[0]


def resolve(sql):
    script = parse_sql(sql)
    assert script.errors == [], script.errors
    return script, Resolver().resolve_script(script)


def cols(node):
    return [n for n in ast.iter_nodes(node) if isinstance(n, ast.ColumnRef)]


# =========================================================================
# 1. TEST REGRESI (satu per bug, lihat docs/LAPORAN_BUG.md)
# =========================================================================

# Bug 1 - lexer: keyword campuran huruf besar/kecil tidak dikenali (SPEK 2.2)
def test_bug1_keyword_huruf_campuran_dinormalisasi():
    toks = tokenize("Select id From t")
    assert (toks[0].type, toks[0].value) == (T.KEYWORD, "SELECT")
    assert (toks[2].type, toks[2].value) == (T.KEYWORD, "FROM")


# Bug 2 - lexer: '<>' dipecah jadi '<' dan '>' (maximal munch, SPEK 2.5)
def test_bug2_operator_tidak_sama_dengan_satu_token():
    toks = [t for t in tokenize("a <> b") if t.type != T.EOF]
    assert [(t.type, t.value) for t in toks] == [
        (T.IDENT, "a"), (T.OP, "<>"), (T.IDENT, "b")]


# Bug 3 - lexer: '' di dalam string tidak dianggap satu kutip (SPEK 2.4)
def test_bug3_kutip_ganda_dalam_string():
    toks = tokenize("'O''Brien'")
    assert toks[0].type == T.STRING and toks[0].value == "O'Brien"
    assert toks[1].type == T.EOF          # satu token STRING saja


# Bug 4 - parser: panic mode membuang token sampai EOF, bukan sampai ';' (SPEK 6)
def test_bug4_error_recovery_lanjut_setelah_titik_koma():
    script = parse_sql("SELECT id nama, FROM t;\nDELETE FROM u;\nSELECT x FROM v;")
    assert len(script.errors) == 1
    assert [type(s).__name__ for s in script.statements] == ["Delete", "Select"]


# Bug 5 - parser: AND dan OR satu tingkat presedensi (SPEK 3.1)
def test_bug5_and_lebih_kuat_dari_or():
    w = one("SELECT id FROM t WHERE a = 1 OR b = 2 AND c = 3").where
    assert w.op == "OR"
    assert isinstance(w.right, ast.BinaryOp) and w.right.op == "AND"


# Bug 6 - parser: LEFT OUTER JOIN ditolak (grammar join, SPEK 3)
def test_bug6_left_outer_join_diterima():
    s = one("SELECT a.id FROM a LEFT OUTER JOIN b ON b.a_id = a.id")
    assert s.joins[0].kind == "LEFT" and s.joins[0].source.name == "b"


# Bug 7 - resolver: lookup dari scope terluar, alias dalam tidak menutupi (SPEK 4.3)
def test_bug7_alias_subquery_menutupi_alias_luar():
    script, diags = resolve(
        "SELECT x.id FROM pelanggan x "
        "WHERE x.id IN (SELECT x.pelanggan_id FROM pesanan x)")
    inner = script.statements[0].where.query.columns[0].expr
    assert inner.resolved == "pesanan"
    assert diags == []


# Bug 8 - resolver: DELETE tidak menutup scope, alias bocor ke statement berikutnya (SPEK 4.5)
def test_bug8_alias_delete_tidak_bocor():
    _, diags = resolve("DELETE FROM sesi s WHERE s.id = 1;\nSELECT s.id FROM pengguna u;")
    errors = [d for d in diags if d.level == "error"]
    assert len(errors) == 1 and "'s'" in errors[0].message and errors[0].line == 2


# Bug 9 - analyzer: tabel di subquery UPDATE ditandai U, seharusnya R (SPEK 5)
def test_bug9_subquery_dalam_update_adalah_read():
    s = one("UPDATE pesanan SET total = (SELECT MAX(h) FROM harga) "
            "WHERE pelanggan_id IN (SELECT id FROM pelanggan)")
    assert analyze_statement(s) == {"pesanan": {"U"}, "harga": {"R"}, "pelanggan": {"R"}}


# ---- TODO --------------------------------------------------------------
# T1 - INSERT ... SELECT
def test_t1_insert_select_crud():
    s = one("INSERT INTO arsip SELECT id FROM pesanan")
    assert s.values == [] and isinstance(s.query, ast.Select)
    assert analyze_statement(s) == {"arsip": {"C"}, "pesanan": {"R"}}


# T2 - kolom tanpa qualifier
def test_t2_kolom_tanpa_qualifier_ambigu():
    script, diags = resolve("SELECT nama FROM pelanggan p, pesanan o")
    assert cols(script)[0].resolved is None
    assert [d.level for d in diags] == ["warning"]
    assert "ambigu" in diags[0].message


def test_t2_kolom_tanpa_qualifier_hanya_scope_terdalam():
    # Kolom di subquery hanya melihat tabel subquery, bukan tabel luar.
    script, diags = resolve(
        "SELECT p.id FROM pelanggan p WHERE p.id IN (SELECT pelanggan_id FROM pesanan)")
    inner = script.statements[0].where.query.columns[0].expr
    assert inner.resolved == "pesanan" and diags == []


def test_t2_kolom_tanpa_tabel_di_scope():
    # INSERT tidak membuat scope (SPEK 4.1), jadi tidak ada tabel sama sekali.
    _, diags = resolve("INSERT INTO t (a) VALUES (b)")
    assert [d.level for d in diags] == ["warning"]


def test_t2_kolom_merujuk_subquery_di_from():
    script, diags = resolve("SELECT nama FROM (SELECT nama FROM pelanggan) AS s")
    outer = script.statements[0].columns[0].expr
    assert outer.resolved == "<subquery s>" and diags == []


# T3 - komentar blok
def test_t3_komentar_blok_tidak_ditutup():
    with pytest.raises(LexError):
        tokenize("SELECT /* lupa ditutup")


# =========================================================================
# 2. KASUS TEPI
# =========================================================================

# Berisiko: lexer yang mencocokkan awalan bisa memotong 'selection' jadi
# keyword SELECT + 'ion'.
def test_tepi_kata_berawalan_keyword_tetap_ident():
    toks = tokenize("selection fromage")
    assert [(t.type, t.value) for t in toks[:2]] == [
        (T.IDENT, "selection"), (T.IDENT, "fromage")]


# Berisiko: '*' di dalam komentar dan '**/' bisa membuat lexer salah
# mendeteksi penutup atau berhenti terlalu cepat.
def test_tepi_komentar_blok_berisi_bintang():
    toks = tokenize("/* a * b ** c **/ SELECT")
    assert toks[0].value == "SELECT" and toks[1].type == T.EOF


# Berisiko: AND milik BETWEEN tidak boleh "dicuri" oleh _and (SPEK 3.2).
def test_tepi_between_diikuti_and():
    w = one("SELECT id FROM t WHERE a BETWEEN 1 AND 2 AND b = 3").where
    assert w.op == "AND" and isinstance(w.left, ast.Between)


# Berisiko: setelah lookup dibalik ke terdalam-dulu, subquery harus TETAP
# bisa melihat alias luar (correlated subquery).
def test_tepi_correlated_subquery_melihat_alias_luar():
    script, diags = resolve(
        "SELECT p.nama FROM pelanggan p "
        "WHERE EXISTS (SELECT 1 FROM pembayaran b WHERE b.pelanggan_id = p.id)")
    resolved = {(c.qualifier, c.name): c.resolved for c in cols(script)}
    assert resolved[("p", "id")] == "pelanggan"
    assert resolved[("b", "pelanggan_id")] == "pembayaran"
    assert diags == []


# Berisiko: kata FROM di dalam string atau komentar tidak boleh jadi tabel
# (di sinilah regex baseline salah).
def test_tepi_keyword_di_string_dan_komentar_bukan_tabel():
    res = analyze_source("-- DELETE FROM pelanggan\n"
                         "SELECT id FROM pesanan WHERE catatan <> 'FROM rahasia';")
    assert res.parse_errors == [] and res.matrix() == {"pesanan": "R"}