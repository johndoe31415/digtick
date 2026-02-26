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

		@property
		def as_str(self):
			return {
				self.Low:		"0",
				self.High:		"1",
				self.DontCare:	"*",
				self.Undefined:	"N/A",
			}[self]

	def __init__(self, variable_count: int, initial_value: int | None = None):
		self._variable_count = variable_count
		if initial_value is None:
			# Initialize all values to undefined
			self._value = (2 ** (2 * self.table_entry_count)) - 1
		else:
			self._value = initial_value

	@property
	def variable_count(self):
		return self._variable_count

	@property
	def table_entry_count(self):
		return 2 ** self.variable_count

	@property
	def has_undefined_values(self):
		return any(value == self.Entry.Undefined for value in self)

	@classmethod
	def from_string(cls, variable_count: int, compact_table_str: str):
		return cls(variable_count = variable_count, initial_value = int(compact_table_str, 16))

	def to_string(self):
		return f"{self._value:x}"

	def set_undefined_values_to(self, entryvalue: Entry):
		for (index, value) in enumerate(self):
			if value == self.Entry.Undefined:
				self[index] = entryvalue

	def __iter__(self):
		value = self._value
		for _ in range(self.table_entry_count):
			yield self.Entry(value & 3)
			value >>= 2

	def __setitem__(self, index: int, entryvalue: Entry | int | str):
		assert(isinstance(entryvalue, self.Entry) or (entryvalue in [ 0, 1, "0", "1", "*" ]))
		if entryvalue == "*":
			entryvalue = self.Entry.DontCare
		else:
			entryvalue = int(entryvalue)
		assert(0 <= index < self.table_entry_count)
		bitpos = 2 * index
		mask = 3 << bitpos
		self._value = (self._value & ~mask) | (entryvalue << bitpos)

	def __getitem__(self, index: int):
		assert(0 <= index < self.table_entry_count)
		bitpos = 2 * index
		return self.Entry((self._value >> bitpos) & 3)

	def __repr__(self):
		return f"CompStor<{self.variable_count}>"

