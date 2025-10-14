# ----------------------------------------------------------
# LEXICAL ANALYZER (Tokenizer)
# ----------------------------------------------------------
# Converts source code into a list of tokens.
# Keeps line and column info for error reporting.
# Supports:
#   - Keywords: int, return, if, else, while, print
#   - Identifiers, numbers, strings
#   - Arithmetic operators: + - * /
#   - Comparison operators: == != >= <= > <
#   - Assignment: =
#   - Punctuation: ; , ( ) { }
#   - Comments (// ...)
# ----------------------------------------------------------

import re


# ----------------------------------------------------------
# Token Class
# ----------------------------------------------------------
class Token:
    def __init__(self, type_, value, line, col):
        self.type = type_
        self.value = value
        self.line = line
        self.col = col

    def __repr__(self):
        return f"Token('{self.type}', '{self.value}', line={self.line}, col={self.col})"


# ----------------------------------------------------------
# Tokenization Rules
# ----------------------------------------------------------
TOKEN_SPEC = [
    ("COMMENT", r'//[^\n]*'),              #  Skip // comments
    ("STRING",  r'"[^"\n]*"'),             #  String literal
    ("NUMBER",  r'\d+'),
    ("ID",      r'[A-Za-z_]\w*'),
    ("EQ",      r'=='),
    ("NE",      r'!='),
    ("LE",      r'<='),
    ("GE",      r'>='),
    ("ASSIGN",  r'='),
    ("LT",      r'<'),
    ("GT",      r'>'),
    ("PLUS",    r'\+'),
    ("MINUS",   r'-'),
    ("MUL",     r'\*'),
    ("DIV",     r'/'),
    ("LPAREN",  r'\('),
    ("RPAREN",  r'\)'),
    ("LBRACE",  r'\{'),
    ("RBRACE",  r'\}'),
    ("COMMA",   r','),
    ("SEMI",    r';'),
    ("NEWLINE", r'\n'),
    ("SKIP",    r'[ \t]+'),
    ("MISMATCH", r'.'),
]

# Reserved keywords
KEYWORDS = {
    "int": "INT",
    "return": "RETURN",
    "if": "IF",
    "else": "ELSE",
    "while": "WHILE",
    "print": "PRINT",
}


# ----------------------------------------------------------
# Tokenizer
# ----------------------------------------------------------
def tokenize(code):
    tok_regex = "|".join(f"(?P<{name}>{pattern})" for name, pattern in TOKEN_SPEC)
    line_num = 1
    line_start = 0
    tokens = []

    for mo in re.finditer(tok_regex, code):
        kind = mo.lastgroup
        value = mo.group()
        col = mo.start() - line_start + 1

        if kind == "NEWLINE":
            line_start = mo.end()
            line_num += 1
            continue

        elif kind in ("SKIP", "COMMENT"):
            # ✅ Ignore spaces and comments
            continue

        elif kind == "ID" and value in KEYWORDS:
            kind = KEYWORDS[value]

        elif kind == "STRING":
            # ✅ Keep string content with quotes stripped
            value = value.strip('"')

        elif kind == "MISMATCH":
            # ✅ Ignore stray characters like '.' ONLY if in comment
            raise SyntaxError(f"Unexpected character {value!r} at line {line_num}")

        tokens.append(Token(kind, value, line_num, col))

    tokens.append(Token("EOF", "", line_num, 1))
    return tokens
