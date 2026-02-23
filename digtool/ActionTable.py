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

from .BaseAction import BaseAction
from .ExpressionParser import parse_expression
from .TableFormatter import Table

class ActionTable(BaseAction):
	def _table(self):
		for (var_dict, evaluation) in self._expr.table():
			if (self._dc_expr is None) or (self._dc_expr.expr.evaluate(var_dict) == 0):
				yield (var_dict, evaluation)
			else:
				yield (var_dict, "*")

	def _coltable(self):
		rows = [ ]
		for i in range(len(self._expr.variables) + 1):
			rows.append([ ])
		for (var_dict, evaluation) in self._table():
			for (varno, varname) in enumerate(self._expr.variables):
				rows[varno].append(var_dict[varname])
			rows[-1].append(evaluation)
		yield from zip(self._expr.variables, rows)
		yield (None, rows[-1])

	def _print_text(self):
		table = Table()
		print(table)
		table.print()

#		fdfd
#		sep = f"{'-' * (self._maxlen + 2)}"
#		end = "|"
#		cols = len(self._expr.variables) + 1
#
#		hdr_row = end + end.join(f" {varname:<{self._maxlen}} " for varname in list(self._expr.variables) + [ "=" ]) + end
#		sep_row = end + end.join([ sep ] * cols) + end
#		print(hdr_row)
#		print(sep_row)
		for (var_dict, evaluation) in self._table():
			var_dict["="] = evaluation
			table.add_row(var_dict)
#			val_row = end + end.join(f" {var_dict[varname]:<{self._maxlen}} " for varname in list(self._expr.variables)) + end + f" {evaluation:<{self._maxlen}} " + end
#			print(val_row)

		table.print("A", "B", "C", "D", "=")

#	def _print_table(self):
#		print("\t".join(varname for varname in self._expr.variables))
#		for (var_dict, evaluation) in self._table():
#			line = [ str(var_dict[varname]) for varname in self._expr.variables ]
#			line.append(str(evaluation))
#			print("\t".join(line))

	def _print_tex(self):
		rows = [ ]
		for i in range(len(self._expr.variables) + 1):
			rows.append([ ])

		for (var_name, values) in self._coltable():
			if var_name is None:
				print("\\hline")
				var_name = "="
			print(" & ".join([ var_name ] + [ str(value) for value in values ]) + "\\\\")

	def _print_kv(self):
		def _gray_code(x):
			return x ^ (x >> 1)

		def _inv_gray_code(x):
			result = 0
			while x != 0:
				result ^= x
				x >>= 1
			return result

		x_var_cnt = (len(self._expr.variables) + 1) // 2
		y_var_cnt = len(self._expr.variables) - x_var_cnt

		x_vars = self._expr.variables[ : x_var_cnt]
		y_vars = self._expr.variables[x_var_cnt : ]

		data_width = 1 << x_var_cnt
		data_height = 1 << y_var_cnt
		width = y_var_cnt + data_width
		height = x_var_cnt + data_height
		table = Table(width, height)

		for (no, varname) in enumerate(x_vars):
			for x in range(data_width):
				gc = _gray_code(x)
				inverted = (gc & (1 << (x_var_cnt - 1 - no))) == 0
				table.set(y_var_cnt + x, no, f"{'!' if inverted else ''}{varname}")

		for (no, varname) in enumerate(y_vars):
			for y in range(data_height):
				gc = _gray_code(y)
				inverted = (gc & (1 << (y_var_cnt - 1 - no))) == 0
				table.set(y_var_cnt - 1 - no, x_var_cnt + y, f"{'!' if inverted else ''}{varname}")

		for (var_dict, evaluation) in self._table():
			if (evaluation == 0) and (not self._args.kv_show_zeros):
				continue

			x_gc = 0
			for (no, x_var) in enumerate(x_vars):
				if var_dict[x_var]:
					x_gc |= 1 << (x_var_cnt - 1 - no)
			x = _inv_gray_code(x_gc)

			y_gc = 0
			for (no, y_var) in enumerate(y_vars):
				if var_dict[y_var]:
					y_gc |= 1 << (y_var_cnt - 1 - no)
			y = _inv_gray_code(y_gc)

			table.set(y_var_cnt + x, x_var_cnt + y, str(evaluation))

		table.print()

	def run(self):
		self._expr = parse_expression(self._args.expression)
		if self._args.dc_expression is not None:
			self._dc_expr = parse_expression(self._args.dc_expression)
		else:
			self._dc_expr = None
		self._maxlen = max(len(varname) for varname in self._expr.variables)

		handler_name = f"_print_{self._args.format}"
		handler = getattr(self, handler_name, None)
		if handler is None:
			raise NotImplementedError(handler_name)
		return handler()
