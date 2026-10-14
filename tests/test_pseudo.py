
import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parent.parent)
)

from parser import parse_line
from symbols import build_layout
from pseudo import expand_instruction, PseudoError
from encoder import encode_instruction, to_hex


def analyze(source):
    parsed = []

    for number, text in enumerate(source.splitlines(), 1):
        line = parse_line(text, number)
        if line is not None:
            parsed.append(line)

    return build_layout(parsed)


def expand_program(source):
    layout = analyze(source)
    result = []

    for instruction in layout.instructions:
        result.extend(
            expand_instruction(instruction, layout.symbols)
        )

    return result


def encode_program(source):
    expanded = expand_program(source)

    return [
        to_hex(encode_instruction(name, operands))
        for name, operands in expanded
    ]


def test_simple():
    source = """
.text
    nop
    mv t0, t1
    not t0, t1
    neg t0, t1
    seqz t0, t1
    snez t0, t1
    sltz t0, t1
    sgtz t0, t1
"""
    result = expand_program(source)

    expected = [
        ("addi", ["x0", "x0", "0"]),
        ("addi", ["t0", "t1", "0"]),
        ("xori", ["t0", "t1", "-1"]),
        ("sub", ["t0", "x0", "t1"]),
        ("sltiu", ["t0", "t1", "1"]),
        ("sltu", ["t0", "x0", "t1"]),
        ("slt", ["t0", "t1", "x0"]),
        ("slt", ["t0", "x0", "t1"]),
    ]

    assert result == expected
    print("OK: operaciones simples")


def test_li():
    assert expand_program(
        ".text\nli t0, 10"
    ) == [("addi", ["t0", "x0", "10"])]

    assert expand_program(
        ".text\nli t0, 0x12345000"
    ) == [("lui", ["t0", "74565"])]

    assert expand_program(
        ".text\nli t0, 0x12345FFF"
    ) == [
        ("lui", ["t0", "74566"]),
        ("addi", ["t0", "t0", "-1"]),
    ]

    assert expand_program(
        ".text\nli t0, 0xFFFFFFFF"
    ) == [("addi", ["t0", "x0", "-1"])]

    print("OK: li de 12 y 32 bits")


def test_branches():
    source = """
.text
inicio:
    beqz t0, fin
    bnez t0, inicio
    blez t0, fin
    bgez t0, inicio
    bltz t0, fin
    bgtz t0, inicio
    bgt t0, t1, fin
    ble t0, t1, inicio
    bgtu t0, t1, fin
    bleu t0, t1, inicio
fin:
    nop
"""
    result = expand_program(source)

    assert result[0] == ("beq", ["t0", "x0", "40"])
    assert result[1] == ("bne", ["t0", "x0", "-4"])
    assert result[2] == ("bge", ["x0", "t0", "32"])
    assert result[6] == ("blt", ["t1", "t0", "16"])
    assert result[8] == ("bltu", ["t1", "t0", "8"])
    assert result[9] == ("bgeu", ["t1", "t0", "-36"])

    print("OK: bifurcaciones y etiquetas")


def test_jumps():
    source = """
.text
inicio:
    j fin
    jal fin
    jr ra
    jalr t0
    ret
fin:
    nop
"""
    result = expand_program(source)

    assert result[0] == ("jal", ["x0", "20"])
    assert result[1] == ("jal", ["x1", "16"])
    assert result[2] == ("jalr", ["x0", "0(ra)"])
    assert result[3] == ("jalr", ["x1", "0(t0)"])
    assert result[4] == ("jalr", ["x0", "0(x1)"])

    print("OK: saltos y retornos")


def test_symbols():
    source = """
.data
numero: .word 100

.text
inicio:
    la t0, numero
    lw t1, numero
    sw t1, numero, t2
    call funcion
    tail funcion
funcion:
    ret
"""
    layout = analyze(source)
    result = expand_program(source)

    assert len(result) == 11
    assert layout.symbols["funcion"].address == 40
    assert result[0][0] == "auipc"
    assert result[1][0] == "addi"
    assert result[2][0] == "auipc"
    assert result[3][0] == "lw"
    assert result[4][0] == "auipc"
    assert result[5][0] == "sw"
    assert result[6][0] == "auipc"
    assert result[7][0] == "jalr"
    assert result[8][0] == "auipc"
    assert result[9][0] == "jalr"

    print("OK: la, cargas, almacenes, call y tail")


def test_errors():
    try:
        expand_program(".text\nj etiqueta_inexistente")
    except PseudoError as error:
        assert "no definida" in str(error)
    else:
        raise AssertionError("No detecto etiqueta inexistente")

    try:
        expand_program(".text\nmv x32, x1")
    except PseudoError as error:
        assert "registro inexistente" in str(error)
    else:
        raise AssertionError("No detecto registro invalido")

    print("OK: errores de pseudoinstrucciones")


def test_hex():
    source = """
.text
    li a0, 10
    li a1, 0
    nop
"""
    assert encode_program(source) == [
        "00a00513",
        "00000593",
        "00000013",
    ]

    print("OK: codificacion hexadecimal de expansiones")


if __name__ == "__main__":
    print("=== PRUEBAS DE PSEUDOINSTRUCCIONES ===")

    test_simple()
    test_li()
    test_branches()
    test_jumps()
    test_symbols()
    test_errors()
    test_hex()

    print()
    print("FASE 6: PRUEBAS BASICAS SUPERADAS")
