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
from .ExpressionParser import parse_expression
from .ValueTable import ValueTable, CompactStorage
from .Tools import open_file

class ActionSatisfied(BaseAction):
	def run(self):
		with open_file(self._args.filename) as f:
			vt = ValueTable.parse_from_file(f, set_undefined_values_to = self._args.unused_value_is)
		expr = parse_expression(self._args.expression)

		all_satisfied = True
		eval_storage = CompactStorage(vt.input_variable_count)
		sat_storage = CompactStorage(vt.input_variable_count)
		for (index, (input_dict, output_dict)) in enumerate(vt.iter_inputdict):
			expected_value = output_dict[self._args.output_variable_name]
			eval_value = expr.evaluate(input_dict)
			eval_storage[index] = eval_value

			satisfied = (expected_value == CompactStorage.Entry.DontCare) or (expected_value == eval_value)
			if not satisfied:
				#print(f"Not satisfied for: {input_dict} -- expect {int(expected_value)} but evaluation yielded {eval_value}")
				all_satisfied = False
			sat_storage[index] = int(satisfied)

		vt.add_output_variable("Eval", eval_storage)
		vt.add_output_variable("Sat", sat_storage)
		vt.print(ValueTable.PrintFormat(self._args.tbl_format))

		if not all_satisfied:
			print("Warning: the given expression does NOT satisfy the truth table")
		else:
			print("The given expression satisfies the truth table.")
		return 0 if all_satisfied else 1
