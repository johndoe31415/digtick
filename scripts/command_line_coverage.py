#!/usr/bin/python3
#	digtick - Digital logic design toolkit: simplify, minimize and transform Boolean expressions, draw KV-maps, etc.
#	Copyright (C) 2022-2026 Johannes Bauer
#
#	This file is part of digtick.
#
#	digtick is free software; you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation; this program is ONLY licensed under
#	version 3 of the License, later versions are explicitly excluded.
#
#	digtick is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with digtick; if not, write to the Free Software
#	Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#	Johannes Bauer <JohannesBauer@gmx.de>

import os
import dataclasses
import subprocess
import hashlib
import sys
from FriendlyArgumentParser import FriendlyArgumentParser

@dataclasses.dataclass
class Cmd():
	cmdline: str
	expect_success: bool = True
	output_deterministic: bool = True

	@classmethod
	def parse_many(cls, multiline_cmd_str: str):
		cmds = multiline_cmd_str.strip("\r\n").split("\n")
		parsed_cmds = [ ]
		for cmd in cmds:
			cmd = cmd.strip()
			if cmd == "":
				continue

			if cmd.startswith("-"):
				parsed_cmds.append(cls(cmdline = cmd[1:], expect_success = False))
			else:
				parsed_cmds.append(cls(cmdline = cmd))
		return parsed_cmds

	@property
	def regular_cmdline(self):
		return self.cmdline.replace("$digtick", "digtick")

	@property
	def manual_cmdline(self):
		return self.cmdline.replace("$digtick", "python3 -m digtick.__main__")

	@property
	def coverage_cmdline(self):
		return self.cmdline.replace("$digtick", "coverage run -a --source digtick --omit=tpg.py,PrefixMatcher.py,RandomDist.py,TableFormatter.py,MultiCommand.py,FriendlyArgumentParser.py -m digtick.__main__")

	@property
	def hash(self):
		return hashlib.md5(self.cmdline.encode("utf-8")).hexdigest()

class CmdRunner():
	def __init__(self, args):
		self._args = args
		self._reference_output_dir = "scripts/reference/"
		self._produced_output_dir = "/tmp/output/"
		os.makedirs(self._produced_output_dir, exist_ok = True)

	def _compare(self, cmd: Cmd, channel: str, produced: bytes, produced_filename: str, reference_filename: str):
		with open(produced_filename, "wb") as f:
			f.write(produced)

		try:
			with open(reference_filename, "rb") as f:
				ref = f.read()
			if ref != produced:
				print(f"Different {channel} output in {cmd.regular_cmdline}")
				print(f"Reference: {reference_filename}")
				print(ref.decode("utf-8"))
				print(f"Produced : {produced_filename}")
				print(produced.decode("utf-8"))
				if not self._args.accept_all:
					print()
					yn = input(f"{channel} OK (y/n)? ")
				else:
					yn = "y"
				if (yn.lower() == "y") or (yn == ""):
					with open(reference_filename, "wb") as f:
						f.write(produced)
				else:
					raise RuntimeError(f"Command returned different output than expected: {cmd.regular_cmdline}")
		except FileNotFoundError:
			print(f"No {channel} reference found for command: {cmd.regular_cmdline}")
			if self._args.interactive or self._args.accept_all:
				if not self._args.accept_all:
					print(f"This was produced on {channel}:")
					print(produced.decode("utf-8"))
					yn = input(f"{channel} OK (y/n)? ")
				else:
					yn = "y"
				if (yn.lower() == "y") or (yn == ""):
					with open(reference_filename, "wb") as f:
						f.write(produced)
			else:
				raise

	def _run(self, cmd: Cmd):
		print(cmd.regular_cmdline)
		cmdline = cmd.manual_cmdline if self._args.no_coverage else cmd.coverage_cmdline
		proc = subprocess.run(cmdline, shell = True, check = False, capture_output = True)
		if cmd.expect_success and (proc.returncode != 0):
			raise RuntimeError(f"Command expected success but failed: {cmd.regular_cmdline}")
		elif (not cmd.expect_success) and (proc.returncode == 0):
			raise RuntimeError(f"Command expected failure but returned successful: {cmd.regular_cmdline}")

		if cmd.expect_success and cmd.output_deterministic:
			produced_stdout_filename = f"{self._produced_output_dir}{cmd.hash}-stdout.txt"
			produced_stderr_filename = f"{self._produced_output_dir}{cmd.hash}-stderr.txt"
			reference_stdout_filename = f"{self._reference_output_dir}{cmd.hash}-stdout.txt"
			reference_stderr_filename = f"{self._reference_output_dir}{cmd.hash}-stderr.txt"

			self._compare(cmd, "stdout", proc.stdout, produced_stdout_filename, reference_stdout_filename)
			self._compare(cmd, "stderr", proc.stderr, produced_stderr_filename, reference_stderr_filename)


	def run(self, cmds: list[Cmd]):
		for cmd in cmds:
			self._run(cmd)

