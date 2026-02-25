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

from .MultiCommand import BaseAction
from .ExpressionParser import parse_expression

class ActionEqual(BaseAction):
	def run(self):
		expr1 = parse_expression(self._args.expression1)
		expr2 = parse_expression(self._args.expression2)
		eq = True
		for (value_dict, eval1, eval2) in expr1.compare_to_expression(expr2):
			if eval1 != eval2:
				eq = False
				print(f"Not equal: {value_dict} gives {eval1} on LHS but {eval2} on RHS")
				return 1

		print("Expressions equal.")
		return 0
