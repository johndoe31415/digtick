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
from pysvgedit import SVGDocument, SVGRect, SVGGroup, SVGPath, SVGText, Vector2D
from .TableFormatter import Table, CellFormatter
from .ValueTable import CompactStorage
from .TextWidthEstimator import TextWidthEstimator
from .QuineMcCluskey import QuineMcCluskey
from .ExpressionParser import Operator, BinaryOperator
from .ExpressionFormatter import format_expression

class KVDiagram():
	_SVG_COLORS = [
		"#2ecc71",
		"#3498db",
		"#f39c12",
		"#e74c3c",
		"#9b59b6",
	]

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
		self._rkvd = self._compute()
		self._svg_cell_width = 20

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
		table = Table()
		table.format_columns({ f"x{x}": CellFormatter.basic_center() for x in range(len(self._rkvd.x_values)) })

		def _overline(text: str) -> str:
			return "".join(char + "\u0305" for char in text)

		def _dict2str(var_dict: dict) -> str:
			return " ".join(_overline(varname) if (value == 0) else varname for (varname, value) in sorted(var_dict.items()))

		heading = { "_": " " }
		for (x, xvalue) in enumerate(self._rkvd.x_values):
			heading[f"x{x}"] = _dict2str(xvalue)
		table.add_row(heading)

		for (y, yvalue) in enumerate(self._rkvd.y_values):
			row = { "_": _dict2str(yvalue) }
			cell_value = dict(yvalue)
			for (x, xvalue) in enumerate(self._rkvd.x_values):
				cell_value.update(xvalue)
				row[f"x{x}"] = self._value_table.at(cell_value, self._output_variable_name).as_str

			table.add_separator_row()
			table.add_row(row)

		table.print(*([ "_" ] + [ f"x{x}" for x in range(len(self._rkvd.x_values)) ]))

	def _svg_overline(self, layer: SVGGroup, text_pos: Vector2D, text: str):
		text_width = TextWidthEstimator.estimate_text_width(text)
		svg_path = layer.add(SVGPath.new(text_pos + Vector2D((self._svg_cell_width / 2) - (text_width / 2), 1.25)))
		svg_path.horizontal(text_width, relative = True)
		svg_path.style["stroke-width"] = 0.75

	def _svg_render_grid(self, layer: SVGGroup):
		grid_extents = Vector2D(len(self._rkvd.x_values), len(self._rkvd.y_values)) * self._svg_cell_width
		layer.add(SVGRect.new(pos = Vector2D(0, 0), extents = grid_extents))

		for x in range(1, len(self._rkvd.x_values)):
			path = layer.add(SVGPath.new(Vector2D(x * self._svg_cell_width, 0)))
			path.vertical(grid_extents.y, relative = True)
			path.style["stroke-width"] = 0.5
		for y in range(1, len(self._rkvd.y_values)):
			path = layer.add(SVGPath.new(Vector2D(0, y * self._svg_cell_width)))
			path.horizontal(grid_extents.x, relative = True)
			path.style["stroke-width"] = 0.5

		for (x, literals) in enumerate(self._rkvd.x_values):
			for (y, literal) in enumerate(sorted(literals.keys())):
				litvalue = literals[literal]

				pos = Vector2D(x * self._svg_cell_width, (y * -15) - 15)
				svg_text = layer.add(SVGText.new(pos = pos, text = literal, rect_extents = Vector2D(self._svg_cell_width, self._svg_cell_width)))
				svg_text.style["text-align"] = "center"
				svg_text.style["font-family"] = "'Latin Modern Roman'"

				if litvalue == 0:
					self._svg_overline(layer, text_pos = pos, text = literal)

		for (y, literals) in enumerate(self._rkvd.y_values):
			for (x, literal) in enumerate(sorted(literals.keys())):
				litvalue = literals[literal]

				pos = Vector2D((x * -15) - 20, y * self._svg_cell_width + 3)
				svg_text = layer.add(SVGText.new(pos = pos, text = literal, rect_extents = Vector2D(self._svg_cell_width, self._svg_cell_width)))
				svg_text.style["text-align"] = "center"
				svg_text.style["font-family"] = "'Latin Modern Roman'"

				if litvalue == 0:
					self._svg_overline(layer, text_pos = pos, text = literal)


	def _svg_render_values(self, layer: SVGGroup):
		zero_layer = layer.add(SVGGroup.new(is_layer = True))
		zero_layer.label = "0 values"

		one_layer = layer.add(SVGGroup.new(is_layer = True))
		one_layer.label = "1 values"

		dc_layer = layer.add(SVGGroup.new(is_layer = True))
		dc_layer.label = "Don't care values"
		sub_layer = {
			CompactStorage.Entry.Low:		zero_layer,
			CompactStorage.Entry.High:		one_layer,
			CompactStorage.Entry.DontCare:	dc_layer,
		}

		for (y, yvalue) in enumerate(self._rkvd.y_values):
			cell_value = dict(yvalue)
			for (x, xvalue) in enumerate(self._rkvd.x_values):
				cell_value.update(xvalue)
				eval_value = self._value_table.at(cell_value, self._output_variable_name)
				pos = Vector2D(x, y) * self._svg_cell_width +  Vector2D(0, 3.5)
				svg_text = sub_layer[eval_value].add(SVGText.new(pos = pos, text = eval_value.as_str, rect_extents = Vector2D(self._svg_cell_width, self._svg_cell_width)))
				svg_text.style["text-align"] = "center"

	def _svg_render_term_coverage(self, layer: SVGGroup, covered: set[tuple[int, int]], color: str):
		for (x, y) in covered:
			pos = Vector2D(x, y) * self._svg_cell_width
			svg_rect = layer.add(SVGRect.new(pos = pos, extents = Vector2D(self._svg_cell_width, self._svg_cell_width)))
			svg_rect.style["stroke"] = "none"
			svg_rect.style["fill"] = color
			svg_rect.style["fill-opacity"] = 0.5

	def _svg_get_color(self, index: int):
		return self._SVG_COLORS[index % len(self._SVG_COLORS)]

	def _svg_render_solution(self, layer: SVGGroup, terms: list["ParseTreeElement"], compare_value: int):
		for (index, term) in enumerate(terms):
			covered = set()
			for (y, yvalue) in enumerate(self._rkvd.y_values):
				cell_value = dict(yvalue)
				for (x, xvalue) in enumerate(self._rkvd.x_values):
					cell_value.update(xvalue)
					if term.evaluate(cell_value) == compare_value:
						covered.add((x, y))

			color = self._svg_get_color(index)
			term_layer = layer.add(SVGGroup.new(is_layer = True))
			term_layer.label = format_expression(term)
			term_layer.highlight_color = color

			self._svg_render_term_coverage(term_layer, covered, color)

	def _svg_render_solutions(self, layer: SVGGroup):
		qmc = QuineMcCluskey(self._value_table, self._output_variable_name)
		opt_dnf = qmc.optimize(emit_dnf = True)
		opt_cnf = qmc.optimize(emit_dnf = False)

		dnf_layer = layer.add(SVGGroup.new(is_layer = True))
		dnf_layer.label = "DNF"
		cnf_layer = layer.add(SVGGroup.new(is_layer = True))
		cnf_layer.label = "CNF"
		# By default, hide CNF terms
		cnf_layer.style.hide()

		dnf_terms = list(opt_dnf.find_minterms())
		cnf_terms = list(opt_cnf.find_maxterms())

		self._svg_render_solution(dnf_layer, dnf_terms, compare_value = 1)
		self._svg_render_solution(cnf_layer, cnf_terms, compare_value = 0)


	def render_svg(self):
		svg = SVGDocument.new()

		values_layer = svg.add(SVGGroup.new(is_layer = True))
		values_layer.label = "Solution"
		self._svg_render_solutions(values_layer)

		grid_layer = svg.add(SVGGroup.new(is_layer = True))
		grid_layer.label = "Grid"
		self._svg_render_grid(grid_layer)

		values_layer = svg.add(SVGGroup.new(is_layer = True))
		values_layer.label = "Values"
		self._svg_render_values(values_layer)

		return svg
