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
	def hash(self):
		return hashlib.md5(self.cmdline.encode("utf-8")).hexdigest()

class CmdRunner():
	def __init__(self, cmds: list[Cmd], interactive: bool = False):
		self._cmds = cmds
		self._interactive = interactive
		self._reference_output_dir = "scripts/reference/"
		self._produced_output_dir = "/tmp/output/"
		os.makedirs(self._produced_output_dir, exist_ok = True)

	def _run(self, cmd: Cmd):
		print(cmd)
		cmdline = cmd.cmdline.replace("$digtick", "digtick")
		proc = subprocess.run(cmdline, shell = True, check = False, capture_output = True)
		if cmd.expect_success and (proc.returncode != 0):
			raise RuntimeError(f"Command expected success but failed: {cmdline}")

		produced_output_filename = f"{self._produced_output_dir}{cmd.hash}.txt"
		reference_filename = f"{self._reference_output_dir}{cmd.hash}.txt"
		with open(produced_output_filename, "wb") as f:
			f.write(proc.stdout)

		try:
			with open(reference_filename, "rb") as f:
				ref = f.read()
			if ref != proc.stdout:
				print(f"Different output in {cmdline}")
				print(f"Reference: {reference_filename}")
				print(ref.decode("utf-8"))
				print(f"Produced : {produced_output_filename}")
				print(proc.stdout.decode("utf-8"))
				raise RuntimeError(f"Command returned different output than expected: {cmdline}")
		except FileNotFoundError:
			print(f"No reference found for command: {cmdline}")
			if self._interactive:
				print("This was produced:")
				print(proc.stdout.decode("utf-8"))
				yn = input("Output OK (y/n)? ")
				if (yn.lower() == "y") or (yn == ""):
					with open(reference_filename, "wb") as f:
						f.write(proc.stdout)
			else:
				raise

	def run(self):
		for cmd in self._cmds:
			self._run(cmd)

cmds = [ ]
cmds += Cmd.parse_many("""
$digtick parse "A B C"
$digtick parse -F implicit-and=0 "A B C"
$digtick parse -f text "A B C"
""")
CmdRunner(cmds, interactive = True).run()
