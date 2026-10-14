"""Ensamblador RV32I: una palabra hexadecimal por línea."""
import argparse
import os
from pathlib import Path
import sys
import tempfile
from encoder import to_hex
from errors import validate_source


def assemble(input_path, output_path):
    source, target = Path(input_path), Path(output_path)
    if source.resolve() == target.resolve() or (source.exists() and target.exists() and os.path.samefile(source, target)):
        raise ValueError('entrada y salida deben ser archivos distintos')
    words, collector = validate_source(source)
    if collector.has_errors():
        return None, collector
    content = ''.join(to_hex(word) + '\n' for word in words)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='ascii', newline='\n', dir=target.parent, prefix='.assembler-', suffix='.tmp', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(content)
        os.replace(temporary, target)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
    return len(words), collector


def main(argv=None):
    cli = argparse.ArgumentParser(description='Ensambla RV32I y genera un HEX de instrucciones.')
    cli.add_argument('entrada', help='archivo fuente ASM')
    cli.add_argument('salida', help='archivo HEX de salida')
    args = cli.parse_args(argv)
    try:
        count, collector = assemble(args.entrada, args.salida)
    except (OSError, ValueError) as error:
        print(f'error: {error}', file=sys.stderr)
        return 1
    if collector.has_errors():
        print(collector.report(), file=sys.stderr)
        return 1
    print(f'Ensamblado completado: {count} instrucciones -> {args.salida}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
