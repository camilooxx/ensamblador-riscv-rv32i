
import re
from dataclasses import dataclass


@dataclass
class ParsedLine:
    number: int
    label: str | None = None
    directive: str | None = None
    instruction: str | None = None
    operands: list[str] | None = None


LABEL_PATTERN = re.compile(r"^[A-Za-z_.$][A-Za-z0-9_.$]*$")
LABEL_PREFIX = re.compile(r"^([A-Za-z_.$][A-Za-z0-9_.$]*):")


class ParserError(Exception):
    def __init__(self, line_number, message):
        self.line_number = line_number
        super().__init__(message)


def remove_comment(line):
    """Elimina comentarios sin modificar el texto entre comillas."""
    in_string = False
    escaped = False

    for i, char in enumerate(line):
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
        elif char == '"':
            in_string = True
        elif char == "#":
            return line[:i]

    return line


def split_operands(text, line_number):
    """Separa operandos respetando cadenas y paréntesis."""
    if not text.strip():
        return []

    operands = []
    current = []
    in_string = False
    escaped = False
    depth = 0

    for char in text:
        if in_string:
            current.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
        elif char == '"':
            in_string = True
            current.append(char)
        elif char == "(":
            depth += 1
            current.append(char)
        elif char == ")":
            depth -= 1
            if depth < 0:
                raise ParserError(line_number, "paréntesis incorrectos")
            current.append(char)
        elif char == "," and depth == 0:
            operand = "".join(current).strip()
            if not operand:
                raise ParserError(line_number, "operando vacío")
            operands.append(operand)
            current = []
        else:
            current.append(char)

    if in_string:
        raise ParserError(line_number, "cadena sin cerrar")
    if depth != 0:
        raise ParserError(line_number, "paréntesis sin cerrar")

    operand = "".join(current).strip()
    if not operand:
        raise ParserError(line_number, "operando vacío")

    operands.append(operand)
    return operands


def parse_line(line, line_number):
    """Analiza una línea de ensamblador."""
    line = remove_comment(line).strip()

    if not line:
        return None

    result = ParsedLine(number=line_number, operands=[])

    # Extraer una etiqueta opcional
    match = LABEL_PREFIX.match(line)
    if match:
        result.label = match.group(1)
        line = line[match.end():].strip()

    if not line:
        return result

    parts = line.split(None, 1)
    name = parts[0].lower()
    operand_text = parts[1] if len(parts) > 1 else ""

    result.operands = split_operands(operand_text, line_number)

    if name.startswith("."):
        result.directive = name
    else:
        result.instruction = name

    return result


def parse_file(filename):
    """Lee un archivo ASM y devuelve sus líneas analizadas."""
    parsed = []

    with open(filename, "r", encoding="utf-8") as file:
        for number, line in enumerate(file, start=1):
            result = parse_line(line, number)
            if result is not None:
                parsed.append(result)

    return parsed
