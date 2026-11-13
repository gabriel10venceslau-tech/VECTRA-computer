"""Parser do VECTRA: separa sequências e valida a sintaxe matemática."""

from lexer import ALPHABET

class VectraSyntaxError(SyntaxError):
    def __init__(self, message, line=1, column=1):
        self.line = line
        self.column = column
        super().__init__(f"Erro de sintaxe na linha {line}, coluna {column}: {message}")

def _error(message, item=None):
    item = item or {"line": 1, "column": 1}
    raise VectraSyntaxError(message, item["line"], item["column"])

def parse(tokens):
    # Converte o fluxo de caracteres em texto, sem perder posições.
    chars = tokens
    sequences, current = [], []
    for item in chars:
        if item["value"] == ";":
            if not current:
                _error("sequência vazia antes de ';'.", item)
            sequences.append(current)
            current = []
        else:
            current.append(item)
    if current:
        _error("toda sequência precisa terminar com ';'.", current[-1])
    return sequences
