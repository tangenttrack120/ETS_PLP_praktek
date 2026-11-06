**ast_nodes.py (Abstract Syntax Tree Definitions)**

This file defines the Data Transfer Objects (DTOs) using Python's @dataclass to represent a SQL Abstract Syntax Tree (AST), along with tree traversal utilities.

Data Classes (AST Nodes)
Statements
Script: Root container for an entire SQL script, holding a list of parsed statements and any parsing errors.

Select: Represents a SELECT statement, including clauses: distinct, columns, sources (tables/subqueries), joins, where, group_by, order_by, and line number.

Insert: Represents an INSERT statement, specifying the target table, targeted columns, inserted values (rows of expressions), or a source query (INSERT INTO ... SELECT).

Update: Represents an UPDATE statement, containing target table, column assignments, and where clause.

Delete: Represents a DELETE statement, containing target table and where clause.

Statement Parts
SelectItem: Wraps a single expression inside a SELECT clause along with an optional alias.

Star: Marker representing SELECT \*.

TableRef: Represents a direct table reference (e.g., crm.pelanggan) with optional table alias.

DerivedTable: Represents a subquery used as a table source inside a FROM or JOIN clause.

Join: Represents a SQL JOIN clause with its kind ("INNER", "LEFT"), target source, and condition.

Assignment: Pairs a target ColumnRef with its assigned value expression in an UPDATE statement.

OrderItem: Represents an expression in an ORDER BY clause with sort direction ("ASC" or "DESC").

Expressions & Predicates
BinaryOp: Represents binary operations (+, -, =, AND, OR, LIKE, etc.) between left and right expressions.

UnaryOp: Represents unary operations (NOT, -) applied to an operand.

InExpr: Represents IN (...) conditions—either containing explicit static values or a subquery (query).

Between: Represents expr BETWEEN low AND high.

IsNull: Represents IS NULL or IS NOT NULL checks.

Exists: Represents an EXISTS (SELECT ...) predicate.

Subquery: Represents a scalar subquery embedded within an expression.

FunctionCall: Represents standard SQL functions (e.g., COUNT(\*), SUM(val)) with function name and args.

ColumnRef: Represents a column reference (qualifier.name or just name). Includes a resolved attribute populated during semantic analysis to store the fully qualified table name.

Literal: Represents constant values (numbers, strings, NULL).

Param: Represents parameter placeholders (?, :name) for prepared statements.

Utility Functions
iter_nodes(node)
Traverses the AST starting from node in pre-order depth-first search (DFS).

Iterates through Python lists recursively.

Ignores non-dataclass nodes.

Yields the current node, then iterates over all dataclass fields (skipping metadata fields like resolved).

pretty(node, indent=0) -> str
Formats the AST into a human-readable, indented string tree representation used for debugging or predicting tree structures.

**analyzer.py (SQL Statement Analyzer & CRUD Mapper)**

this file analyzes SQL AST statements to map operations to target tables/columns (CRUD operations: Create, Read, Update, Delete).

Primary API Functions
analyze_statement(stmt) -> dict[str, set[str]]
Performs high-level table-level CRUD analysis on a single SQL statement.

Select: Collects all referenced tables and marks them with Read ("R").

Insert: Marks the target table with Create ("C"), and marks any tables referenced in values or subqueries with Read ("R").

Update: Marks the target table with Update ("U"), and marks expression targets/predicates with Update ("U").

Delete: Marks the target table with Delete ("D"), and marks tables in where conditions with Read ("R").

Returns: A dictionary mapping table names to set of CRUD operations, e.g., {"crm.pelanggan": {"R"}, "crm.pesanan": {"C"}}.

column_usage(stmt) -> set[tuple[str, str, str]]
Performs fine-grained column-level analysis. Requires prior resolution (where ColumnRef.resolved has been populated by a resolver module).

Update: Maps assigned target columns to Update ("U"), and scans value/where expressions for Read ("R").

