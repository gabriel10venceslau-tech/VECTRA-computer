"""Ponto de entrada do interpretador VECTRA."""

import sys
from pathlib import Path

from lexer import tokenize
from parser import parse
from processor import process, VectraMathError, VectraInvalidOperation

def run_file(file_path):
    path = Path(file_path)
    if not path.exists():
        print(f"ERRO: arquivo não encontrado: {path}")
        return 1
    if path.suffix.lower() != ".vx":
        print("ERRO: o arquivo precisa ter extensão .vx")
        return 1

    try:
        code = path.read_text(encoding="utf-8")
        sequences = parse(tokenize(code))
        results = process(sequences)

        print("=== VECTRA INTERPRETER ===")
        print("Arquivo:", path.name)
        print("\nResultados:")
        for result in results:
            if result["type"] == "comparison":
                print(result["value"], f"({result['plain']})")
            else:
                print(result["value"])
        print("\nExecução concluída!")
        return 0

    except VectraMathError as error:
        print("ERRO MATEMÁTICO:", error)
        return 2
    except VectraInvalidOperation as error:
        print("OPERAÇÃO INVÁLIDA:", error)
        return 3
    except (SyntaxError, ValueError, ArithmeticError) as error:
        print("ERRO VECTRA:", error)
        return 4
    except UnicodeDecodeError:
        print("ERRO: o arquivo precisa estar salvo em UTF-8.")
        return 5

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python main.py caminho\\para\\arquivo.vx")
        raise SystemExit(1)
    raise SystemExit(run_file(sys.argv[1]))
