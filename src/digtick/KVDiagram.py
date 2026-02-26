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

import dataclasses
from .TableFormatter import Table, CellFormatter

class KVDiagram():
	@dataclasses.dataclass
	class RenderedKVDiagram():
		x_values: list[dict]
		y_values: list[dict]

	def __init__(self, value_table: "ValueTable", output_variable_name: str | None = None, variable_order: list[str] | None = None, x_offset: int = 0, y_offset: int = 0, x_invert: bool = False, y_invert: bool = False, row_heavy: bool = True):
		self._value_table = value_table
		self._output_variable_name = output_variable_name
		self._variable_order = variable_order
		self._x_offset = x_offset
		self._y_offset = y_offset
		self._x_invert = x_invert
		self._y_invert = y_invert
		self._row_heavy = row_heavy
		if output_variable_name is None:
			if self._value_table.output_variable_count == 1:
				output_variable_name = self._value_table.output_variable_names[0]
			else:
				raise ValueError(f"Multiple outputs are present in the data table, need to explicitly specify which of the output variables the KV diagram should show. Options: {', '.join(sorted(self._value_table.output_variable_names))}")

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

	def _compute(self):
		def _create_kv_dict(var_names: list[str], offset: int = 0, invert_direction: bool = False):
			result = [ ]
			var_count = len(var_names)
			for i in range(2 ** var_count):
				idx = (-i + offset) if invert_direction else (i + offset)
				gc = self._gray_code(idx % (2 ** var_count))
				values = { var_names[i]: int((gc & (1 << i)) != 0) for i in range(var_count) }
				result.append(values)
			return result

		variables = self._value_table.input_variable_names if (self._variable_order is None) else self._variable_order
		if self._row_heavy:
			x_var_cnt = len(variables) // 2
		else:
			x_var_cnt = (len(variables) + 1) // 2
		x_vars = list(reversed(variables[:x_var_cnt]))
		y_vars = list(reversed(variables[x_var_cnt:]))

		x_values = _create_kv_dict(x_vars, self._x_offset, invert_direction = self._x_invert)
		y_values = _create_kv_dict(y_vars, self._y_offset, invert_direction = self._y_invert)

		return self.RenderedKVDiagram(x_values = x_values, y_values = y_values)


	def print_text(self):
		rkvd = self._compute()

		table = Table()
		table.format_columns({ f"x{x}": CellFormatter.basic_center() for x in range(len(rkvd.x_values)) })

		def _overline(text: str) -> str:
			return "".join(char + "\u0305" for char in text)

		def _dict2str(var_dict: dict) -> str:
			return " ".join(_overline(varname) if (value == 0) else varname for (varname, value) in sorted(var_dict.items()))

		heading = { "_": " " }
		for (x, xvalue) in enumerate(rkvd.x_values):
			heading[f"x{x}"] = _dict2str(xvalue)
		table.add_row(heading)

		for (y, yvalue) in enumerate(rkvd.y_values):
			row = { "_": _dict2str(yvalue) }
			cell_value = dict(yvalue)
			for (x, xvalue) in enumerate(rkvd.x_values):
				cell_value.update(xvalue)
				row[f"x{x}"] = self._value_table.at(cell_value, self._output_variable_name).as_str

			table.add_separator_row()
			table.add_row(row)

		table.print(*([ "_" ] + [ f"x{x}" for x in range(len(rkvd.x_values)) ]))

	def render_svg(self):
		pass
