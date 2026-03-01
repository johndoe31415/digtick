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
from .ValueTable import ValueTable

class ActionMakeTable(BaseAction):
	def run(self):
		expr = parse_expression(self._args.expression)
		if self._args.dc_expression is not None:
			dc_expr = parse_expression(self._args.dc_expression)
		else:
			dc_expr = None

		vt = ValueTable.create_from_expression(output_variable_name = self._args.output_variable_name, expression = expr, dc_expression = dc_expr)
		vt.print(ValueTable.PrintFormat(self._args.tbl_format))
