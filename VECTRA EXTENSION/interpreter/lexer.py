"""Analisador léxico do VECTRA."""

ALPHABET = {
    "|": "A", "—": "B", "$": "C", "/": "D", "\\": "E",
    "○": "F", "△": "G", "□": "H", "×": "I", "~": "J",
    "<": "K", ">": "L", "∩": "M", "∪": "N", "◇": "O",
    "*": "P", "[": "Q", "#": "R", "@": "S", "%": "T",
    "!": "U", "?": "V", "^": "W", "&": "X", "-": "Y", "_": "Z",
}
REVERSE_ALPHABET = {v: k for k, v in ALPHABET.items()}

def tokenize(code):
    """Produz tokens individuais, mantendo linha e coluna para diagnósticos."""
    tokens = []
    line = column = 1
    for char in code:
        if char not in " \t\r\n":
            tokens.append({
                "type": "CHAR",
                "value": char,
                "line": line,
                "column": column,
            })
        if char == "\n":
            line += 1
            column = 1
        else:
            column += 1
    return tokens
