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

import re
import enum
import collections
from .TableFormatter import Table
from .ExpressionParser import Operator, Constant, Variable, BinaryOperator

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

	def indices_with_value(self, search_value: Entry):
		return [ index for (index, value) in enumerate(self) if (value == search_value) ]

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
		LogiSim = "logisim"

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

	def add_output_variable(self, varname: str, storage: CompactStorage):
		assert(storage.variable_count == self.input_variable_count)
		self._output_variable_names.append(varname)
		self._named_outputs[varname] = storage
		self._output_values.append(storage)

	@classmethod
	def from_compact_representation(cls, compact_str: str):
		assert(compact_str.startswith(":"))
		(input_variable_names, output_variable_names, compact_data) = compact_str[1:].split(":")
		input_variable_names = input_variable_names.split(",")
		output_variable_names = output_variable_names.split(",")
		compact_data = compact_data.split(",")
		if len(output_variable_names) != len(compact_data):
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
					return cls.from_compact_representation(line)

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

	def iter_output_variable(self, output_var_name: str):
		if output_var_name not in self._named_outputs:
			raise KeyError(f"No output variable \"{output_var_name}\" in truth table, only: {', '.join(self.output_variable_names)}")
		yield from self._named_outputs[output_var_name]

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

	def _print_logisim(self):
		logisim_chars = {
			CompactStorage.Entry.Low:		"0",
			CompactStorage.Entry.High:		"1",
			CompactStorage.Entry.DontCare:	"-",
		}
		print("# Logisim-compatible truth table, generated by https://github.com/johndoe31415/digtick")
		print()
		print(" ".join(self.input_variable_names + [ "|" ] + self.output_variable_names))
		print("~" * (((len(self.input_variable_names) + len(self._output_variable_names)) * 2) + 1))
		for (inputs, outputs) in self.iter_inputlist:
			row = [ str(bit) for bit in inputs ] + [ "|" ] + [ logisim_chars[output_bit] for output_bit in outputs ]
			print(" ".join(row))

	def print(self, print_format: PrintFormat = PrintFormat.Text):
		method = getattr(self, f"_print_{print_format.value}")
		return method()

	def _cdnf(self, varname: str, search_value: CompactStorage.Entry):
		term_input_values = [ self.index_to_dict(index) for index in self._named_outputs[varname].indices_with_value(search_value) ]
		def _minterm(input_values: dict):
			literals = [ ~Variable(varname) if input_values[varname] else Variable(varname) for varname in self.input_variable_names ]
			return BinaryOperator.join(Operator.And, literals)
		terms = [ _minterm(term_input_value) for term_input_value in term_input_values ]
		if len(terms) == 0:
			return Constant(0)
		else:
			return BinaryOperator.join(Operator.Or, terms)

	def cdnf(self, varname: str) -> "ParseTreeElement":
		return self._cdnf(varname = varname, search_value = CompactStorage.Entry.High)

	def cdnf_dc(self, varname: str) -> "ParseTreeElement":
		return self._cdnf(varname = varname, search_value = CompactStorage.Entry.DontCare)

	def ccnf(self, varname: str) -> "ParseTreeElement":
		term_input_values = [ self.index_to_dict(index) for index in self._named_outputs[varname].indices_with_value(CompactStorage.Entry.Low) ]
		def _maxterm(input_values: dict):
			literals = [ Variable(varname) if input_values[varname] else ~Variable(varname) for varname in self.input_variable_names ]
			return BinaryOperator.join(Operator.Or, literals)
		terms = [ _maxterm(term_input_value) for term_input_value in term_input_values ]
		if len(terms) == 0:
			return Constant(1)
		else:
			return BinaryOperator.join(Operator.And, terms)

if __name__ == "__main__":
	from .ExpressionParser import parse_expression
	vt = ValueTable.create_from_expression("Q", parse_expression("A B + C !D + (A (C + !C))"), dc_expression = parse_expression("A !B !C"))
	vt.print()
