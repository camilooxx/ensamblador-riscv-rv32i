
import sys
from pathlib import Path

# Permite importar los modulos desde la carpeta principal.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from instructions import (
    INSTRUCTIONS,
    get_instruction,
    get_register,
    parse_immediate,
    validate_operand_count,
    InstructionError,
)


def test_instructions():
    assert len(INSTRUCTIONS) == 39

    expected_formats = {
        "R": 10,
        "I": 17,
        "S": 3,
        "B": 6,
        "U": 2,
        "J": 1,
    }

    for fmt, expected in expected_formats.items():
        actual = sum(
            1 for inst in INSTRUCTIONS.values()
            if inst["format"] == fmt
        )
        assert actual == expected, (
            f"Formato {fmt}: esperado {expected}, obtenido {actual}"
        )

    assert "fence" not in INSTRUCTIONS
    assert "mul" not in INSTRUCTIONS

    print("OK: conjunto base RV32I")


def test_registers():
    for i in range(32):
        assert get_register(f"x{i}") == i

    assert get_register("zero") == 0
    assert get_register("ra") == 1
    assert get_register("sp") == 2
    assert get_register("t0") == 5
    assert get_register("fp") == 8
    assert get_register("a0") == 10
    assert get_register("s11") == 27
    assert get_register("t6") == 31

    print("OK: registros numericos y ABI")


def test_immediates():
    assert parse_immediate("42") == 42
    assert parse_immediate("-12") == -12
    assert parse_immediate("0xFF") == 255
    assert parse_immediate("0b1010") == 10

    print("OK: inmediatos")


def test_operands():
    assert validate_operand_count(
        "add", ["x1", "x2", "x3"]
    )

    assert validate_operand_count(
        "lw", ["t0", "8(sp)"]
    )

    assert validate_operand_count(
        "ecall", []
    )

    assert get_instruction("srai")["funct7"] == 0x20

    print("OK: cantidad de operandos")


def test_errors():
    invalid_registers = ["x32", "t7", "a8"]

    for name in invalid_registers:
        try:
            get_register(name)
            raise AssertionError(
                f"No detecto registro invalido: {name}"
            )
        except InstructionError:
            pass

    try:
        get_instruction("mul")
        raise AssertionError("No rechazo extension M")
    except InstructionError:
        pass

    try:
        validate_operand_count("add", ["x1", "x2"])
        raise AssertionError("No detecto operando faltante")
    except InstructionError:
        pass

    print("OK: errores basicos")


if __name__ == "__main__":
    test_instructions()
    test_registers()
    test_immediates()
    test_operands()
    test_errors()

    print()
    print("FASE 3: TODAS LAS PRUEBAS SUPERADAS")
