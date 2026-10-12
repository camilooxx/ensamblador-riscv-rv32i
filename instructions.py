
"""
Definiciones de instrucciones y registros RISC-V RV32I.

Proyecto: Ensamblador RV32I
Arquitectura de Computadores

No incluye la instruccion FENCE ni extensiones M, A, F, D, C.
"""

# -------------------------------------------------
# 1. REGISTROS RISC-V
# -------------------------------------------------

REGISTERS = {f"x{i}": i for i in range(32)}

ABI_REGISTERS = {
    "zero": 0,
    "ra": 1,
    "sp": 2,
    "gp": 3,
    "tp": 4,
    "t0": 5,
    "t1": 6,
    "t2": 7,
    "s0": 8,
    "fp": 8,
    "s1": 9,
    "a0": 10,
    "a1": 11,
    "a2": 12,
    "a3": 13,
    "a4": 14,
    "a5": 15,
    "a6": 16,
    "a7": 17,
    "s2": 18,
    "s3": 19,
    "s4": 20,
    "s5": 21,
    "s6": 22,
    "s7": 23,
    "s8": 24,
    "s9": 25,
    "s10": 26,
    "s11": 27,
    "t3": 28,
    "t4": 29,
    "t5": 30,
    "t6": 31,
}

REGISTERS.update(ABI_REGISTERS)


# -------------------------------------------------
# 2. TABLA DE INSTRUCCIONES RV32I
# -------------------------------------------------
# Campos:
# format: tipo de instruccion
# opcode: codigo de operacion de 7 bits
# funct3: campo de 3 bits, cuando aplica
# funct7: campo de 7 bits, cuando aplica
# operands: cantidad de operandos esperados

INSTRUCTIONS = {
    # FORMATO R
    "add":  {"format": "R", "opcode": 0x33, "funct3": 0, "funct7": 0x00, "operands": 3},
    "sub":  {"format": "R", "opcode": 0x33, "funct3": 0, "funct7": 0x20, "operands": 3},
    "sll":  {"format": "R", "opcode": 0x33, "funct3": 1, "funct7": 0x00, "operands": 3},
    "slt":  {"format": "R", "opcode": 0x33, "funct3": 2, "funct7": 0x00, "operands": 3},
    "sltu": {"format": "R", "opcode": 0x33, "funct3": 3, "funct7": 0x00, "operands": 3},
    "xor":  {"format": "R", "opcode": 0x33, "funct3": 4, "funct7": 0x00, "operands": 3},
    "srl":  {"format": "R", "opcode": 0x33, "funct3": 5, "funct7": 0x00, "operands": 3},
    "sra":  {"format": "R", "opcode": 0x33, "funct3": 5, "funct7": 0x20, "operands": 3},
    "or":   {"format": "R", "opcode": 0x33, "funct3": 6, "funct7": 0x00, "operands": 3},
    "and":  {"format": "R", "opcode": 0x33, "funct3": 7, "funct7": 0x00, "operands": 3},

    # FORMATO I - ARITMETICAS
    "addi":  {"format": "I", "opcode": 0x13, "funct3": 0, "operands": 3},
    "slti":  {"format": "I", "opcode": 0x13, "funct3": 2, "operands": 3},
    "sltiu": {"format": "I", "opcode": 0x13, "funct3": 3, "operands": 3},
    "xori":  {"format": "I", "opcode": 0x13, "funct3": 4, "operands": 3},
    "ori":   {"format": "I", "opcode": 0x13, "funct3": 6, "operands": 3},
    "andi":  {"format": "I", "opcode": 0x13, "funct3": 7, "operands": 3},
    "slli":  {"format": "I", "opcode": 0x13, "funct3": 1, "funct7": 0x00, "operands": 3},
    "srli":  {"format": "I", "opcode": 0x13, "funct3": 5, "funct7": 0x00, "operands": 3},
    "srai":  {"format": "I", "opcode": 0x13, "funct3": 5, "funct7": 0x20, "operands": 3},

    # FORMATO I - CARGAS
    "lb":  {"format": "I", "opcode": 0x03, "funct3": 0, "operands": 2},
    "lh":  {"format": "I", "opcode": 0x03, "funct3": 1, "operands": 2},
    "lw":  {"format": "I", "opcode": 0x03, "funct3": 2, "operands": 2},
    "lbu": {"format": "I", "opcode": 0x03, "funct3": 4, "operands": 2},
    "lhu": {"format": "I", "opcode": 0x03, "funct3": 5, "operands": 2},

    # FORMATO I - OTRAS
    "jalr":   {"format": "I", "opcode": 0x67, "funct3": 0, "operands": 2},
    "ecall":  {"format": "I", "opcode": 0x73, "funct3": 0, "operands": 0},
    "ebreak": {"format": "I", "opcode": 0x73, "funct3": 0, "operands": 0},

    # FORMATO S
    "sb": {"format": "S", "opcode": 0x23, "funct3": 0, "operands": 2},
    "sh": {"format": "S", "opcode": 0x23, "funct3": 1, "operands": 2},
    "sw": {"format": "S", "opcode": 0x23, "funct3": 2, "operands": 2},

    # FORMATO B
    "beq":  {"format": "B", "opcode": 0x63, "funct3": 0, "operands": 3},
    "bne":  {"format": "B", "opcode": 0x63, "funct3": 1, "operands": 3},
    "blt":  {"format": "B", "opcode": 0x63, "funct3": 4, "operands": 3},
    "bge":  {"format": "B", "opcode": 0x63, "funct3": 5, "operands": 3},
    "bltu": {"format": "B", "opcode": 0x63, "funct3": 6, "operands": 3},
    "bgeu": {"format": "B", "opcode": 0x63, "funct3": 7, "operands": 3},

    # FORMATO U
    "lui":   {"format": "U", "opcode": 0x37, "operands": 2},
    "auipc": {"format": "U", "opcode": 0x17, "operands": 2},

    # FORMATO J
    "jal": {"format": "J", "opcode": 0x6F, "operands": 2},
}


# -------------------------------------------------
# 3. CONSULTAS Y VALIDACIONES BASICAS
# -------------------------------------------------

class InstructionError(ValueError):
    """Error de instruccion, registro u operando."""


def get_register(name):
    """Convierte un registro RISC-V a su numero (0-31)."""
    key = name.strip().lower()

    if key not in REGISTERS:
        raise InstructionError(
            f"registro inexistente '{name}'"
        )

    return REGISTERS[key]


def get_instruction(mnemonic):
    """Obtiene los datos de una instruccion RV32I."""
    key = mnemonic.strip().lower()

    if key not in INSTRUCTIONS:
        raise InstructionError(
            f"instruccion no soportada '{mnemonic}'"
        )

    return INSTRUCTIONS[key]


def parse_immediate(value):
    """Convierte numeros decimales, hexadecimales o binarios."""
    value = value.strip()

    try:
        if value.lower().startswith(("0x", "+0x", "-0x")):
            return int(value, 16)

        if value.lower().startswith(("0b", "+0b", "-0b")):
            return int(value, 2)

        return int(value, 10)

    except ValueError:
        raise InstructionError(
            f"inmediato invalido '{value}'"
        ) from None


def validate_operand_count(mnemonic, operands):
    """Comprueba la cantidad de operandos."""
    instruction = get_instruction(mnemonic)
    expected = instruction["operands"]

    if len(operands) != expected:
        raise InstructionError(
            f"'{mnemonic}' espera {expected} operandos, "
            f"pero recibio {len(operands)}"
        )

    return True
