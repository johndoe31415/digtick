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

from .MultiCommand import BaseAction
from .ValueTable import ValueTable
from .Tools import open_file
from .Exceptions import OutputValueMissingException

class ActionStateTransitions(BaseAction):
	def _process_next_cycle(self, start_value: int):
		cycle_values = [ start_value ]
		cur_value = start_value
		while cur_value in self._remaining:
			self._remaining.remove(cur_value)
			next_value = [ self._vt.at_index(cur_value, output_varname) for output_varname in self._output_vars ]
			next_value = sum(value << bitpos for (bitpos, value) in enumerate(reversed(next_value)))
			cycle_values.append(next_value)
			cur_value = next_value

		if self._args.output_format == "text":
			first_index = cycle_values.index(cycle_values[-1])
			if first_index == 0:
				tstr = f"full cycle length {len(cycle_values) - 1}"
			else:
				tail_length = first_index
				cycle_length = len(cycle_values) - tail_length - 1
				tstr = f"Rho graph with tail length {tail_length}, cycle length {cycle_length}"
			print(f"{' → '.join(str(x) for x in cycle_values)}  {tstr}")
		elif self._args.output_format == "dot":
			for value in cycle_values:
				print(f"	n{value} [ label=\"{value:0{len(self._output_vars)}b}\\n{value}\" ];")
			for (value, next_value) in zip(cycle_values, cycle_values[1:]):
				print(f"	n{value} -> n{next_value};")

	def run(self):
		with open_file(self._args.filename) as f:
			self._vt = ValueTable.parse_from_file(f, set_undefined_values_to = "forbidden")

		for varname in self._vt.input_variable_names:
			if not self._vt.has_output_named(varname + "'"):
				raise OutputValueMissingException(f"Every input needs a nextstate input (the label plus an apostrophe). Found input {varname} but no output {varname}'")
		self._output_vars = [ varname + "'" for varname in self._vt.input_variable_names ]
		self._remaining = set(range(1 << len(self._vt.input_variable_names)))
		if self._args.output_format == "text":
			print(f"{', '.join(self._vt.input_variable_names)} → {', '.join(self._output_vars)}")

		if self._args.output_format == "dot":
			print("digraph g {")
			print("	layout=circo;")
			print("	overlap=false;")
			print("	splines=true;")
			print("	node [shape=circle];")
		while len(self._remaining) > 0:
			self._process_next_cycle(min(self._remaining))
		if self._args.output_format == "dot":
			print("}")
