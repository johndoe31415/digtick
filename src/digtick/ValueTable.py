#	digtick - Digital systems toolkit: simplify, minimize and transform Boolean expressions, draw KV-maps, etc.
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

import re
import enum
import itertools
from .TableFormatter import Table, CellFormatter

class CompactStorage():
	class Entry(enum.IntEnum):
		Low = 0
		High = 1
		DontCare = 2
		Undefined = 3

	def __init__(self, variable_count: int, intial_value: int | None = None):
		self._variable_count = variable_count
		if initial_value is not None:
			# Initialize all values to undefined
			self._value = (2 ** (2 * self.table_entry_count)) - 1
		else:
			self._value = initial_value

	@property
	def table_entry_count(self):
		return 2 ** self._variable_count

	@property
	def has_undefined_values(self):
		return any(value == TableEntry.Undefined for value in self)

	@classmethod
	def from_string(cls, variable_count: int, compact_table_str: str):
		return cls(variable_count = variable_count, initial_value = int(compact_table_str, 16))

	def to_string(self):
		return f"{self._value:x}"

	def __iter__(self):
		value = self._value
		for _ in range(self.table_entry_count):
			yield self.Entry(value & 3)
			value >>= 2

	def __setitem__(self, index: int, value: TableEntry):
		assert(isinstance(value, TableEntry))
		assert(0 <= index < self.table_entry_count)
		bitpos = 2 * index
		mask = 3 << bitpos
		self._value = (self._value & ~mask) | (int(value) << bitpos)

	def __getitem__(self, index: int):
		assert(0 <= index < self.table_entry_count)
		return self.Entry((self._value >> bitpos) & 3)

class ValueTable():
	class PrintFormat(enum.Enum):
		Text = "text"
		Pretty = "pretty"
		TeX = "tex"
		Compact = "compact"

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

	@property
	def output_variable_count(self):
		return 1

	@classmethod
	def _from_compact_representation(cls, compact_str: str):
		assert(compact_str.startswith(":"))
		(input_variable_names, output_variable_names, compact_data) = compact_str[1:].split(":")
		input_variable_names = input_variable_names.split(",")
		output_variable_names = output_variable_names.split(",")
		compact_data = [ int(value, 16) for value in compact_data.split(",") ]
		input_variable_count = len(input_variable_names)
		output_variable_count = len(output_variable_names)

		if output_variable_count != len(compact_data):
			raise ValueError(f"Format specifies {output_variable_count} output variables, but present data section indicates {len(compact_data)}.")
		if output_variable_count != 1:
			raise ValueError("At the moment, only a single output variable is supported.")

		decompacted_values = [ ]
		compact_value = compact_data[0]
		for index in range(2 ** input_variable_count):
			next_value = (compact_value >> (2 * index)) & 3
			if next_value == 2:
				next_value = None
			decompacted_values.append(next_value)
		return cls(input_variable_names = input_variable_names, output_values = decompacted_values)

	@classmethod
	def _parse_from_file(cls, f: "_io.TextIOWrapper", unused_value: int | None = -1):
		assert(unused_value in [ None, 0, 1, -1 ])
		output_values = None
		for (lineno, line) in enumerate(f, 1):
			line = line.strip("\r\n\t ")
			tokens = cls._TABLE_SEP.split(line)
			if lineno == 1:
				if line.startswith(":"):
					# Compact format!
					return cls._from_compact_representation(line)

				variables = tokens
				if len(variables) != len(set(variables)):
					raise ValueError(f"Syntax error when parsing truth table in line {lineno}: Duplicate literal definition found")
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
				index = cls.input_dict_to_index(input_value_dict, variables)
				if output_values[index] != unused_value:
					print(f"Warning when parsing truth table: {input_value_dict} overwrites value in line {lineno}")
				output_values[index] = output_value
		if output_values is None:
			raise ValueError("Unable to read table data from source.")
		if (unused_value == -1) and (-1 in output_values):
			# If strict parsing required, all values must be explicitly set
			raise ValueError("Strict parsing was requested and not all input patterns were explicitly specified.")
		return ValueTable(input_variable_names = variables, output_values = output_values)

	@classmethod
	def parse_from_file(cls, f: "_io.TextIOWrapper", unused_value_str: str):
		assert(unused_value_str in [ "0", "1", "*", "forbidden" ])
		return cls._parse_from_file(f = f, unused_value = {
			"0":			0,
			"1":			1,
			"*":			None,
			"forbidden":	-1,
		}[unused_value_str])

	@classmethod
	def create_from_expression(self, expression: "ParseTreeElement", dc_expression: "ParseTreeElement | None" = None):
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

	def _print_text(self):
		print("\t".join(self.input_variable_names))
		for (inputs, output) in self:
			row = [ str(inputs.get(varname)) for varname in self.input_variable_names ]
			if output is None:
				row.append("*")
			else:
				row.append(str(output))
			print("\t".join(row))

	def _print_pretty(self):
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

	def _print_tex(self):
		colcnt = len(self._output_values) + 1
		print(f"\\begin{{tabular}}{{{'c' * colcnt}}}")
		for (varidx, varname) in enumerate(self.input_variable_names):
			bit = self.input_variable_count - 1 - varidx
			line = [ varname ]
			for i in range(2 ** self.input_variable_count):
				line.append(str((i >> bit) & 1))
			print(f"	{' & '.join(line)}\\\\%")
		print("	\\hline")

		line = [ "Y" ] + [ "*" if (value is None) else str(value) for value in self._output_values ]
		print(f"	{' & '.join(line)}\\\\%")
		print("\\end{tabular}")

	def _print_compact(self):
		output = [ ]
		output += [ f":{','.join(self.input_variable_names)}:Y" ]
		compact_value = 0
		for (index, value) in enumerate(self._output_values):
			if value is None:
				value = 2
			compact_value |= value << (2 * index)
		output += [ f"{compact_value:x}" ]
		print(":".join(output))

	def print(self, print_format: PrintFormat = PrintFormat.Text):
		method = getattr(self, f"_print_{print_format.value}")
		return method()

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
	def input_dict_to_index(input_var_dict: dict, variable_names: list[str]) -> int:
		index = 0
		for (i, varname) in enumerate(variable_names):
			bitno = len(variable_names) - 1 - i
			if input_var_dict[varname]:
				index += (1 << bitno)
		return index

	def at(self, input_var_dict: dict) -> int | None:
		return self._output_values[self.input_dict_to_index(input_var_dict, self.input_variable_names)]

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
			x_var_cnt = (len(variables) + 1) // 2
		x_vars = list(reversed(variables[:x_var_cnt]))
		y_vars = list(reversed(variables[x_var_cnt:]))

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
	vt = ValueTable.create_from_expression(parse_expression("A B + C !D + (A (C + !C))"), dc_expression = parse_expression("A !B !C"))
	vt.print()
	vt.print_kv()