cmds = [ ]
cmds += Cmd.parse_many("""
$digtick parse "A B C"
$digtick parse -F implicit-and=0 "A B C"
$digtick parse -F pretty "<A + B> C"
$digtick parse -f tex -F math-operators "<A + B> C"
$digtick parse -f text "A B C"
""")
for expr_fmt in [ "text", "tex", "typst", "dot", "internal" ]:
	cmds.append(Cmd(f"$digtick parse -f {expr_fmt} \"A B C\""))
	cmds.append(Cmd(f"$digtick parse -f {expr_fmt} \"A B C + !A !B !C + (!1 + !0) @ Z % W\""))

expr = "A B C + !A !B !C + (!1 + !0) @ Z % W"
cmds.append(Cmd(f"$digtick parse -f tex -F math-operators \"{expr}\""))
cmds.append(Cmd(f"$digtick parse -f tex -F math-operators -F math-constants \"{expr}\""))
cmds.append(Cmd(f"$digtick parse -f tex -F math-operators -F math-constants -F use-mathrm=0 \"{expr}\""))
cmds.append(Cmd(f"$digtick parse -f tex -F math-operators -F math-constants -F use-mathrm=0 -F implicit-and=0 \"{expr}\""))
cmds.append(Cmd(f"$digtick parse -f typst -F math-operators \"{expr}\""))
cmds.append(Cmd(f"$digtick parse -f typst -F math-operators -F math-constants \"{expr}\""))
cmds.append(Cmd(f"$digtick parse -f typst -F math-operators -F math-constants -F literals-upright=0 \"{expr}\""))
cmds.append(Cmd(f"$digtick parse -f typst -F math-operators -F math-constants -F literals-upright=0 -F implicit-and=0 \"{expr}\""))

cmds.append(Cmd("""
(
	echo "A B C"
	echo "B C A"
	echo "# test that comment works"
) | $digtick parse --read-as-filename --validate-equivalence -
"""))
cmds.append(Cmd("""
(
	echo "A B C"
	echo "B C A"
	echo "# test that comment works"
	echo "A !B C"
) | $digtick parse --read-as-filename --validate-equivalence -
""", expect_success = False))

cmds.append(Cmd("$digtick make-table 'A B C' '!B !C' >/tmp/table1"))
for tbl_fmt in [ "text", "tex", "typst", "compact", "logisim" ]:
	cmds.append(Cmd(f"cat /tmp/table1 | $digtick print-table -f {tbl_fmt}"))
cmds.append(Cmd("cat /tmp/table1 | $digtick print-table -f text -F pretty"))
cmds.append(Cmd("cat /tmp/table1 | $digtick print-table -f text -F pretty=true"))
cmds.append(Cmd("cat /tmp/table1 | $digtick print-table -f text -F pretty=1"))
cmds.append(Cmd("cat /tmp/table1 | $digtick print-table -f text -F pretty=0"))
cmds.append(Cmd("cat /tmp/table1 | $digtick print-table -f text -F pretty=slop", expect_success = False))
cmds.append(Cmd("cat /tmp/table1 | $digtick print-table -f text -F blah=true", expect_success = False))
cmds.append(Cmd("cat /tmp/table1 | $digtick print-table -f logisim -F pretty", expect_success = False))
cmds.append(Cmd("cat /tmp/table1 | $digtick print-table -f tex -F layout=wrong", expect_success = False))
for tbl_fmt in [ "tex", "typst" ]:
	for layout in [ "horizontal", "vertical" ]:
		cmds.append(Cmd(f"cat /tmp/table1 | $digtick print-table -f {tbl_fmt} -F layout={layout}"))


