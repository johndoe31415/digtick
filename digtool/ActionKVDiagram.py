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
from .ValueTable import ValueTable
from .Tools import open_file

class ActionKVDiagram(BaseAction):
	def run(self):
		with open_file(self._args.filename) as f:
			vt = ValueTable.parse_from_file(f, unused_value_str = self._args.unused_value_is)
		if self._args.literal_order is None:
			variable_order = None
		else:
			if "," in self._args.literal_order:
				variable_order = ",".split(self._args.literal_order)
			else:
				variable_order = list(self._args.literal_order)

			if len(set(variable_order)) != len(variable_order):
				raise ValueError("Literal order has duplicate literal")
			if set(variable_order) != set(vt.input_variable_names):
				raise ValueError(f"The specified literal order variables ({', '.join(variable_order)}) does not match the variables present in the input file ({', '.join(vt.input_variable_names)}).")

		vt.print_kv(variable_order = variable_order, x_offset = self._args.x_offset, y_offset = self._args.y_offset, x_invert = self._args.x_invert, y_invert = self._args.y_invert, row_heavy = self._args.row_heavy)
