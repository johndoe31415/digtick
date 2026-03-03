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
from .TableFormatter import Table

class ActionDiffTable(BaseAction):
	def run(self):
		with open(self._args.filename1) as f:
			vt1 = ValueTable.parse_from_file(f, set_undefined_values_to = "N/A")
		with open_file(self._args.filename2) as f:
			vt2 = ValueTable.parse_from_file(f, set_undefined_values_to = "N/A")

		if set(vt1.input_variable_names) != set(vt2.input_variable_names):
			raise ValueError("Truth tables have different input variables, cannot compare.")

		common_output = set(vt1.output_variable_names) & set(vt2.output_variable_names)
		if len(common_output) == 0:
			raise ValueError("Truth tables have no common output variable, cannot compare.")

		input_variable_names = list(sorted(vt1.input_variable_names))
		output_variable_names = list(sorted(common_output))

		table = Table()
		table.add_row({ varname: varname for varname in (input_variable_names + output_variable_names) })
		table.add_separator_row()

		for (input_vars, output1_vars) in vt1.iter_inputdict:
			row = { varname: str(value) for (varname, value) in input_vars.items() }
			for (varname, output1) in output1_vars.items():
				output2 = vt2.at(input_vars, varname)
				if output1 != output2:
					row[varname] = f"{output1} / {output2}"
			table.add_row(row)

		table.print(*(input_variable_names + output_variable_names))