cmds += Cmd.parse_many("""
$digtick print-table -L examples/logisim_full_adder.txt

$digtick make-table 'A B + !B C' >/tmp/table2
$digtick make-table 'A B + !B C + A !B !C' >/tmp/table3
$digtick diff-table /tmp/table2 /tmp/table3
-echo ':A,B,C:Z:5404' | $digtick diff /tmp/table2
-echo ':A,D,C:Y:5404' | $digtick diff /tmp/table2

$digtick kv /tmp/table1
$digtick kv --render-indices /tmp/table1
-$digtick kv -o P /tmp/table1
$digtick kv -r /tmp/table1
$digtick kv -x 1 -y 2 -X -Y -d BCA /tmp/table1
$digtick kv -x 1 -y 2 -X -Y -d C,B,A /tmp/table1
-cat /tmp/table1 | head -n -1 | $digtick kv -x 1 -y 2 -X -Y -d BCA
cat /tmp/table1 | head -n -1 | $digtick kv -x 1 -y 2 -X -Y -d BCA --unused-value-is '*'
-$digtick kv -x 1 -y 2 -X -Y -d BCAA /tmp/table1
-$digtick kv -x 1 -y 2 -X -Y -d BCAX /tmp/table1
$digtick kv -x 1 -y 2 -X -Y -d BCA -O /tmp/kv.svg /tmp/table1
$digtick kv --render-indices -x 1 -y 2 -X -Y -d BCA -O /tmp/kv.svg /tmp/table1

$digtick synth /tmp/table1
$digtick synth /tmp/table1 --show-all-solutions

-$digtick sat /tmp/table1 'A B'
$digtick sat /tmp/table1 'A B C'

-$digtick eq 'A B C' 'A B !C'
$digtick eq 'A(B C)' 'B(A C)'
""")

cmds.append(Cmd("$digtick random-expr 4 10", output_deterministic = False))
cmds += Cmd.parse_many("""
$digtick random-expr --prng-seed foobar 4 10
$digtick random-expr --prng-seed foobar --allow-nand-nor-xor 4 10
""")



cmds.append(Cmd("$digtick random-table 4", output_deterministic = False))
cmds += Cmd.parse_many("""
$digtick random-table --prng-seed foobar 4
$digtick random-table --prng-seed foobar -1 100 -0 0 4
$digtick random-table --prng-seed foobar -1 100 -0 0 -o Z 4
-$digtick random-table -1 100 -0 50 4
""")

cmds += Cmd.parse_many("""
$digtick transform -t simplify 'A C B'
$digtick transform -t nand 'A ^ B'
$digtick transform -t nor 'A ^ B'
$digtick transform -t nand -t nor -t nand 'A ^ B'
$digtick transform -t simplify '(A + 1)(B & 0)((1))'
$digtick transform -t simplify '(A + 1)(B & 0)((1)) + (!B !C !A) + (A + A) + (A A) + (X @ 1 @ 1)'
$digtick transform -t simplify '-((A + 1)(B & 0)((1)) + (!B !C !A) + (A + A) + (A A) + (-X @ 1 @ 1))(C 1)(D + 0)((X)+(X))((Y)(Y))(Z % 0 % 0)(K + !K)'
$digtick transform --prng-seed FOOBAR -t shuffle '-((A + 1)(B & 0)((1)) + (!B !C !A) + (A + A) + (A A) + (-X @ 1 @ 1))(C 1)(D + 0)((X)+(X))((Y)(Y))(Z % 0 % 0)(K + !K)'
$digtick transform -t sort '-((A + 1)(B & 0)((1)) + (!B !C !A) + (A + A) + (A A) + (-X @ 1 @ 1))(C 1)(D + 0)((X)+(X))((Y)(Y))(Z % 0 % 0)(K + !K)'
""")
cmds.append(Cmd("$digtick transform -t shuffle '-((A + 1)(B & 0)((1)) + (!B !C !A) + (A + A) + (A A) + (-X @ 1 @ 1))(C 1)(D + 0)((X)+(X))((Y)(Y))(Z % 0 % 0)(K + !K)'", output_deterministic = False))


