
import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parent.parent)
)

from parser import parse_line
from symbols import (
    build_layout,
    resolve_symbol,
    relative_offset,
    SymbolError,
)


def analyze(source):
    parsed = []

    for number, line in enumerate(
        source.splitlines(), start=1
    ):
        result = parse_line(line, number)

        if result is not None:
            parsed.append(result)

    return build_layout(parsed)


def test_labels():
    source = """
.data
numero: .word 25
mensaje: .string "Hola"

.text
main:
    addi t0, zero, 10
loop:
    addi t0, t0, -1
    bne t0, zero, loop
fin:
    nop
"""
    layout = analyze(source)
    symbols = layout.symbols

    assert resolve_symbol(symbols, "numero", 1) == 0x10000000
    assert resolve_symbol(symbols, "mensaje", 1) == 0x10000004
    assert resolve_symbol(symbols, "main", 1) == 0
    assert resolve_symbol(symbols, "loop", 1) == 4
    assert resolve_symbol(symbols, "fin", 1) == 12

    assert layout.text_size == 16
    assert layout.data_size == 9

    assert relative_offset(
        symbols, "loop", 8, 1
    ) == -4

    print("OK: etiquetas y direcciones")


def test_two_instructions():
    source = """
.text
inicio:
    li t0, 0x12345FFF
    la t1, numero
    call funcion
funcion:
    ret

.data
numero: .word 100
"""

    layout = analyze(source)
    instructions = layout.instructions

    assert [i.address for i in instructions] == [
        0, 8, 16, 24
    ]

    assert [i.size for i in instructions] == [
        8, 8, 8, 4
    ]

    assert layout.symbols["funcion"].address == 24
    assert layout.symbols["numero"].address == 0x10000000

    print("OK: pseudoinstrucciones de dos instrucciones")


def test_data():
    source = """
.data
b: .byte 1, 2, 3
h: .half 100, 200
w: .word 1234
s: .string "ABC"
"""

    layout = analyze(source)

    assert layout.symbols["b"].address == 0x10000000
    assert layout.symbols["h"].address == 0x10000003
    assert layout.symbols["w"].address == 0x10000007
    assert layout.symbols["s"].address == 0x1000000B

    assert layout.data_size == 15

    print("OK: tamanos de directivas")


def test_duplicate_label():
    source = """
.text
inicio: addi x1, x0, 1
inicio: addi x2, x0, 2
"""
    try:
        analyze(source)
    except SymbolError as error:
        assert "duplicada" in str(error)
        print("OK: etiqueta duplicada detectada")
        return

    raise AssertionError("No detecto etiqueta duplicada")


def test_undefined_label():
    layout = analyze(".text\nmain: nop")

    try:
        resolve_symbol(layout.symbols, "no_existe", 2)
    except SymbolError as error:
        assert "no definida" in str(error)
        print("OK: etiqueta inexistente detectada")
        return

    raise AssertionError("No detecto etiqueta inexistente")


def test_invalid_directive():
    try:
        analyze(".text\nvalor: .word 10")
    except SymbolError:
        print("OK: directiva en segmento incorrecto")
        return

    raise AssertionError("No detecto directiva invalida")


def main():
    print("=== PRUEBAS DE SIMBOLOS RV32I ===")

    test_labels()
    test_two_instructions()
    test_data()
    test_duplicate_label()
    test_undefined_label()
    test_invalid_directive()

    print()
    print("FASE 5: PRUEBAS BASICAS SUPERADAS")


if __name__ == "__main__":
    main()