Insert: Maps target columns to Create ("C"), and scans source values/queries for Read ("R").

Other Statements (Select, Delete): Scans all nodes via iter_nodes() for column read operations.

Returns: A set of tuples formatted as (table_name, column_name, operation_type).

Internal Helper Functions
\_collect_select(sel: ast.Select, usage, op: str) -> None
Traverses a Select node (and subqueries inside FROM, JOIN, WHERE, GROUP BY, ORDER BY, or target list) to flag table references with the operation op.

\_collect(expr, usage, op: str) -> None
Traverses complex expressions recursively to discover nested subqueries (e.g., EXISTS, scalar subqueries, IN (SELECT ...)) and extract table usage from them using \_collect_select.

**lexer.py (Lexical Analysis & Tokenization)**

This file converts raw SQL text into a sequential stream of strongly typed tokens.

Data Structures & Definitions
TokenType (Enum): Defines all supported token categories, including KEYWORD, IDENT (identifiers), NUMBER, STRING, PARAM (bind variables like ? or :name), OP (operators), STAR (\*), delimiters (LPAREN, RPAREN, COMMA, DOT, SEMICOLON), and EOF.

KEYWORDS (frozenset): List of reserved SQL keywords in uppercase (e.g., SELECT, FROM, WHERE, JOIN, UPDATE, INSERT, DELETE).

\_SINGLE (dict): Direct lookup table mapping single-character punctuation marks ((, ), ,, ., ;, \*) to their respective TokenType.

Token (@dataclass): Immutable container storing token metadata: type, value (raw substring), line number, and col number.

LexError (Exception): Custom error raised when encountering invalid characters or unclosed literals, capturing the error line and column.

Lexer Class & State Machine
**init**(source): Initializes the scanning pointer pos = 0, trackable position line = 1 and col = 1, and an empty tokens list.

tokenize() -> list[Token]: Main loop that calls \_scan_token() until the input end is reached, then appends a TokenType.EOF token.

Position & Scanning Helpers:

\_at_end(): Checks if pointer reaches source length.

\_peek(offset): Looks ahead at the character at pos + offset without moving the pointer.

\_advance(): Consumes current character and updates line/column counters.

\_match(expected): Consumes character if it matches expected input.

_add(type_, value, line, col): Appends a new Token object to tokens.

Token Scanning Logic
\_scan_token(): Core scanner function that reads the next character and routes to specific handlers:

Whitespace: Ignored ( \t\r\n).

Comments: Skips single-line -- comments until \n. Raises LexError for unsupported /\* block comments.

Operators: Handles single-character (+, -, /, =), multi-character operators (<=, >=, !=), and raises errors for invalid standalone !.

Parameters: Recognizes standard positional parameters (?) and named parameters (:name).

\_string(line, col): Scans single-quoted string literals ('text'). Raises LexError if string remains unclosed at EOF.

\_number(line, col): Scans integer and floating-point numeric literals (e.g., 42, 3.14).

\_word(line, col): Scans alphanumeric identifiers and underscores. Checks against KEYWORDS: matches convert to TokenType.KEYWORD, while non-matches default to TokenType.IDENT.

tokenize(source): High-level wrapper function instantiating Lexer and returning the token list.

**parser.py (Recursive Descent AST Parser)**

This file parses the flat token list generated by the lexer into an Abstract Syntax Tree (AST) defined by ast_nodes.py.

Error Handling & Helper Methods
ParseError (Exception): Custom exception raised when expected tokens are missing or syntactically invalid.

Parser State & Lookahead:

\_peek(offset) / \_advance(): Inspects or consumes tokens.

_check(type_, value) / \_check_kw(\*words): Verifies if current token matches target type/value without advancing.

_match(type_, value) / \_match_kw(\*words): Consumes and returns true if current token matches expectations.

\_expect(...) / \_expect_kw(...) / \_expect_ident(...): Consumes expected token or raises ParseError.