for dev in [ "sr-nand-ff", "d-ff", "jk-ff", "jk-ms-ff" ]:
	cmds += Cmd.parse_many(f"""
		$digtick dtd-create --random-seed 12345 -d {dev}
		$digtick dtd-create --random-seed 23456 -n -d {dev}
	""")


cmds += Cmd.parse_many("""
$digtick dtd-create -i >/tmp/dtd
$digtick dtd-create --random-seed blubb -d jk-ff "J=00001111000011110000111100001111"
-$digtick dtd-create --random-seed blubb -d jk-ff "J=000011110000111100001111000"
""")

cmds += Cmd.parse_many("""
rm -f /tmp/dtd.svg; $digtick dtd-render -o /tmp/dtd.svg /tmp/dtd
-touch /tmp/dtd.svg; $digtick dtd-render -o /tmp/dtd.svg /tmp/dtd
touch /tmp/dtd.svg; $digtick dtd-render -f -o /tmp/dtd.svg /tmp/dtd
""")

cmds += Cmd.parse_many("""
$digtick sim-combinatorial src/digtick/tests/data/awful.circ >/tmp/awful.txt

$digtick sim-sequential -s FF1,FF2,FF3,FF4 src/digtick/tests/data/stateful.circ >/tmp/state_table.txt
$digtick sim-sequential -s B4,B3,B2,B1,B0 -n main_gates examples/counter_5bit.circ >/tmp/state_table2.txt

$digtick analyze-sequential -vv /tmp/state_table.txt
$digtick analyze-sequential -vv /tmp/state_table2.txt
$digtick analyze-sequential -f dot /tmp/state_table.txt
$digtick analyze-sequential -f json /tmp/state_table.txt
echo ":FF1,FF2,FF3,FF4,FF5:FF1',FF2',FF3',FF4',FF5':5555000055550000,5555000000005555,4455440044554400,55005500550055,4051514040515140" | $digtick analyze-sequential
echo ":FF1,FF2,FF3,FF4,FF5:FF1',FF2',FF3',FF4',FF5':5555000055550000,5555000000005555,4455440044554400,55005500550055,4051514040515140" | $digtick analyze-sequential -f dot
-$digtick analyze-sequential /tmp/table1

-$digtick mutate src/digtick/tests/data/invgate.circ
$digtick mutate -m G src/digtick/tests/data/invgate.circ
$digtick mutate -m G:c=AND src/digtick/tests/data/invgate.circ
$digtick mutate -m G:c=AND,c=OR src/digtick/tests/data/invgate.circ
-$digtick mutate -m G:inv=foo src/digtick/tests/data/invgate.circ
-$digtick mutate -m G:comb=foo src/digtick/tests/data/invgate.circ
-$digtick mutate -m G:randcomb=foo src/digtick/tests/data/invgate.circ
-$digtick mutate -m G:foo=bar src/digtick/tests/data/invgate.circ
-$digtick mutate -m G:comb=999 src/digtick/tests/data/invgate.circ
$digtick mutate -m G:inv=1 src/digtick/tests/data/invgate.circ
$digtick mutate -m G:inv=1,randcomb=3 src/digtick/tests/data/invgate.circ
$digtick mutate -m G:inv=1,comb=1,comb=2 --prefix foobar src/digtick/tests/data/invgate.circ
$digtick mutate -r G1,G2,G3,G4,G5,G6 examples/mutate_me.circ
""")

parser = FriendlyArgumentParser(description = "Run the digtick command line tool and verify it produces correct output.")
parser.add_argument("-c", "--no-coverage", action = "store_true", help = "Do not collect coverage information")
parser.add_argument("-i", "--interactive", action = "store_true", help = "Interactive query if output is acceptable")
parser.add_argument("-a", "--accept-all", action = "store_true", help = "When deviations from expected test output occur, just accept them")
args = parser.parse_args(sys.argv[1:])
CmdRunner(args).run(cmds)
