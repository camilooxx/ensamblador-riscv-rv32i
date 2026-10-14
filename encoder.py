
"""
Codificador de instrucciones RISC-V RV32I.

Proyecto: Arquitectura de Computadores
Entrega 1: Ensamblador RV32I

Formatos soportados: R, I, S, B, U, J.
No implementa FENCE ni extensiones adicionales.

Este modulo codifica instrucciones base.
Las pseudoinstrucciones se expanden en pseudo.py.
"""

import re

from instructions import (
    get_instruction,
    get_register,
    parse_immediate,
    validate_operand_count,
    InstructionError,
)


# ------------------------------------------
# VALIDACION DE INMEDIATOS
# ------------------------------------------

def check_range(value, minimum, maximum, description):
    if not minimum <= value <= maximum:
        raise InstructionError(
            f"{description} {value} fuera de rango "
            f"[{minimum}, {maximum}]"
        )


def signed_immediate(value, bits):
    minimum = -(1 << (bits - 1))
    maximum = (1 << (bits - 1)) - 1

    check_range(value, minimum, maximum, "inmediato")

    return value & ((1 << bits) - 1)


def parse_memory_operand(operand):
    """
    Interpreta operandos como:
        8(sp)
        -4(x5)
        (sp)
    """
    match = re.fullmatch(
        r"\s*(.*?)\s*\(\s*([A-Za-z0-9_]+)\s*\)\s*",
        operand
    )

    if not match:
        raise InstructionError(
            f"operando de memoria invalido '{operand}'"
        )

    offset_text = match.group(1).strip()
    register_text = match.group(2)

    offset = (
        parse_immediate(offset_text)
        if offset_text else 0
    )

    rs1 = get_register(register_text)

    return offset, rs1


# ------------------------------------------
# FORMATO R
# ------------------------------------------

def encode_r(rd, rs1, rs2, funct3, funct7, opcode):
    return (
        (funct7 << 25)
        | (rs2 << 20)
        | (rs1 << 15)
        | (funct3 << 12)
        | (rd << 7)
        | opcode
    )


# ------------------------------------------
# FORMATO I
# ------------------------------------------

def encode_i(rd, rs1, imm, funct3, opcode):
    imm = signed_immediate(imm, 12)

    return (
        (imm << 20)
        | (rs1 << 15)
        | (funct3 << 12)
        | (rd << 7)
        | opcode
    )


# ------------------------------------------
# FORMATO S
# ------------------------------------------

def encode_s(rs2, rs1, imm, funct3, opcode):
    imm = signed_immediate(imm, 12)

    imm_high = (imm >> 5) & 0x7F
    imm_low = imm & 0x1F

    return (
        (imm_high << 25)
        | (rs2 << 20)
        | (rs1 << 15)
        | (funct3 << 12)
        | (imm_low << 7)
        | opcode
    )


# ------------------------------------------
# FORMATO B
# ------------------------------------------

def encode_b(rs1, rs2, offset, funct3, opcode):
    check_range(
        offset, -4096, 4094, "desplazamiento"
    )

    if offset % 2 != 0:
        raise InstructionError(
            "desplazamiento B debe ser multiplo de 2"
        )

    imm = offset & 0x1FFF

    bit12 = (imm >> 12) & 1
    bit11 = (imm >> 11) & 1
    bits10_5 = (imm >> 5) & 0x3F
    bits4_1 = (imm >> 1) & 0xF

    return (
        (bit12 << 31)
        | (bits10_5 << 25)
        | (rs2 << 20)
        | (rs1 << 15)
        | (funct3 << 12)
        | (bits4_1 << 8)
        | (bit11 << 7)
        | opcode
    )


# ------------------------------------------
# FORMATO U
# ------------------------------------------

def encode_u(rd, imm, opcode):
    # Campo de 20 bits: admite representacion
    # hexadecimal sin signo o valor con signo.
    check_range(
        imm, -(1 << 19), (1 << 20) - 1,
        "inmediato U"
    )

    return (
        ((imm & 0xFFFFF) << 12)
        | (rd << 7)
        | opcode
    )


# ------------------------------------------
# FORMATO J
# ------------------------------------------

def encode_j(rd, offset, opcode):
    check_range(
        offset, -1048576, 1048574,
        "desplazamiento"
    )

    if offset % 2 != 0:
        raise InstructionError(
            "desplazamiento J debe ser multiplo de 2"
        )

    imm = offset & 0x1FFFFF

    bit20 = (imm >> 20) & 1
    bits10_1 = (imm >> 1) & 0x3FF
    bit11 = (imm >> 11) & 1
    bits19_12 = (imm >> 12) & 0xFF

    return (
        (bit20 << 31)
        | (bits10_1 << 21)
        | (bit11 << 20)
        | (bits19_12 << 12)
        | (rd << 7)
        | opcode
    )


# ------------------------------------------
# CODIFICADOR PRINCIPAL
# ------------------------------------------

def encode_instruction(mnemonic, operands):
    """
    Convierte una instruccion RV32I base
    a un entero de 32 bits.

    B y J reciben desplazamientos numericos,
    calculados previamente desde las etiquetas.
    """

    mnemonic = mnemonic.strip().lower()

    info = get_instruction(mnemonic)
    validate_operand_count(mnemonic, operands)

    fmt = info["format"]
    opcode = info["opcode"]
    funct3 = info.get("funct3", 0)

    # Instrucciones de sistema
    if mnemonic == "ecall":
        return 0x00000073

    if mnemonic == "ebreak":
        return 0x00100073

    # FORMATO R
    if fmt == "R":
        rd = get_register(operands[0])
        rs1 = get_register(operands[1])
        rs2 = get_register(operands[2])

        return encode_r(
            rd, rs1, rs2,
            funct3, info["funct7"], opcode
        )

    # FORMATO I
    if fmt == "I":

        # Cargas y JALR
        if mnemonic in (
            "lb", "lh", "lw", "lbu", "lhu", "jalr"
        ):
            rd = get_register(operands[0])
            imm, rs1 = parse_memory_operand(operands[1])

            return encode_i(
                rd, rs1, imm, funct3, opcode
            )

        rd = get_register(operands[0])
        rs1 = get_register(operands[1])
        imm = parse_immediate(operands[2])

        # Desplazamientos de 5 bits
        if mnemonic in ("slli", "srli", "srai"):
            check_range(
                imm, 0, 31, "desplazamiento"
            )

            imm = (info["funct7"] << 5) | imm

        return encode_i(
            rd, rs1, imm, funct3, opcode
        )

    # FORMATO S
    if fmt == "S":
        rs2 = get_register(operands[0])
        imm, rs1 = parse_memory_operand(operands[1])

        return encode_s(
            rs2, rs1, imm, funct3, opcode
        )

    # FORMATO B
    if fmt == "B":
        rs1 = get_register(operands[0])
        rs2 = get_register(operands[1])
        offset = parse_immediate(operands[2])

        return encode_b(
            rs1, rs2, offset, funct3, opcode
        )

    # FORMATO U
    if fmt == "U":
        rd = get_register(operands[0])
        imm = parse_immediate(operands[1])

        return encode_u(rd, imm, opcode)

    # FORMATO J
    if fmt == "J":
        rd = get_register(operands[0])
        offset = parse_immediate(operands[1])

        return encode_j(rd, offset, opcode)

    raise InstructionError(
        f"formato no soportado para '{mnemonic}'"
    )


# ------------------------------------------
# CONVERSION A HEXADECIMAL
# ------------------------------------------

def to_hex(instruction):
    """Devuelve exactamente 8 digitos hexadecimales."""
    return f"{instruction:08x}"
