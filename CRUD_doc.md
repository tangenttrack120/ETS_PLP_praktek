# SQL Engine Architecture & CRUD Documentation

This document provides a comprehensive structural and functional overview of the SQL parser, AST representations, lexical scanner, semantic resolver, and CRUD analysis engine.

## 1. Abstract Syntax Tree — `ast_nodes.py`

The `ast_nodes.py` module defines the **Data Transfer Objects (DTOs)** using Python `@dataclass` decorators to represent the SQL Abstract Syntax Tree (AST), alongside utility functions for tree traversal and formatting.

### Data Classes (AST Nodes)

#### Statements

- **`Script`**: The root container for an entire SQL script, maintaining a list of parsed `statements` and associated `errors`.

- **`Select`**: Represents a `SELECT` statement, encapsulating clauses: `distinct`, `columns`, `sources` (tables/subqueries), `joins`, `where`, `group_by`, `order_by`, and `line`.

- **`Insert`**: Represents an `INSERT` statement, specifying the target `table`, targeted `columns`, inserted `values` (rows of expressions), or a source `query` (`INSERT INTO ... SELECT`).

- **`Update`**: Represents an `UPDATE` statement, containing the target `table`, column `assignments`, and optional `where` clause.

- **`Delete`**: Represents a `DELETE` statement, containing the target `table` and optional `where` clause.

#### Statement Components

- **`SelectItem`**: Wraps a single expression inside a `SELECT` clause along with an optional `alias`.

- **`Star`**: Marker representing all columns (`SELECT *`).

- **`TableRef`**: Direct table reference (e.g., `crm.pelanggan`) with an optional table `alias`.

- **`DerivedTable`**: Represents a subquery used as a table source inside a `FROM` or `JOIN` clause.

- **`Join`**: Represents a SQL `JOIN` clause with its `kind` (`"INNER"`, `"LEFT"`), target `source`, and `condition`.

- **`Assignment`**: Pairs a target `ColumnRef` with its assigned value expression in an `UPDATE` statement.

- **`OrderItem`**: Represents an expression in an `ORDER BY` clause with a sort direction (`"ASC"` or `"DESC"`).

#### Expressions & Predicates

- **`BinaryOp`**: Represents binary operations (`+`, `-`, `=`, `AND`, `OR`, `LIKE`, etc.) between `left` and `right` expressions.

- **`UnaryOp`**: Represents unary operations (`NOT`, `-`) applied to an `operand`.

- **`InExpr`**: Represents `IN (...)` conditions—containing either explicit static `values` or a subquery (`query`).

- **`Between`**: Represents `expr BETWEEN low AND high`.

- **`IsNull`**: Represents `IS NULL` or `IS NOT NULL` evaluation checks.

- **`Exists`**: Represents an `EXISTS (SELECT ...)` predicate.

- **`Subquery`**: Represents a scalar subquery embedded within an expression.

- **`FunctionCall`**: Represents standard SQL function invocations (e.g., `COUNT(*)`, `SUM(val)`) with function `name` and `args`.

- **`ColumnRef`**: Represents a column reference (`qualifier.name` or `name`). Includes a `resolved` attribute populated during semantic analysis to store the fully qualified table name.

- **`Literal`**: Represents literal values (numbers, strings, `NULL`).

- **`Param`**: Represents parameter placeholders (`?`, `:name`) for prepared queries.

### Utility Functions

#### `iter_nodes(node)`

Traverses the AST starting from `node` using pre-order **Depth-First Search (DFS)**:

- Iterates through Python `list` items recursively.

- Bypasses non-dataclass instances.

- Yields the current node, then traverses all dataclass fields (excluding metadata fields like `resolved`).

#### `pretty(node, indent=0) -> str`

Formats the AST into a human-readable, indented string tree representation for debugging and visualization.

## 2. SQL CRUD Analyzer — `analyzer.py`

The `analyzer.py` module evaluates SQL AST nodes to map operations to target tables and columns using standard **CRUD** mapping (**C**reate, **R**ead, **U**pdate, **D**elete).

### Primary API Functions

#### `analyze_statement(stmt) -> dict[str, set[str]]`

Performs high-level, table-level CRUD analysis on a single SQL statement.

| Statement    | Target Table Action                     | Referenced Table Action                                  |
| ------------ | --------------------------------------- | -------------------------------------------------------- |
| **`Select`** | N/A                                     | Marks all source tables with Read (`"R"`)                |
| **`Insert`** | Target table marked with Create (`"C"`) | Value/subquery tables marked with Read (`"R"`)           |
| **`Update`** | Target table marked with Update (`"U"`) | Target expressions/predicates marked with Update (`"U"`) |
| **`Delete`** | Target table marked with Delete (`"D"`) | `WHERE` condition tables marked with Read (`"R"`)        |

