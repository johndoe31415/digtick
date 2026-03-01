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
from .ExpressionFormatter import format_expression
from .ValueTable import ValueTable
from .QuineMcCluskey import QuineMcCluskey
from .RandomExpressionGenerator import RandomExpressionGenerator

class ActionRandomExpression(BaseAction):
	def run(self):
		if self._args.allow_nand_nor_xor:
			operator_distribution = None
		else:
			operator_distribution = {
				"parenthesis": 1,
				"not": 1,
				"and": 5,
				"or": 10,
			}

		reg = RandomExpressionGenerator(self._args.var_count, operator_distribution = operator_distribution)
		try_no = 0
		while True:
			try_no += 1
			expression = reg.generate(self._args.complexity)

			vt = ValueTable.create_from_expression("Y", expression)
			simplified = QuineMcCluskey(vt, "Y", verbosity = self._args.verbose).optimize()
			simplified_str = format_expression(simplified)
			if (not self._args.allow_trivial) and ((len(simplified_str) < 20) and (try_no < 100)):
				# Too low simplified complexity or unable to fulfill
				continue
			print(f"Expression: {format_expression(expression)}")
			print(f"Simplified: {format_expression(simplified)}")
			break
