
"""
Tabla de simbolos y distribucion de memoria RV32I.

Calcula direcciones para .text y .data, identifica
etiquetas y determina el espacio de instrucciones
y pseudoinstrucciones.

No genera codigo hexadecimal todavia.
"""

import ast
from dataclasses import dataclass

from instructions import (
    INSTRUCTIONS,
    parse_immediate,
    InstructionError,
)


TEXT_START = 0x00000000
DATA_START = 0x10000000


# Pseudoinstrucciones incluidas en la seccion 5.2
SIMPLE_PSEUDOS = {
    "nop", "mv", "not", "neg",
    "seqz", "snez", "sltz", "sgtz",
    "beqz", "bnez", "blez", "bgez",
    "bltz", "bgtz", "bgt", "ble",
    "bgtu", "bleu",
    "j", "jr", "ret",
}

# Estas expansiones ocupan siempre 2 instrucciones.
TWO_INSTRUCTION_PSEUDOS = {
    "la", "call", "tail",
}

DATA_DIRECTIVES = {
    ".word": 4,
    ".half": 2,
    ".byte": 1,
}


class SymbolError(ValueError):
    def __init__(self, line_number, message):
        self.line_number = line_number
        super().__init__(message)


@dataclass
class Symbol:
    name: str
    address: int
    segment: str
    line_number: int


@dataclass
class LocatedInstruction:
    address: int
    line_number: int
    mnemonic: str
    operands: list
    size: int


@dataclass
class Layout:
    symbols: dict
    instructions: list
    data_size: int
    text_size: int


def value_32bit(value, line_number):
    """Interpreta un inmediato como valor de 32 bits."""
    if value < -(1 << 31) or value > 0xFFFFFFFF:
        raise SymbolError(
            line_number,
            f"inmediato {value} fuera del rango de 32 bits"
        )

    unsigned = value & 0xFFFFFFFF

    if unsigned >= (1 << 31):
        return unsigned - (1 << 32)

    return unsigned


def instruction_size(mnemonic, operands, line_number):
    """
    Devuelve el numero de bytes que ocupa una
    instruccion, considerando pseudoinstrucciones.
    """
    mnemonic = mnemonic.lower()

    if mnemonic == "li":
        if len(operands) != 2:
            raise SymbolError(
                line_number, "li espera 2 operandos"
            )

        try:
            value = parse_immediate(operands[1])
        except InstructionError as error:
            raise SymbolError(line_number, str(error))

        value = value_32bit(value, line_number)

        if -2048 <= value <= 2047:
            return 4

        hi = (value + 0x800) >> 12
        lo = value - (hi << 12)

        return 4 if lo == 0 else 8

    if mnemonic in TWO_INSTRUCTION_PSEUDOS:
        return 8

    # Cargas desde un simbolo:
    # lb rd, simbolo / lh rd, simbolo / lw rd, simbolo
    if mnemonic in {"lb", "lh", "lw"}:
        if len(operands) == 2 and "(" not in operands[1]:
            return 8

    # Almacenamientos hacia un simbolo:
    # sb rs, simbolo, rt
    if mnemonic in {"sb", "sh", "sw"}:
        if len(operands) == 3:
            return 8

    if mnemonic in INSTRUCTIONS or mnemonic in SIMPLE_PSEUDOS:
        return 4

    raise SymbolError(
        line_number,
        f"instruccion no soportada '{mnemonic}'"
    )


def parse_data_string(operand, line_number):
    """Interpreta una cadena entre comillas."""
    try:
        value = ast.literal_eval(operand)
    except (SyntaxError, ValueError):
        raise SymbolError(
            line_number,
            "cadena .string invalida"
        ) from None

    if not isinstance(value, str):
        raise SymbolError(
            line_number,
            ".string necesita una cadena entre comillas"
        )

    # Cadena terminada en un byte nulo.
    return value.encode("utf-8") + b"\x00"


def data_directive_size(directive, operands, line_number):
    """Calcula los bytes reservados por una directiva."""
    if directive in DATA_DIRECTIVES:
        if not operands:
            raise SymbolError(
                line_number,
                f"{directive} necesita valores"
            )

        bits = DATA_DIRECTIVES[directive] * 8

        for operand in operands:
            try:
                value = parse_immediate(operand)
            except InstructionError as error:
                raise SymbolError(line_number, str(error))

            minimum = -(1 << (bits - 1))
            maximum = (1 << bits) - 1

            if not minimum <= value <= maximum:
                raise SymbolError(
                    line_number,
                    f"valor {value} fuera de rango para "
                    f"{directive}"
                )

        return len(operands) * DATA_DIRECTIVES[directive]

    if directive == ".string":
        if len(operands) != 1:
            raise SymbolError(
                line_number,
                ".string espera una cadena"
            )

        return len(parse_data_string(
            operands[0], line_number
        ))

    raise SymbolError(
        line_number,
        f"directiva no soportada '{directive}'"
    )


def build_layout(parsed_lines):
    """Calcula la distribucion y tabla de simbolos."""
    symbols = {}
    instructions = []

    segment = ".text"
    text_pc = TEXT_START
    data_pc = DATA_START

    for line in parsed_lines:
        number = line.number
        directive = line.directive
        mnemonic = line.instruction
        operands = line.operands or []

        # Cambiar de segmento antes de registrar etiquetas.
        if directive in {".text", ".data"}:
            if operands:
                raise SymbolError(
                    number,
                    f"{directive} no espera operandos"
                )
            segment = directive

        # Guardar etiquetas.
        if line.label is not None:
            name = line.label

            if name in symbols:
                original = symbols[name].line_number
                raise SymbolError(
                    number,
                    f"etiqueta duplicada '{name}' "
                    f"(definida antes en linea {original})"
                )

            address = (
                text_pc if segment == ".text" else data_pc
            )

            symbols[name] = Symbol(
                name=name,
                address=address,
                segment=segment,
                line_number=number,
            )

        if directive is not None:
            if directive in {".text", ".data"}:
                continue

            if segment != ".data":
                raise SymbolError(
                    number,
                    f"{directive} solo se admite en .data"
                )

            data_pc += data_directive_size(
                directive, operands, number
            )
            continue

        if mnemonic is None:
            continue

        if segment != ".text":
            raise SymbolError(
                number,
                "las instrucciones deben estar en .text"
            )

        size = instruction_size(
            mnemonic, operands, number
        )

        instructions.append(
            LocatedInstruction(
                address=text_pc,
                line_number=number,
                mnemonic=mnemonic,
                operands=operands,
                size=size,
            )
        )

        text_pc += size

    return Layout(
        symbols=symbols,
        instructions=instructions,
        data_size=data_pc - DATA_START,
        text_size=text_pc - TEXT_START,
    )


def resolve_symbol(symbols, name, line_number):
    """Consulta la direccion de una etiqueta."""
    if name not in symbols:
        raise SymbolError(
            line_number,
            f"etiqueta '{name}' no definida"
        )

    return symbols[name].address


def relative_offset(symbols, name, pc, line_number):
    """Calcula la distancia entre simbolo y PC."""
    target = resolve_symbol(
        symbols, name, line_number
    )
    return target - pc
