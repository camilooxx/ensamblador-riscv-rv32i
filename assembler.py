
import sys
from parser import parse_file, ParserError


def main():
    if len(sys.argv) != 3:
        print("Uso: python assembler.py entrada.asm salida.hex")
        sys.exit(1)

    archivo_entrada = sys.argv[1]
    archivo_salida = sys.argv[2]

    try:
        lines = parse_file(archivo_entrada)

        print("=== ANALIZADOR RISC-V RV32I ===")
        print(f"Entrada: {archivo_entrada}")
        print(f"Salida futura: {archivo_salida}")
        print()

        for line in lines:
            print(f"Línea {line.number}:")
            print(f"  Etiqueta:     {line.label}")
            print(f"  Directiva:    {line.directive}")
            print(f"  Instrucción:  {line.instruction}")
            print(f"  Operandos:    {line.operands}")
            print()

        print("Análisis sintáctico completado.")
        print("La generación hexadecimal se implementará después.")

    except ParserError as error:
        print(
            f"{archivo_entrada}:{error.line_number}: "
            f"error: {error}",
            file=sys.stderr
        )
        sys.exit(1)

    except OSError as error:
        print(f"Error al leer el archivo: {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