parse_script() -> ast.Script: Parses multiple semicolon-separated statements. Uses \_synchronize() (panic-mode error recovery) to skip tokens after an error until reaching a semicolon.

Statement Parsers
\_statement(): Main routing node for statements (SELECT, INSERT, UPDATE, DELETE).

\_select(): Parses complete SELECT statements including DISTINCT, select expressions (\_select_list), FROM sources (\_table_ref), optional JOIN clauses (\_join), WHERE predicates, GROUP BY lists, and ORDER BY items (\_order_list).

\_select_item(): Handles individual return columns and optional AS column aliases.

\_table_ref() / \_table_name() / \_alias(): Parses standard table references (schema.table), explicit/implicit aliases, and parenthesized derived tables (subqueries).

\_insert(): Parses INSERT INTO table (cols) VALUES (...). (Contains a TODO hook for INSERT INTO ... SELECT).

\_update() / \_assignment(): Parses UPDATE table SET column = expr WHERE ....

\_delete(): Parses DELETE FROM table WHERE ....

Expression Parsing (Operator Precedence Hierarchy)
Expressions are parsed from lowest precedence to highest precedence:

\_logical(): Handles binary OR and AND operations (left-associative).

\_not(): Handles unary NOT prefix operations.

\_comparison(): Handles relational operators (=, <>, !=, <, <=, >, >=), IN, LIKE, BETWEEN, and IS [NOT] NULL.

\_in_rest(): Differentiates between static IN (val1, val2) lists and subquery IN (SELECT ...).

\_additive(): Handles binary + and -.

\_multiplicative(): Handles binary \* and /.

\_unary(): Handles unary numerical negation (-).

\_primary(): Parses atomic values: literals (numbers, strings, NULL), parameters, subqueries (EXISTS, scalar (SELECT ...)), grouped sub-expressions (expr), function calls, or column references.

\_function_call() / \_column_ref(): Parses function calls (e.g., COUNT(\*), SUM(val)) and column references (table.column or column).

parse_sql(source): Convenience function chaining tokenize() and Parser.parse_script().

**resolver.py (Symbol Resolution & Scope Analysis Pass)**

This file executes a post-parsing semantic pass over the AST. It builds scope trees to map table qualifiers (e.g., p in p.name) to actual underlying database tables and populates the ColumnRef.resolved field.

Scope Management Structures
Diagnostic (@dataclass): Tracks semantic warnings and errors along with line numbers.

ScopeEntry (@dataclass): Stores an alias or table name in scope and maps it to its target table string (or <subquery alias>).

Scope: Implements a tree node for nested lexical environments with a pointer to its parent scope.

Resolver Scope Operations:

\_push() / \_pop(): Manages entering and exiting nested scope blocks.

\_declare(name, table, line): Registers table/alias names in the active scope. Reports duplicate alias definitions as errors.

\_declare_source(source): Registers TableRef or DerivedTable nodes into scope. Issues warnings for subqueries in FROM missing an alias.

\_lookup(name): Traverses the scope hierarchy from child to parent to resolve identifier qualifiers.

Semantic Pass Traversal
resolve_script() / resolve_statement(): Dispatches AST statements (Select, Insert, Update, Delete) through scope resolution routines.

\_select():

Resolves subqueries inside FROM/JOIN first (preventing subqueries from referencing peer FROM sources).

Pushes a new scope level and declares source tables.

Resolves column references across SELECT targets, JOIN conditions, WHERE, GROUP BY, and ORDER BY.

\_insert() / \_update() / \_delete(): Pushes necessary scopes, registers target tables, and traverses assignment values and WHERE predicates.

\_expr(): Recursively traverses AST expression nodes (BinaryOp, InExpr, Between, FunctionCall, etc.) down to leaf ColumnRef nodes.

\_column(col): Resolves ColumnRef nodes:

If a qualifier exists (e.g., p.name), looks up p in scope chain and assigns col.resolved = target_table.

(Contains a TODO for handling unqualified column references according to spec rules).
