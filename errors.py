"""
Manejo de diagnosticos del ensamblador RV32I.

Relaciona errores con su archivo y linea.
Valida las instrucciones expandidas y codificadas.

No escribe archivos HEX: esa responsabilidad
correspondera a assembler.py.
"""

from dataclasses import dataclass
from pathlib import Path

from parser import parse_line, ParserError
from symbols import build_layout, SymbolError
from pseudo import expand_instruction, PseudoError
from encoder import encode_instruction
from instructions import InstructionError


@dataclass
class Diagnostic:
    filename: str
    line_number: int
    message: str

    def __str__(self):
        if self.line_number > 0:
            return (
                f"{self.filename}:{self.line_number}: "
                f"error: {self.message}"
            )

        return f"{self.filename}: error: {self.message}"


class ErrorCollector:
    """Almacena los errores de un archivo ASM."""

    def __init__(self, filename):
        self.filename = str(filename)
        self.errors = []

    def add(self, line_number, message):
        self.errors.append(
            Diagnostic(
                self.filename,
                line_number,
                str(message)
            )
        )

    def has_errors(self):
        return bool(self.errors)

    def report(self):
        return "\n".join(
            str(error) for error in self.errors
        )


def validate_source(filename):
    """
    Lee, analiza, expande y codifica en memoria.

    Devuelve:
        (palabras_codificadas, collector)

    Si se detectan errores:
        palabras_codificadas sera None.

    No crea ni modifica archivos de salida.
    """
    collector = ErrorCollector(filename)
    parsed_lines = []

    # Etapa 1: lectura y analisis sintactico
    try:
        with open(filename, "r", encoding="utf-8") as file:
            for number, text in enumerate(file, 1):
                try:
                    parsed = parse_line(text, number)
                    if parsed is not None:
                        parsed_lines.append(parsed)

                except ParserError as error:
                    collector.add(
                        error.line_number, str(error)
                    )

    except (OSError, UnicodeError) as error:
        collector.add(0, str(error))
        return None, collector

    if collector.has_errors():
        return None, collector

    # Etapa 2: tabla de simbolos y direcciones
    try:
        layout = build_layout(parsed_lines)

    except SymbolError as error:
        collector.add(
            error.line_number, str(error)
        )
        return None, collector

    # Etapa 3: expandir y validar cada instruccion
    encoded_words = []

    for instruction in layout.instructions:
        try:
            expanded = expand_instruction(
                instruction, layout.symbols
            )

            for mnemonic, operands in expanded:
                word = encode_instruction(
                    mnemonic, operands
                )
                encoded_words.append(word)

        except (
            PseudoError,
            SymbolError,
            InstructionError,
            ValueError
        ) as error:
            collector.add(
                instruction.line_number,
                str(error)
            )

    if collector.has_errors():
        return None, collector

    return encoded_words, collector