- **Returns**: Dictionary mapping table names to sets of operations, e.g., `{"crm.pelanggan": {"R"}, "crm.pesanan": {"C"}}`.

#### `column_usage(stmt) -> set[tuple[str, str, str]]`

Performs fine-grained column-level analysis.

> **Prerequisite:** Requires semantic resolution to have been executed (`ColumnRef.resolved` must be populated).

- **`Update`**: Maps assigned target columns to Update (`"U"`), and scans value/where expressions for Read (`"R"`).

- **`Insert`**: Maps target columns to Create (`"C"`), and scans source values/queries for Read (`"R"`).

- **`Select` / `Delete`**: Scans all nodes via `iter_nodes()` for column Read (`"R"`) operations.

- **Returns**: A set of tuples formatted as `(table_name, column_name, operation_type)`.

### Internal Helper Functions

- **`_collect_select(sel: ast.Select, usage, op: str) -> None`**
  Traverses a `Select` node (and nested subqueries within `FROM`, `JOIN`, `WHERE`, `GROUP BY`, `ORDER BY`, or target lists) to tag table references with operation `op`.

- **`_collect(expr, usage, op: str) -> None`**
  Recursively traverses complex expressions to discover subqueries (`EXISTS`, scalar subqueries, `IN (SELECT ...)`) and extract table operations via `_collect_select`.

## 3. Lexical Analysis — `lexer.py`

The `lexer.py` module converts raw SQL source text into a sequential stream of strongly-typed tokens.

### Data Structures & Definitions

- **`TokenType` (`Enum`)**: Defines token categories:
  `KEYWORD`, `IDENT`, `NUMBER`, `STRING`, `PARAM`, `OP`, `STAR`, `LPAREN`, `RPAREN`, `COMMA`, `DOT`, `SEMICOLON`, `EOF`.

- **`KEYWORDS` (`frozenset`)**: Immutably stores standard reserved SQL keywords in uppercase (e.g., `SELECT`, `FROM`, `WHERE`, `JOIN`, `UPDATE`, `INSERT`, `DELETE`).

- **`_SINGLE` (`dict`)**: Constant map translating single-character punctuation (`(`, `)`, `,`, `.`, `;`, `*`) directly to `TokenType`.

- **`Token` (`@dataclass`)**: Immutable container storing token details: `type`, `value`, `line`, and `col`.

- **`LexError` (`Exception`)**: Custom exception raised for unexpected characters or unclosed literal strings.

### Lexer State Machine

- **`__init__(source)`**: Initializes tracking pointers (`pos = 0`, `line = 1`, `col = 1`) and an empty `tokens` buffer.

- **`tokenize() -> list[Token]`**: Executes the primary scan loop until input termination, appending a final `TokenType.EOF` token.

#### Position & Scanning Helpers

- `_at_end()`: Checks if the scanner pointer has reached input end.

- `_peek(offset)`: Inspects ahead by `offset` characters without advancing position.

- `_advance()`: Consumes the current character and updates line/column coordinates.

- `_match(expected)`: Consumes the next character conditionally if it matches `expected`.

- `_add(type_, value, line, col)`: Instantiates and appends a `Token` to the internal buffer.

### Scanning Handlers

```
Input Character
├── Whitespace         ──> Ignore (\t, \r, \n)
├── Single-line '--'   ──> Skip until newline
├── Single char        ──> Map directly via _SINGLE
├── Operators          ──> Evaluate single/multi-char (+, -, <=, >=, !=)
├── String (')         ──> _string() handler
├── Numbers (0-9)      ──> _number() handler
└── Alphanumeric       ──> _word() handler ──> KEYWORD or IDENT

```

- **`_scan_token()`**: Main character dispatcher for the scanner.

- **`_string(line, col)`**: Consumes single-quoted literals. Raises `LexError` if unclosed.

- **`_number(line, col)`**: Consumes integer and decimal floating-point literals.

- **`_word(line, col)`**: Consumes alphanumeric words; checks against `KEYWORDS` to emit `KEYWORD` or `IDENT`.

- **`tokenize(source)`**: High-level wrapper function instantiating `Lexer` and processing token sequence.

## 4. Recursive Descent Parser — `parser.py`

The `parser.py` module converts flat token streams into structured AST instances matching `ast_nodes.py`.

### Error Handling & Utilities

