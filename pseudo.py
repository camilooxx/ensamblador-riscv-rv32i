
"""
Expansion de pseudoinstrucciones RISC-V RV32I.
Basado en las secciones 5.2 y 5.2.1 del proyecto.

Recibe una instruccion localizada, consulta los
simbolos y devuelve instrucciones RV32I base.
"""

import re

from instructions import (
    INSTRUCTIONS,
    get_register,
    parse_immediate,
    InstructionError,
)

from symbols import (
    resolve_symbol,
    relative_offset,
    value_32bit,
    SymbolError,
)


class PseudoError(ValueError):
    def __init__(self, line_number, message):
        self.line_number = line_number
        super().__init__(message)


# Formato: pseudoinstruccion -> (instruccion base, tipo)
SIMPLE_PSEUDOS = {
    "nop": ("addi", "nop"),
    "mv": ("addi", "mv"),
    "not": ("xori", "not"),
    "neg": ("sub", "neg"),
    "seqz": ("sltiu", "seqz"),
    "snez": ("sltu", "snez"),
    "sltz": ("slt", "sltz"),
    "sgtz": ("slt", "sgtz"),
    "beqz": ("beq", "branch_zero"),
    "bnez": ("bne", "branch_zero"),
    "blez": ("bge", "branch_zero"),
    "bgez": ("bge", "branch_zero"),
    "bltz": ("blt", "branch_zero"),
    "bgtz": ("blt", "branch_zero"),
    "bgt": ("blt", "branch_compare"),
    "ble": ("bge", "branch_compare"),
    "bgtu": ("bltu", "branch_compare"),
    "bleu": ("bgeu", "branch_compare"),
    "j": ("jal", "jump"),
    "jr": ("jalr", "jump_register"),
    "ret": ("jalr", "return"),
}

LOADS = {"lb", "lh", "lw"}
STORES = {"sb", "sh", "sw"}


def require_count(name, operands, count, line):
    if len(operands) != count:
        raise PseudoError(
            line,
            f"'{name}' espera {count} operandos, "
            f"recibio {len(operands)}"
        )


def check_registers(operands, line):
    for register in operands:
        try:
            get_register(register)
        except InstructionError as error:
            raise PseudoError(line, str(error)) from None


def split_hi_lo(value):
    """Calcula partes alta y baja segun 5.2.1."""
    hi = (value + 0x800) >> 12
    lo = value - (hi << 12)
    return hi, lo


def relative_hi_lo(symbols, name, pc, line):
    """Obtiene hi/lo para un simbolo relativo al PC."""
    try:
        distance = relative_offset(symbols, name, pc, line)
    except SymbolError as error:
        raise PseudoError(line, str(error)) from None

    if not -(1 << 31) <= distance <= (1 << 31) - 1:
        raise PseudoError(
            line, f"simbolo '{name}' fuera de alcance"
        )

    hi, lo = split_hi_lo(distance)

    if not -(1 << 19) <= hi <= (1 << 19):
        raise PseudoError(
            line, f"parte alta fuera de rango para '{name}'"
        )

    return hi, lo


def get_target_offset(symbols, label, pc, line):
    """Desplazamiento relativo para saltos y branches."""
    try:
        return relative_offset(symbols, label, pc, line)
    except SymbolError as error:
        raise PseudoError(line, str(error)) from None


def expand_simple(name, operands, pc, symbols, line):
    """Expande pseudoinstrucciones de una instruccion."""
    base, kind = SIMPLE_PSEUDOS[name]

    if kind == "nop":
        require_count(name, operands, 0, line)
        return [("addi", ["x0", "x0", "0"])]

    if kind == "mv":
        require_count(name, operands, 2, line)
        check_registers(operands, line)
        return [("addi", [operands[0], operands[1], "0"])]

    if kind == "not":
        require_count(name, operands, 2, line)
        check_registers(operands, line)
        return [("xori", [operands[0], operands[1], "-1"])]

    if kind == "neg":
        require_count(name, operands, 2, line)
        check_registers(operands, line)
        return [("sub", [operands[0], "x0", operands[1]])]

    if kind == "seqz":
        require_count(name, operands, 2, line)
        check_registers(operands, line)
        return [("sltiu", [operands[0], operands[1], "1"])]

    if kind == "snez":
        require_count(name, operands, 2, line)
        check_registers(operands, line)
        return [("sltu", [operands[0], "x0", operands[1]])]

    if kind == "sltz":
        require_count(name, operands, 2, line)
        check_registers(operands, line)
        return [("slt", [operands[0], operands[1], "x0"])]

    if kind == "sgtz":
        require_count(name, operands, 2, line)
        check_registers(operands, line)
        return [("slt", [operands[0], "x0", operands[1]])]

    if kind == "branch_zero":
        require_count(name, operands, 2, line)
        check_registers([operands[0]], line)
        rs, label = operands
        offset = str(
            get_target_offset(symbols, label, pc, line)
        )

        if name in ("blez", "bgtz"):
            return [(base, ["x0", rs, offset])]

        return [(base, [rs, "x0", offset])]

    if kind == "branch_compare":
        require_count(name, operands, 3, line)
        check_registers(operands[:2], line)
        rs, rt, label = operands
        offset = str(
            get_target_offset(symbols, label, pc, line)
        )
        return [(base, [rt, rs, offset])]

    if kind == "jump":
        require_count(name, operands, 1, line)
        offset = str(
            get_target_offset(symbols, operands[0], pc, line)
        )
        return [("jal", ["x0", offset])]

    if kind == "jump_register":
        require_count(name, operands, 1, line)
        check_registers(operands, line)
        return [("jalr", ["x0", f"0({operands[0]})"])]

    if kind == "return":
        require_count(name, operands, 0, line)
        return [("jalr", ["x0", "0(x1)"])]

    raise PseudoError(line, f"pseudoinstruccion '{name}' invalida")


