
import sys
import tempfile
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parent.parent)
)

from errors import validate_source


def check_error(source, expected):
    """Comprueba un error usando un archivo temporal."""
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "programa.asm"
        path.write_text(source, encoding="utf-8")

        words, collector = validate_source(path)

        assert words is None, (
            f"Se esperaba un error: {expected}"
        )

        assert collector.has_errors(), (
            "El ensamblador no reporto errores"
        )

        messages = collector.report()

        assert expected in messages, (
            f"No encontro '{expected}' en:\n{messages}"
        )

        print(f"OK: {expected}")


def test_invalid_instruction():
    check_error(
        ".text\nmultiplicar x1, x2, x3\n",
        "instruccion no soportada"
    )


def test_invalid_register():
    check_error(
        ".text\nadd x32, x1, x2\n",
        "registro inexistente"
    )


def test_wrong_operand():
    check_error(
        ".text\naddi x1, x2, x3\n",
        "inmediato invalido"
    )


def test_immediate_range():
    check_error(
        ".text\naddi x1, x2, 4096\n",
        "fuera de rango"
    )


def test_shift_range():
    check_error(
        ".text\nslli x1, x2, 32\n",
        "fuera de rango"
    )


def test_undefined_label():
    check_error(
        ".text\nbeq x1, x2, nowhere\n",
        "no definida"
    )


def test_duplicate_label():
    check_error(
        ".text\ninicio: nop\ninicio: nop\n",
        "etiqueta duplicada"
    )



def test_syntax():
    check_error(
        ".text\naddi x1, x2, (3\n",
        "paréntesis sin cerrar"
    )


def test_multiple_errors():
    source = (
        ".text\n"
        "addi x1, x2, 4096\n"
        "add x32, x1, x2\n"
        "slli x1, x2, 32\n"
    )

    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "varios.asm"
        path.write_text(source, encoding="utf-8")

        words, collector = validate_source(path)

        assert words is None
        assert len(collector.errors) == 3

        assert [e.line_number for e in collector.errors] == [
            2, 3, 4
        ]

        print("OK: multiples errores detectados")


def test_valid_program():
    source = (
        ".text\n"
        "addi x5, x0, 10\n"
        "add x6, x5, x5\n"
    )

    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "valido.asm"
        path.write_text(source, encoding="utf-8")

        words, collector = validate_source(path)

        assert not collector.has_errors()
        assert words == [0x00A00293, 0x00528333]

        print("OK: programa valido")


if __name__ == "__main__":
    print("=== PRUEBAS DE ERRORES RV32I ===")

    test_invalid_instruction()
    test_invalid_register()
    test_wrong_operand()
    test_immediate_range()
    test_shift_range()
    test_undefined_label()
    test_duplicate_label()
    test_syntax()
    test_multiple_errors()
    test_valid_program()

    print()
    print("FASE 7: PRUEBAS BASICAS SUPERADAS")
