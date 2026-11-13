"""Execução das operações e decodificação do alfabeto VECTRA."""

from decimal import Decimal, localcontext, InvalidOperation
from lexer import ALPHABET, REVERSE_ALPHABET

class VectraMathError(ValueError):
    pass

class VectraInvalidOperation(ValueError):
    pass

class Cursor:
    def __init__(self, items):
        self.items = items
        self.i = 0

    def peek(self):
        return self.items[self.i]["value"] if self.i < len(self.items) else None

    def take(self):
        item = self.items[self.i]
        self.i += 1
        return item

    def fail(self, message):
        item = self.items[self.i] if self.i < len(self.items) else (self.items[-1] if self.items else {})
        line, col = item.get("line", 1), item.get("column", 1)
        raise SyntaxError(f"Erro de sintaxe na linha {line}, coluna {col}: {message}")

def _decode_word_sequence(items):
    # Só é texto codificado se todos os caracteres pertencerem ao alfabeto
    # e não houver sinais reservados à matemática.
    raw = "".join(x["value"] for x in items)
    if not raw or any(ch != " " and ch not in ALPHABET for ch in raw):
        return None
    return "".join(" " if ch == " " else ALPHABET[ch] for ch in raw)

def _format_decimal(value):
    if value == 0:
        return "0"
    negative = value < 0
    text = format(value.copy_abs(), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    text = text.replace(".", ":")
    return text + ("N" if negative else "")

def _parse_number(cur):
    if cur.peek() is None or not cur.peek().isdigit():
        cur.fail("era esperado um número.")
    digits = ""
    while cur.peek() is not None and cur.peek().isdigit():
        digits += cur.take()["value"]

    # Expansões: número(+d.q){dígitos}; blocos adicionais podem ser
    # concatenados com ponto, conforme a notação definida para expansões.
    while cur.peek() == "(":
        cur.take()
        if cur.peek() != "+":
            cur.fail("a expansão deve começar com '(+'.")
        cur.take()
        digit = cur.peek()
        if digit is None or not digit.isdigit() or len(digit) != 1:
            cur.fail("a expansão aceita um único algarismo de 0 a 9.")
        cur.take()
        if cur.peek() != ".":
            cur.fail("use '.' entre o algarismo e a quantidade da expansão.")
        cur.take()
        count = ""
        while cur.peek() is not None and cur.peek().isdigit():
            count += cur.take()["value"]
        if not count:
            cur.fail("informe quantas repetições serão feitas.")
        if cur.peek() != ")":
            cur.fail("faltou ')' na expansão.")
        cur.take()
        digits += digit * int(count)
        if cur.peek() == "{":
            cur.take()
            appended = ""
            while cur.peek() is not None and cur.peek().isdigit():
                appended += cur.take()["value"]
            if not appended or cur.peek() != "}":
                cur.fail("use {algarismos} depois da expansão.")
            cur.take()
            digits += appended
        # ponto + outro bloco de expansão concatena blocos numéricos
        if cur.peek() == "." and cur.i + 1 < len(cur.items):
            nxt = cur.items[cur.i + 1]["value"]
            if nxt.isdigit():
                cur.take()
                extra = _parse_number(cur)
                if extra != extra.to_integral_value():
                    cur.fail("blocos concatenados não podem conter decimais.")
                digits += format(extra, "f").split(".")[0]
                break

    if cur.peek() == "{":
        cur.take()
        appended = ""
        while cur.peek() is not None and cur.peek().isdigit():
            appended += cur.take()["value"]
        if not appended or cur.peek() != "}":
            cur.fail("use {algarismos} depois do número.")
        cur.take()
        digits += appended

    negative = False
    if cur.peek() == "N":
        cur.take()
        negative = True

    # Parte decimal usa ':' e também é construída por texto, sem float.
    if cur.peek() == ":":
        cur.take()
        fraction = ""
        while cur.peek() is not None and cur.peek().isdigit():
            fraction += cur.take()["value"]
        if not fraction:
            cur.fail("informe algarismos depois de ':'.")
        digits += "." + fraction

    # Decimal é construído por texto, sem passar por float.
    number = Decimal(digits)
    return -number if negative else number

class Expression:
    def __init__(self, items):
        self.cur = Cursor(items)

    def parse(self):
        result = self._sum()
        if self.cur.peek() is not None:
            self.cur.fail(f"caractere inesperado: {self.cur.peek()!r}.")
        return result

    def _sum(self):
        value = self._product()
        while self.cur.peek() in ("A", "T"):
            op = self.cur.take()["value"]
            right = self._product()
            value = value + right if op == "A" else value - right
        return value

    def _product(self):
        value = self._factor()
        while self.cur.peek() in (",", "D"):
            op = self.cur.take()["value"]
            right = self._factor()
            if op == ",":
                value *= right
            else:
                if right == 0:
                    raise VectraMathError("A operação não pode ser concluída com sucesso.")
                value /= right
        return value

    def _factor(self):
        if self.cur.peek() == "(":
            self.cur.take()
            value = self._sum()
            if self.cur.peek() != ")":
                self.cur.fail("faltou ')' para fechar o agrupamento.")
            self.cur.take()
            return value
        return _parse_number(self.cur)

def _split_elements(items):
    """Ponto separa elementos no nível externo; expansão consome seus pontos."""
    parts, current = [], []
    depth = 0
    i = 0
    while i < len(items):
        ch = items[i]["value"]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        chained_expansion = (
            ch == "." and depth == 0 and current
            and any(x["value"] == ")" for x in current)
            and i + 2 < len(items)
            and items[i + 1]["value"].isdigit()
            and items[i + 2]["value"] == "("
        )
        if ch == "." and depth == 0 and not chained_expansion:
            if not current:
                item = items[i]
                raise SyntaxError(f"Erro de sintaxe na linha {item['line']}, coluna {item['column']}: elemento vazio.")
            parts.append(current)
            current = []
        else:
            current.append(items[i])
        i += 1
    if not current:
        item = items[-1]
        raise SyntaxError(f"Erro de sintaxe na linha {item['line']}, coluna {item['column']}: elemento vazio.")
    parts.append(current)
    return parts

def _comparison(items):
    operators = [i for i, x in enumerate(items) if x["value"] in ("=", "G", "I")]
    if len(operators) != 1:
        return None
    idx = operators[0]
    left, right = items[:idx], items[idx+1:]
    if not left or not right:
        item = items[idx]
        raise SyntaxError(f"Erro de sintaxe na linha {item['line']}, coluna {item['column']}: comparação precisa de dois números.")
    arithmetic_symbols = {"A", "T", ",", "D"}
    if any(x["value"] in arithmetic_symbols for x in left + right):
        item = items[idx]
        raise VectraInvalidOperation(
            f"Operação inválida na linha {item['line']}, coluna {item['column']}: comparação aceita exatamente dois números, sem operações aritméticas."
        )
    a, b = Expression(left).parse(), Expression(right).parse()
    if a < 0 or b < 0:
        item = items[idx]
        raise SyntaxError(f"Erro de sintaxe na linha {item['line']}, coluna {item['column']}: comparações aceitam somente números positivos.")
    op = items[idx]["value"]
    return (a == b) if op == "=" else ((a > b) if op == "G" else (a < b))

def process(sequences):
    results = []
    for sequence in sequences:
        # Espaços são ignorados pelo lexer; um texto codificado sem operadores
        # matemáticos é decodificado diretamente.
        decoded = _decode_word_sequence(sequence)
        if decoded is not None:
            results.append({"type": "text", "value": decoded})
            continue

        # Comparações têm prioridade de reconhecimento e aceitam duas expressões.
        comparison = _comparison(sequence)
        if comparison is not None:
            word = "VERDADEIRO" if comparison else "FALSO"
            encoded = "".join(REVERSE_ALPHABET[c] for c in word)
            results.append({"type": "comparison", "value": encoded, "plain": word})
            continue

        # Cada ponto externo separa um elemento matemático independente.
        for element in _split_elements(sequence):
            if any(x["value"] in ("=", "G", "I") for x in element):
                item = next(x for x in element if x["value"] in ("=", "G", "I"))
                raise VectraInvalidOperation(
                    f"Operação inválida na linha {item['line']}, coluna {item['column']}: comparação não pode ser misturada com outros elementos."
                )
            with localcontext() as ctx:
                ctx.prec = max(100, sum(len(x["value"]) for x in element) + 50)
                value = Expression(element).parse()
            results.append({"type": "number", "value": _format_decimal(value)})
    return results
