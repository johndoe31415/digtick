#	digtool - Tool to compute and simplify problems in digital systems
#	Copyright (C) 2022-2026 Johannes Bauer
#
#	This file is part of digtool.
#
#	digtool is free software; you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation; this program is ONLY licensed under
#	version 3 of the License, later versions are explicitly excluded.
#
#	digtool is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with digtool; if not, write to the Free Software
#	Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#	Johannes Bauer <JohannesBauer@gmx.de>

import re
import itertools
from .TableFormatter import Table, CellFormatter

class ValueTable():
	_TABLE_SEP = re.compile(r"\t+")

	def __init__(self, input_variable_names: list[str], output_values: list[bool | None]):
		if len(output_values) != 2 ** len(input_variable_names):
			raise ValueError(f"For {len(input_variable_names)} variables there are {2 ** len(input_variable_names)} output values expected, but {len(output_values)} were found.")
		self._input_variable_names = input_variable_names
		self._output_values = output_values

	@property
	def input_variable_names(self):
		return self._input_variable_names

	@property
	def input_variable_count(self):
		return len(self._input_variable_names)

	@classmethod
	def parse_from_file(self, f: "_io.TextIOWrapper", unused_value: int | None = -1):
		assert(unused_value in [ None, 0, 1, -1 ])
		for (lineno, line) in enumerate(f, 1):
			line = line.strip("\r\n\t ")
			tokens = self._TABLE_SEP.split(line)
			if lineno == 1:
				variables = tokens
				output_values = [ unused_value ] * (2 ** len(variables))
			else:
				if len(tokens) != len(variables) + 1:
					raise ValueError(f"Syntax error when parsing truth table in line {lineno}: expected {len(variables) + 1} tokens, but saw {len(tokens)}")
				input_value_dict = { varname: int(token) for (varname, token) in zip(variables, tokens) }
				output_value = tokens[-1]
				if output_value == "*":
					output_value = None
				else:
					output_value = int(output_value)
				index = self._dict2index(input_value_dict, variables)
				output_values[index] = output_value
		if (unused_value == -1) and (-1 in output_values):
			# If strict parsing required, all values must be explicitly set
			raise ValueError("Strict parsing was requested and not all input patterns were explicitly specified.")
		return ValueTable(input_variable_names = variables, output_values = output_values)

	@classmethod
	def create_from_expression(self, expression: "ParsedExpression", dc_expression: "ParsedExpression | None" = None):
		output_values = [ ]
		for (inputs, output) in expression.table():
			if (dc_expression is not None) and (dc_expression.evaluate(inputs) != 0):
				# Don't care
				output = None
			output_values.append(output)
		return ValueTable(expression.variables, output_values = output_values)

	def __iter__(self):
		for (inputs, output) in zip(itertools.product([0, 1], repeat = self.input_variable_count), self._output_values):
			input_dict = { varname: input_value for (varname, input_value) in zip(self.input_variable_names, inputs) }
			yield (input_dict, output)

	def print(self):
		table = Table()
		header = { varname: varname for varname in self.input_variable_names }
		header["="] = " "
		table.add_row(header)
		table.add_separator_row()

		for (inputs, output) in self:
			row = inputs
			if output is None:
				row["="] = "*"
			else:
				row["="] = output
			table.add_row(row)

		table.print(*(list(self._input_variable_names) + [ "=" ]))

	def print_native(self):
		print("\t".join(self.input_variable_names))
		for (inputs, output) in self:
			row = [ str(inputs.get(varname)) for varname in self.input_variable_names ]
			if output is None:
				row.append("*")
			else:
				row.append(str(output))
			print("\t".join(row))

	@staticmethod
	def _gray_code(x: int) -> int:
		return x ^ (x >> 1)

	@staticmethod
	def _inv_gray_code(x: int) -> int:
		result = 0
		while x != 0:
			result ^= x
			x >>= 1
		return result

	@staticmethod
	def _dict2index(input_var_dict: dict, variable_names: list[str]) -> int:
		index = 0
		for (i, varname) in enumerate(variable_names):
			bitno = len(variable_names) - 1 - i
			if input_var_dict[varname]:
				index += (1 << bitno)
		return index

	def at(self, input_var_dict: dict) -> int | None:
		return self._output_values[self._dict2index(input_var_dict, self.input_variable_names)]

	def print_kv(self, variable_order: list[str] | None = None, x_offset: int = 0, y_offset: int = 0, x_invert: bool = False, y_invert: bool = False, row_heavy: bool = True):
		def _create_kv_dict(var_names: list[str], offset: int = 0, invert_direction: bool = False):
			result = [ ]
			var_count = len(var_names)
			for i in range(2 ** var_count):
				idx = (-i + offset) if invert_direction else (i + offset)
				gc = self._gray_code(idx % (2 ** var_count))
				values = { var_names[i]: int((gc & (1 << i)) != 0) for i in range(var_count) }
				result.append(values)
			return result

		def _overline(text: str) -> str:
			return "".join(char + "\u0305" for char in text)

		def _dict2str(var_dict: dict) -> str:
			return " ".join(_overline(varname) if (value == 0) else varname for (varname, value) in sorted(var_dict.items()))

		variables = self.input_variable_names if (variable_order is None) else variable_order
		if row_heavy:
			x_var_cnt = len(variables) // 2
		else:
			x_var_cnt = len(variables + 1) // 2
		x_vars = variables[:x_var_cnt]
		y_vars = variables[x_var_cnt:]

		x_values = _create_kv_dict(x_vars, x_offset, invert_direction = x_invert)
		y_values = _create_kv_dict(y_vars, y_offset, invert_direction = y_invert)

		table = Table()
		table.format_columns({ f"x{x}": CellFormatter.basic_center() for x in range(len(x_values)) })

		heading = { "_": " " }
		for (x, xvalue) in enumerate(x_values):
			heading[f"x{x}"] = _dict2str(xvalue)
		table.add_row(heading)

		for (y, yvalue) in enumerate(y_values):
			row = { "_": _dict2str(yvalue) }
			cell_value = dict(yvalue)
			for (x, xvalue) in enumerate(x_values):
				cell_value.update(xvalue)
				row[f"x{x}"] = self.at(cell_value)
			row = { key: value if (value is not None) else "*" for (key, value) in row.items() }

			table.add_separator_row()
			table.add_row(row)

		table.print(*([ "_" ] + [ f"x{x}" for x in range(len(x_values)) ]))


if __name__ == "__main__":
	from .ExpressionParser import parse_expression
	vt = ValueTable.create_from_expression(parse_expression("A B + C !D + (A (C + !C))"), dc_expression =  parse_expression("A !B !C"))
	vt.print()
	vt.print_kv()
