"""Lexical analyzer for AquaLight.

Input : a file with the list of tokens + a source program
Output: Program Internal Form (PIF), Symbol Table (ST), lexical errors
"""
import argparse
import re
from pathlib import Path

from  sym_tab import SymbolTable

ID_TOKEN = "id"
CONST_TOKEN = "const"


def load_tokens(path):
    """Reads the token list: one token per line, '#' starts a comment line."""
    tokens = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            tokens.append(line)
    return tokens


def build_regex(tokens):
    """Builds one regular expression with a named group for each lexical class.

    The order of the groups matters (the first one that matches wins):
    bad identifiers before reserved words before identifiers before constants.
    """
    words = sorted((t for t in tokens if t.isalpha()), key=len, reverse=True)
    symbols = sorted((t for t in tokens if not t.isalpha()), key=len, reverse=True)
    spec = [
        ("WS", r"[ \t\r]+"),
        ("NEWLINE", r"\n"),
        ("BAD_ID", r"[0-9]+[A-Za-z_][A-Za-z0-9_]*"),
        ("KEYWORD", r"(?:" + "|".join(map(re.escape, words)) + r")(?![A-Za-z0-9_])"),
        ("ID", r"[A-Za-z][A-Za-z0-9_]*"),
        ("CONST", r"[0-9]+"),
        ("SYMBOL", "|".join(map(re.escape, symbols))),
        ("ERROR", r"."),
    ]
    return re.compile("|".join(f"(?P<{name}>{pattern})" for name, pattern in spec))


def analyze(source, tokens, symbol_table):
    """Returns (pif, errors). pif is a list of (token, st_position or None)."""
    regex = build_regex(tokens)
    pif, errors = [], []
    line, line_start = 1, 0
    for match in regex.finditer(source):
        kind, text = match.lastgroup, match.group()
        column = match.start() - line_start + 1
        if kind == "WS":
            continue
        if kind == "NEWLINE":
            line += 1
            line_start = match.end()
        elif kind in ("KEYWORD", "SYMBOL"):
            pif.append((text, None))
        elif kind == "ID":
            pif.append((ID_TOKEN, symbol_table.insert(text)))
        elif kind == "CONST":
            pif.append((CONST_TOKEN, symbol_table.insert(text)))
        elif kind == "BAD_ID":
            errors.append(f"Lexical error at line {line}, column {column}: "
                          f"invalid identifier '{text}' (an identifier must start with a letter)")
        else:
            errors.append(f"Lexical error at line {line}, column {column}: "
                          f"unexpected character '{text}'")
    return pif, errors


def format_pif(pif):
    lines = [f"{'TOKEN':<12}ST POSITION (bucket, index)"]
    for token, position in pif:
        shown = "-" if position is None else f"({position[0]}, {position[1]})"
        lines.append(f"{token:<12}{shown}")
    return "\n".join(lines)


def format_st(symbol_table):
    lines = [f"Hash table, {symbol_table.num_buckets} buckets, {len(symbol_table)} entries",
             f"{'BUCKET':<8}{'INDEX':<8}SYMBOL"]
    for bucket, index, key in symbol_table.items():
        lines.append(f"{bucket:<8}{index:<8}{key}")
    return "\n".join(lines)


def format_errors(errors):
    return "\n".join(errors) if errors else "No lexical errors."


def main():
    parser = argparse.ArgumentParser(description="AquaLight lexical analyzer")
    parser.add_argument("source", help="source program (e.g. program1.aq)")
    parser.add_argument("-t", "--tokens", default=str(Path(__file__).with_name("tokens.txt")),
                        help="file with the list of tokens")
    parser.add_argument("-o", "--out", default="output", help="output directory")
    parser.add_argument("-b", "--buckets", type=int, default=31, help="number of hash table buckets")
    args = parser.parse_args()

    source = Path(args.source).read_text(encoding="utf-8")
    tokens = load_tokens(args.tokens)

    with SymbolTable(args.buckets) as symbol_table:
        pif, errors = analyze(source, tokens, symbol_table)
        results = {
            "PIF": format_pif(pif),
            "ST": format_st(symbol_table),
            "errors": format_errors(errors),
        }

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(args.source).stem
    for name, text in results.items():
        (out_dir / f"{stem}_{name}.out").write_text(text + "\n", encoding="utf-8")
        print(f"===== {name} =====\n{text}\n")
    print(f"Output files written to {out_dir}/")


if __name__ == "__main__":
    main()
