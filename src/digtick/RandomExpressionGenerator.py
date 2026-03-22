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

import random
import string
from .ExpressionParser import Variable, BinaryOperator, Operator, Parenthesis
from .RandomDist import RandomDist

class RandomExpressionGenerator():
	_DEFAULT_OPERATOR_DISTRIBUTION = {
		"parenthesis": 1,
		"not": 1,
		"and": 5,
		"or": 10,

		"xor": 2,
		"nand": 2,
		"nor": 2,
	}

	def __init__(self, var_count: int, operator_distribution: dict | None = None, random_source = None):
		self._var_count = var_count
		self._variables = [ Variable(string.ascii_uppercase[i]) for i in range(self._var_count) ]
		self._op_dist = RandomDist(self._DEFAULT_OPERATOR_DISTRIBUTION if (operator_distribution is None) else operator_distribution, random_source = random_source)
		self._random_source = random if (random_source is None) else random_source

	def _gen_term(self):
		disjunctive = self._op_dist.coinflip()
		var_count = round(abs(self._random_source.gauss(0.75 * len(self._variables), 2)))
		if var_count < 1:
			var_count = 1
		elif var_count > len(self._variables):
			var_count = len(self._variables)

		if var_count == len(self._variables):
			variables = list(self._variables)
		else:
			variables = self._random_source.sample(self._variables, var_count)
		self._random_source.shuffle(variables)

		variables = [ ~var if self._op_dist.coinflip() else var for var in variables  ]
		if self._op_dist.coinflip():
			return BinaryOperator.join(Operator.Or, variables)
		else:
			return BinaryOperator.join(Operator.And, variables)

	def generate(self, complexity_count: int) -> "ParseTreeElement":
		expr = self._gen_term()
		for _ in range(complexity_count - 1):
			match option := self._op_dist.event():
				case "parenthesis":
					expr = Parenthesis(expr)

				case "not":
					expr = ~expr

				case "and":
					expr = expr & self._gen_term()

				case "or":
					expr = expr | self._gen_term()

				case "xor":
					expr = expr ^ self._gen_term()

				case "nand":
					expr = expr @ self._gen_term()

				case "nor":
					expr = expr % self._gen_term()
		return expr