def expand_li(operands, line):
    """Expande li a una o dos instrucciones base."""
    require_count("li", operands, 2, line)

    rd, immediate = operands
    check_registers([rd], line)

    try:
        value = parse_immediate(immediate)
        value = value_32bit(value, line)
    except (InstructionError, SymbolError) as error:
        raise PseudoError(line, str(error)) from None

    if -2048 <= value <= 2047:
        return [("addi", [rd, "x0", str(value)])]

    hi, lo = split_hi_lo(value)

    if lo == 0:
        return [("lui", [rd, str(hi)])]

    return [
        ("lui", [rd, str(hi)]),
        ("addi", [rd, rd, str(lo)]),
    ]


def expand_la(operands, pc, symbols, line):
    require_count("la", operands, 2, line)

    rd, symbol = operands
    check_registers([rd], line)
    hi, lo = relative_hi_lo(symbols, symbol, pc, line)

    return [
        ("auipc", [rd, str(hi)]),
        ("addi", [rd, rd, str(lo)]),
    ]


def expand_symbol_load(name, operands, pc, symbols, line):
    require_count(name, operands, 2, line)

    rd, symbol = operands
    check_registers([rd], line)
    hi, lo = relative_hi_lo(symbols, symbol, pc, line)

    return [
        ("auipc", [rd, str(hi)]),
        (name, [rd, f"{lo}({rd})"]),
    ]


def expand_symbol_store(name, operands, pc, symbols, line):
    require_count(name, operands, 3, line)

    rs, symbol, rt = operands
    check_registers([rs, rt], line)
    hi, lo = relative_hi_lo(symbols, symbol, pc, line)

    return [
        ("auipc", [rt, str(hi)]),
        (name, [rs, f"{lo}({rt})"]),
    ]


def expand_call(name, operands, pc, symbols, line):
    require_count(name, operands, 1, line)

    symbol = operands[0]
    hi, lo = relative_hi_lo(symbols, symbol, pc, line)

    if name == "call":
        return [
            ("auipc", ["x1", str(hi)]),
            ("jalr", ["x1", f"{lo}(x1)"]),
        ]

    return [
        ("auipc", ["x6", str(hi)]),
        ("jalr", ["x0", f"{lo}(x6)"]),
    ]


def expand_instruction(located, symbols):
    """
    Recibe LocatedInstruction de symbols.py.

    Devuelve una lista de pares:
       (mnemonic, operandos)

    Cada elemento representa una instruccion RV32I.
    """
    name = located.mnemonic.lower()
    operands = located.operands
    pc = located.address
    line = located.line_number

    if name in SIMPLE_PSEUDOS:
        result = expand_simple(
            name, operands, pc, symbols, line
        )

    elif name == "li":
        result = expand_li(operands, line)

    elif name == "la":
        result = expand_la(operands, pc, symbols, line)

    elif name in ("call", "tail"):
        result = expand_call(
            name, operands, pc, symbols, line
        )

    elif name in LOADS and len(operands) == 2:
        if "(" not in operands[1]:
            result = expand_symbol_load(
                name, operands, pc, symbols, line
            )
        else:
            result = [(name, operands)]

    elif name in STORES and len(operands) == 3:
        result = expand_symbol_store(
            name, operands, pc, symbols, line
        )

    elif name == "jal" and len(operands) == 1:
        offset = get_target_offset(
            symbols, operands[0], pc, line
        )
        result = [("jal", ["x1", str(offset)])]

    elif name == "jalr" and len(operands) == 1:
        check_registers(operands, line)
        result = [
            ("jalr", ["x1", f"0({operands[0]})"])
        ]

    elif name in INSTRUCTIONS:
        if name in ("beq", "bne", "blt", "bge", "bltu", "bgeu"):
            if len(operands) != 3:
                raise PseudoError(
                    line, f"'{name}' espera 3 operandos"
                )
            offset = get_target_offset(
                symbols, operands[2], pc, line
            )
            result = [
                (name, [operands[0], operands[1], str(offset)])
            ]

        elif name == "jal":
            if len(operands) != 2:
                raise PseudoError(
                    line, "jal espera 1 o 2 operandos"
                )
            offset = get_target_offset(
                symbols, operands[1], pc, line
            )
            result = [("jal", [operands[0], str(offset)])]

        else:
            result = [(name, operands)]

    else:
        raise PseudoError(
            line,
            f"instruccion o pseudoinstruccion no soportada '{name}'"
        )

    expected_size = located.size
    actual_size = 4 * len(result)

    if actual_size != expected_size:
        raise PseudoError(
            line,
            f"tamano inconsistente para '{name}': "
            f"reservado {expected_size}, expandido {actual_size}"
        )

    return result
