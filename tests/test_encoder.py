
"""
Pruebas del codificador RISC-V RV32I.
Arquitectura de Computadores.

Verifica los formatos R, I, S, B, U y J,
instrucciones de sistema y manejo de errores.
"""

import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parent.parent)
)

from encoder import encode_instruction, to_hex
from instructions import InstructionError


def verify(mnemonic, operands, expected):
    """Comprueba la codificacion hexadecimal."""
    result = to_hex(
        encode_instruction(mnemonic, operands)
    )

    assert result == expected, (
        f"{mnemonic}: esperado {expected}, "
        f"obtenido {result}"
    )

    print(f"OK: {mnemonic:<8} -> {result}")


def verify_error(mnemonic, operands):
    """Verifica que se detecten entradas invalidas."""
    try:
        encode_instruction(mnemonic, operands)
    except InstructionError:
        print(f"OK: error detectado en {mnemonic}")
        return

    raise AssertionError(
        f"No se detecto el error: {mnemonic} {operands}"
    )


def test_format_r():
    verify("add", ["x5", "x6", "x7"], "007302b3")
    verify("sub", ["x5", "x6", "x7"], "407302b3")


def test_format_i():
    verify("addi", ["x5", "x0", "10"], "00a00293")
    verify("srai", ["x5", "x6", "3"], "40335293")
    verify("lw", ["t0", "8(sp)"], "00812283")
    verify("ecall", [], "00000073")
    verify("ebreak", [], "00100073")


def test_format_s():
    verify("sw", ["t0", "8(sp)"], "00512423")


def test_format_b():
    verify("beq", ["x5", "x6", "16"], "00628863")
    verify("bne", ["x5", "x6", "-4"], "fe629ee3")


def test_format_u():
    verify("lui", ["x5", "0x12345"], "123452b7")
    verify("auipc", ["x5", "0x12345"], "12345297")


def test_format_j():
    verify("jal", ["ra", "16"], "010000ef")
    verify("jal", ["zero", "-12"], "ff5ff06f")


def test_errors():
    verify_error("addi", ["x1", "x2", "4096"])
    verify_error("slli", ["x1", "x2", "32"])
    verify_error("beq", ["x1", "x2", "3"])
    verify_error("jal", ["ra", "1048576"])
    verify_error("sw", ["x5", "5000(sp)"])
    verify_error("mul", ["x1", "x2", "x3"])
    verify_error("add", ["x32", "x1", "x2"])


if __name__ == "__main__":
    print("=== PRUEBAS DEL CODIFICADOR RV32I ===")

    test_format_r()
    test_format_i()
    test_format_s()
    test_format_b()
    test_format_u()
    test_format_j()
    test_errors()

    print()
    print("FASE 4: PRUEBAS BASICAS SUPERADAS")
