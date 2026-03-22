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

@dataclasses.dataclass
class Cmd():
	cmdline: str
	expect_success: bool = True

	@classmethod
	def parse_many(cls, multiline_cmd_str: str):
		cmds = multiline_cmd_str.strip("\r\n").split("\n")
		return [ cls(cmdline = cmd) for cmd in cmds ]


	@property
	def show_cmdline(self):
		return self.cmdline.replace("$digtick", "digtick")

	@property
	def hash(self):
		return hashlib.md5(self.cmdline.encode("utf-8")).hexdigest()

class CmdRunner():
	def __init__(self, cmds: list[Cmd], interactive: bool = False):
		self._cmds = cmds
		self._interactive = interactive
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
				print(f"Different {channel} output in {cmd.show_cmdline}")
				print(f"Reference: {reference_filename}")
				print(ref.decode("utf-8"))
				print(f"Produced : {produced_filename}")
				print(produced.decode("utf-8"))
				raise RuntimeError(f"Command returned different output than expected: {cmd.show_cmdline}")
		except FileNotFoundError:
			print(f"No {channel} reference found for command: {cmd.show_cmdline}")
			if self._interactive:
				print(f"This was produced on {channel}:")
				print(produced.decode("utf-8"))
				yn = input("Output OK (y/n)? ")
				if (yn.lower() == "y") or (yn == ""):
					with open(reference_filename, "wb") as f:
						f.write(produced)
			else:
				raise

	def _run(self, cmd: Cmd):
		print(cmd)
		cmdline = cmd.cmdline.replace("$digtick", "digtick")
		proc = subprocess.run(cmdline, shell = True, check = False, capture_output = True)
		if cmd.expect_success and (proc.returncode != 0):
			raise RuntimeError(f"Command expected success but failed: {cmdline}")
		elif (not cmd.expect_success) and (proc.returncode == 0):
			raise RuntimeError(f"Command expected failure but returned successful: {cmdline}")

		if cmd.expect_success:
			produced_stdout_filename = f"{self._produced_output_dir}{cmd.hash}-stdout.txt"
			produced_stderr_filename = f"{self._produced_output_dir}{cmd.hash}-stderr.txt"
			reference_stdout_filename = f"{self._reference_output_dir}{cmd.hash}-stdout.txt"
			reference_stderr_filename = f"{self._reference_output_dir}{cmd.hash}-stderr.txt"

			self._compare(cmd, "stdout", proc.stdout, produced_stdout_filename, reference_stdout_filename)
			self._compare(cmd, "stderr", proc.stderr, produced_stderr_filename, reference_stderr_filename)


	def run(self):
		for cmd in self._cmds:
			self._run(cmd)

cmds = [ ]
cmds += Cmd.parse_many("""
$digtick parse "A B C"
$digtick parse -F implicit-and=0 "A B C"
$digtick parse -f text "A B C"
""")
for expr_fmt in [ "text", "tex", "typst", "dot", "internal" ]:
	cmds.append(Cmd(f"$digtick parse -f {expr_fmt} \"A B C\""))
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

CmdRunner(cmds, interactive = True).run()