class ValueTable():
	class PrintFormat(enum.Enum):
		Text = "text"
		Pretty = "pretty"
		TeX = "tex"
		Compact = "compact"

	_TABLE_SEP = re.compile(r"\s+")

	def __init__(self, input_variable_names: list[str], output_variable_names: list[str], output_values: list[CompactStorage]):
		assert(len(output_values) == len(output_variable_names))
		assert(all(storage.variable_count == len(input_variable_names) for storage in output_values))
		self._input_variable_names = input_variable_names
		self._output_variable_names = output_variable_names
		self._output_values = output_values
		self._named_outputs = { output_variable_name: storage for (output_variable_name, storage) in zip(self._output_variable_names, self._output_values) }
		self._index_weights = { varname: 1 << bitno for (bitno, varname) in enumerate(reversed(self._input_variable_names)) }

	@property
	def input_variable_names(self):
		return self._input_variable_names

	@property
	def input_variable_count(self):
		return len(self._input_variable_names)

	@property
	def output_variable_names(self):
		return self._output_variable_names

	@property
	def output_variable_count(self):
		return len(self._output_variable_names)

	@classmethod
	def _from_compact_representation(cls, compact_str: str):
		assert(compact_str.startswith(":"))
		(input_variable_names, output_variable_names, compact_data) = compact_str[1:].split(":")
		input_variable_names = input_variable_names.split(",")
		output_variable_names = output_variable_names.split(",")
		compact_data = compact_data.split(",")
		if output_variable_count != len(compact_data):
			raise ValueError(f"Format specifies {len(output_variable_names)} output variables, but present data section indicates {len(compact_data)}.")
		output_values = [ CompactStorage.from_string(len(input_variable_names), compact_data_string) for compact_data_string in compact_data ]
		return cls(input_variable_names = input_variable_names, output_variable_names = output_variable_names, output_values = output_values)

	@classmethod
	def _parse_from_file(cls, f: "_io.TextIOWrapper", set_undefined_values_to: CompactStorage.Entry | None = None):
		output_values = None
		for (lineno, line) in enumerate(f, 1):
			line = line.strip("\r\n\t ")
			tokens = cls._TABLE_SEP.split(line)
			if lineno == 1:
				if line.startswith(":"):
					# Compact format!
					return cls._from_compact_representation(line)

				input_indices = [ ]
				input_variables = [ ]
				output_indices = [ ]
				output_variables = [ ]
				for (index, field) in enumerate(tokens):
					is_output = field.startswith(">")
					name = field[1:] if is_output else field
					if is_output:
						output_variables.append(name)
						output_indices.append(index)
					else:
						input_variables.append(name)
						input_indices.append(index)
				if len(input_variables) == 0:
					raise ValueError(f"Syntax error when parsing truth table in line {lineno}: No input variables found")
				if len(output_variables) == 0:
					raise ValueError(f"Syntax error when parsing truth table in line {lineno}: No output variables found")

				all_variables = input_variables + output_variables
				if len(all_variables) != len(set(all_variables)):
					duplicate_variables = { var_name for (var_name, count) in collections.Counter(all_variables).items() if count > 1 }
					raise ValueError(f"Syntax error when parsing truth table in line {lineno}: Duplicate variable name(s) used: {', '.join(sorted(duplicate_variables))}")

				output_values = [ CompactStorage(variable_count = len(input_variables)) for _ in range(len(output_variables)) ]
			else:
				if len(tokens) != len(input_variables) + len(output_variables):
					raise ValueError(f"Syntax error when parsing truth table in line {lineno}: expected {len(input_variables) + len(output_variables)} tokens, but saw {len(tokens)}")

				input_bits = [ int(tokens[i]) for i in input_indices ]
				index = sum(value << bitpos for (bitpos, value) in enumerate(reversed(input_bits)))

				output_bits = [ tokens[i] for i in output_indices ]
				for (storage, output_bit) in zip(output_values, output_bits):
					if storage[index] != CompactStorage.Entry.Undefined:
						print(f"Warning when parsing truth table: value overwritten in line {lineno}")
					storage[index] = output_bit
		if output_values is None:
			raise ValueError("Unable to read table data from source.")

		if output_values[0].has_undefined_values:
			if set_undefined_values_to is None:
				raise ValueError("Strict parsing was requested but not all input patterns were explicitly specified.")
			else:
				for storage in output_values:
					storage.set_undefined_values_to(set_undefined_values_to)
		return ValueTable(input_variable_names = input_variables, output_variable_names = output_variables, output_values = output_values)

	@classmethod
	def parse_from_file(cls, f: "_io.TextIOWrapper", set_undefined_values_to: str):
		assert(set_undefined_values_to in [ "0", "1", "*", "forbidden" ])
		return cls._parse_from_file(f = f, set_undefined_values_to = {
			"0":			CompactStorage.Entry.Low,
			"1":			CompactStorage.Entry.High,
			"*":			CompactStorage.Entry.DontCare,
		}.get(set_undefined_values_to))

	@classmethod
	def create_from_expression(self, output_variable_name: str, expression: "ParseTreeElement", dc_expression: "ParseTreeElement | None" = None):
		storage = CompactStorage(len(expression.variables))
		index_values = { varname: 1 << bitno for (bitno, varname) in enumerate(reversed(expression.variables)) }
		for (inputs, output) in expression.table():
			if (dc_expression is not None) and (dc_expression.evaluate(inputs) != 0):
				output = CompactStorage.Entry.DontCare
			index = sum(index_values[varname] for (varname, bitvalue) in inputs.items() if bitvalue == 1)
			storage[index] = output
		return ValueTable(input_variable_names = list(expression.variables), output_variable_names = [ output_variable_name ], output_values = [ storage ])

	def index_to_list(self, index: int) -> list[int]:
		return [ (index >> i) & 1 for i in reversed(range(self.input_variable_count)) ]

	def index_to_dict(self, index: int) -> dict:
		return { varname: bit for (varname, bit) in zip(self.input_variable_names, self.index_to_list(index)) }

	def dict_to_index(self, input_var_dict: dict) -> int:
		return sum(self._index_weights[varname] for (varname, bit_value) in input_var_dict.items() if bit_value == 1)

	def at(self, input_var_dict: dict, output_var_name: str) -> CompactStorage.Entry:
		index = self.dict_to_index(input_var_dict)
		return self._named_outputs[output_var_name][index]

	def __iter__(self):
		yield from zip(*self._output_values)

	@property
	def iter_inputlist(self):
		for (index, outputs) in enumerate(zip(*self._output_values)):
			yield (self.index_to_list(index), outputs)

	@property
	def iter_inputdict(self):
		for (index, outputs) in enumerate(zip(*self._output_values)):
			output_dict = { name: output for (name, output) in zip(self._output_variable_names, outputs) }
			yield (self.index_to_dict(index), output_dict)

	def _print_text(self):
		heading = self._input_variable_names + [ f">{name}" for name in self._output_variable_names ]
		print("\t".join(heading))
		for (inputs, outputs) in self.iter_inputlist:
			row = [ str(bit) for bit in inputs ] + [ output_bit.as_str for output_bit in outputs ]
			print("\t".join(row))

	def _print_pretty(self):
		table = Table()
		header = { varname: varname for varname in self.input_variable_names + self.output_variable_names }
		header["="] = " "
		table.add_row(header)
		table.add_separator_row()

		for (inputs, outputs) in self.iter_inputdict:
			row = { name: value.as_str for (name, value) in outputs.items() }
			row.update(inputs)
			table.add_row(row)

		table.print(*(self.input_variable_names + self.output_variable_names))

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

		for (output_varname, storage) in zip(self.output_variable_names, self._output_values):
			line = [ output_varname ] + [ value.as_str for value in storage ]
			print(f"	{' & '.join(line)}\\\\%")
		print("\\end{tabular}")

	def _print_compact(self):
		output = [ ]
		output += [ f":{','.join(self.input_variable_names)}:{','.join(self.output_variable_names)}" ]
		output += [ storage.to_string() for storage in self._output_values ]
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

#	@staticmethod
#	def input_dict_to_index(input_var_dict: dict, variable_names: list[str]) -> int:
#		index = 0
#		for (i, varname) in enumerate(variable_names):
#			bitno = len(variable_names) - 1 - i
#			if input_var_dict[varname]:
#				index += (1 << bitno)
#		return index

	def print_kv(self, variable_order: list[str] | None = None, output_variable_name: str | None = None, x_offset: int = 0, y_offset: int = 0, x_invert: bool = False, y_invert: bool = False, row_heavy: bool = True):
		if output_variable_name is None:
			if self.output_variable_count == 1:
				output_variable_name = self.output_variable_names[0]
			else:
				raise ValueError(f"Multiple outputs are present in the data table, need to explicitly specify which of the output variables the KV diagram should show. Options: {', '.join(sorted(self.output_variable_names))}")

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
				row[f"x{x}"] = self.at(cell_value, output_variable_name).as_str

			table.add_separator_row()
			table.add_row(row)

		table.print(*([ "_" ] + [ f"x{x}" for x in range(len(x_values)) ]))


if __name__ == "__main__":
	from .ExpressionParser import parse_expression
	vt = ValueTable.create_from_expression(parse_expression("A B + C !D + (A (C + !C))"), dc_expression = parse_expression("A !B !C"))
	vt.print()
	vt.print_kv()