- **`ParseError` (`Exception`)**: Raised when expected tokens are absent or syntactically invalid.

- **Parser State Controls**:
  - `_peek()` / `_advance()`: Inspects or consumes current tokens.

  - `_check()` / `_check_kw()`: Validates token type/keyword presence without consuming.

  - `_match()` / `_match_kw()`: Consumes token if expected matches.

  - `_expect()` / `_expect_kw()` / `_expect_ident()`: Enforces token match or raises `ParseError`.

- **`parse_script() -> ast.Script`**: Parses semicolon-separated statements using panic-mode recovery (`_synchronize()`).

### Statement Parsers

```
                ┌──> _select() ──> ast.Select
                ├──> _insert() ──> ast.Insert
_statement() ───┼──> _update() ──> ast.Update
                └──> _delete() ──> ast.Delete

```

- **`_statement()`**: Primary route dispatcher for top-level SQL statements.

- **`_select()`**: Parses full `SELECT` statements (`DISTINCT`, `_select_list`, `FROM`, `_join`, `WHERE`, `GROUP BY`, `_order_list`).

- **`_select_item()`**: Handles individual projection expressions and `AS` aliases.

- **`_table_ref()` / `_table_name()` / `_alias()`**: Parses schema-qualified names (`schema.table`), aliases, and nested derived tables.

- **`_insert()`**: Parses `INSERT INTO table (columns) VALUES (...)`.

- **`_update()` / `_assignment()`**: Parses `UPDATE table SET column = expr WHERE ...`.

- **`_delete()`**: Parses `DELETE FROM table WHERE ...`.

### Expression Parsing (Precedence Hierarchy)

Expressions are parsed top-down from lowest operator precedence to highest:

```
Low Precedence   │  1. _logical()        ──> OR, AND
                 │  2. _not()            ──> NOT
                 │  3. _comparison()     ──> =, <>, !=, <, <=, >, >=, IN, LIKE, BETWEEN, IS NULL
                 │  4. _additive()       ──> +, -
                 │  5. _multiplicative() ──> *, /
                 │  6. _unary()          ──> - (numerical negation)
High Precedence  ▼  7. _primary()        ──> Literals, Params, Subqueries, ColumnRef, Functions

```

- **`_function_call()` / `_column_ref()`**: Parses function signatures (`COUNT(*)`, `SUM(...)`) and column identifiers (`table.column` or `column`).

- **`parse_sql(source)`**: High-level routine chaining `tokenize()` and `parse_script()`.

## 5. Semantic Resolver — `resolver.py`

The `resolver.py` module performs a post-parsing semantic validation pass over the AST to build scoped symbol tables and bind qualified column names to concrete database entities.

### Scope Management & Structures

- **`Diagnostic` (`@dataclass`)**: Tracks warning and error diagnostics alongside source line numbers.

- **`ScopeEntry` (`@dataclass`)**: Maps identifier aliases or table names within a scope to fully-qualified target tables.

- **`Scope`**: Hierarchical scope tree node referencing its `parent` scope.

- **`Resolver` Engine Methods**:
  - `_push()` / `_pop()`: Manages entry and exit for lexical scope blocks.

  - `_declare(name, table, line)`: Binds identifiers in active scope; catches duplicate alias declarations.

  - `_declare_source(source)`: Binds `TableRef` or `DerivedTable` nodes into scope; warns on un-aliased subqueries in `FROM`.

  - `_lookup(name)`: Traverses up the scope tree chain to locate resolved qualifiers.

### Semantic Pass Execution

```
resolve_script()
       │
       ▼
resolve_statement()
 ├── _select()  ──> Scope Push ──> Register Sources ──> Resolve Columns/Exprs ──> Scope Pop
 ├── _insert()  ──> Resolve Values & Subqueries
 ├── _update()  ──> Scope Push ──> Register Target ──> Resolve Assignments ──> Scope Pop
 └── _delete()  ──> Scope Push ──> Register Target ──> Resolve Predicates   ──> Scope Pop

```

- **`_select()`**: Evaluates subqueries in `FROM`/`JOIN` first, creates a local scope, registers source table aliases, and resolves expressions across `SELECT`, `JOIN`, `WHERE`, `GROUP BY`, and `ORDER BY` clauses.

- **`_insert()` / `_update()` / `_delete()`**: Manages appropriate scope frames for target tables and evaluates child expressions.

- **`_expr()`**: Recursively traverses expression structures down to leaf nodes.

- **`_column(col)`**: Resolves `ColumnRef` instances. If a qualifier exists, looks up table mapping and assigns `col.resolved = target_table`.
