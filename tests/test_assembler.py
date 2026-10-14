import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent

class IntegrationTests(unittest.TestCase):
    def test_suma_del_enunciado(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'suma.hex'
            result = self.cli(ROOT / 'tests' / 'suma.asm', output)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(output.read_bytes(), b'00a00513\n00000593\n00050863\n00a585b3\nfff50513\nff5ff06f\n0000006f\n')

    def cli(self, *args):
        return subprocess.run([sys.executable, str(ROOT / 'assembler.py'), *map(str, args)], capture_output=True, text=True)

    def test_suma_and_pc(self):
        programs = [
            ('li t0, 10\nli t1, 20\nadd t2, t0, t1\necall', '00a00293\n01400313\n006283b3\n00000073\n'),
            ('li x5, 4097\nbeq x0, x0, end\nnop\nend: j end', '000012b7\n00128293\n00000463\n00000013\n0000006f\n'),
            ('# vacío', ''),
        ]
        with tempfile.TemporaryDirectory(prefix='fase 8 ') as directory:
            source, output = Path(directory)/'suma.asm', Path(directory)/'suma.hex'
            for program, expected in programs:
                source.write_text(program, encoding='utf-8')
                result = self.cli(source, output)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(output.read_bytes(), expected.encode('ascii'))

    def test_errors_without_output(self):
        programs = ['addi x1, x0, 4096', 'add x32, x0, x1', 'lw x1, (x2', 'j missing', 'a: nop\na: nop', 'foo x1']
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory)/'bad.asm', Path(directory)/'bad.hex'
            for program in programs:
                for existing in (False, True):
                    if output.exists():
                        output.unlink()
                    if existing:
                        output.write_bytes(b'previous')
                    source.write_text(program, encoding='utf-8')
                    result = self.cli(source, output)
                    self.assertEqual(result.returncode, 1)
                    self.assertIn('error:', result.stderr)
                    self.assertNotIn('Traceback', result.stderr)
                    self.assertEqual(output.exists(), existing)
                    if existing:
                        self.assertEqual(output.read_bytes(), b'previous')

    def test_cli_and_io(self):
        for args, code in [((),2), (('one',),2), (('a','b','c'),2), (('--help',),0)]:
            self.assertEqual(self.cli(*args).returncode, code)
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory)/'input.asm', Path(directory)/'output.hex'
            self.assertEqual(self.cli(source, output).returncode, 1)
            self.assertFalse(output.exists())
            source.write_text('nop', encoding='utf-8')
            self.assertEqual(self.cli(source, source).returncode, 1)
            self.assertEqual(source.read_text(), 'nop')
            self.assertEqual(self.cli(source, Path(directory)/'missing'/'out.hex').returncode, 1)
            self.assertEqual(self.cli(source, directory).returncode, 1)
            self.assertEqual(list(Path(directory).glob('.assembler-*')), [])

if __name__ == '__main__':
    unittest.main()
