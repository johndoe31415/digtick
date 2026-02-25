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

import random
import string
from .MultiCommand import BaseAction
from .ExpressionParser import parse_expression
from .ExpressionFormatter import format_expression
from .ValueTable import ValueTable
from .QuineMcCluskey import QuineMcCluskey
from .RandomDist import RandomDist

class ActionRandomExpression(BaseAction):
	def _gen_term(self):
		disjunctive = RandomDist.coinflip()
		literal_count = round(abs(random.gauss(0.75 * len(self._variables), 2)))
		if literal_count < 1:
			literal_count = 1
		elif literal_count > len(self._variables):
			literal_count = len(self._variables)

		if literal_count == len(self._variables):
			literals = list(self._variables)
		else:
			literals = random.sample(self._variables, literal_count)
		random.shuffle(literals)
		literals = [ f"{'!' if RandomDist.coinflip() else ''}{literal}" for literal in literals ]
		if RandomDist.coinflip():
			return f"({' + '.join(literals)})"
		else:
			return f"{' '.join(literals)}"

	def _generate(self):
		expr = self._gen_term()
		while len(expr) < self._args.complexity:
			match option := self._op_dist.event():
				case "parenthesis":
					expr = f"({expr})"

				case "not":
					expr = f"-({expr})"

				case "and":
					expr = f"{expr} {self._gen_term()}"

				case "or":
					expr = f"{expr} + {self._gen_term()}"

		return parse_expression(expr)


	def run(self):
		self._op_dist = RandomDist({
			"parenthesis": 1,
			"not": 1,
			"and": 5,
			"or": 10,
		})

		self._variables = [ string.ascii_uppercase[i] for i in range(self._args.var_count) ]
		while True:
			self._expression = self._generate()

			vt = ValueTable.create_from_expression(self._expression)
			simplified = QuineMcCluskey(vt, verbosity = self._args.verbose).optimize()
			simplified_str = format_expression(simplified)
			if len(simplified_str) < 20:
				# Too low simplified complexity
				continue
			print(f"Expression: {format_expression(self._expression)}")
			print(f"Simplified: {format_expression(simplified)}")
			break
