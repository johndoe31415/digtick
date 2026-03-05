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

import unittest
from digtick.ExpressionParser import parse_expression
from digtick.ExpressionFormatter import format_expression
from digtick.ExpressionTransformer import ExpressionTransformer

class ExpressionTransformerTests(unittest.TestCase):
	def setUp(self):
		self._simplify_transformer = ExpressionTransformer.new("simplify")

	def _simplify(self, expr_str: str):
		return self._simplify_transformer.transform(parse_expression(expr_str))

	def test_simplify_remove_parenthesis(self):
		self.assertEqual(format_expression(self._simplify("(((A + B)))")), "A + B")
		self.assertEqual(format_expression(self._simplify("(((A + B)))((X))")), "(A + B) X")
		#self.assertEqual(format_expression(self._simplify("(((A + B)))((X Y))")), "(A + B) X Y")		# TODO unhanled!

	def test_simplify_and_constant_parenthesis(self):
		self.assertEqual(format_expression(self._simplify("X 1")), "X")
		self.assertEqual(format_expression(self._simplify("X 0")), "0")
		self.assertEqual(format_expression(self._simplify("(X + Y) 1")), "X + Y")
		self.assertEqual(format_expression(self._simplify("(X + Y) 0")), "0")
		self.assertEqual(format_expression(self._simplify("(X + Y) 0 + (A + B) 1")), "A + B")

		self.assertEqual(format_expression(self._simplify("1 X")), "X")
		self.assertEqual(format_expression(self._simplify("0 X")), "0")
		self.assertEqual(format_expression(self._simplify("1 (X + Y)")), "X + Y")
		self.assertEqual(format_expression(self._simplify("0 (X + Y)")), "0")
		self.assertEqual(format_expression(self._simplify("0 (X + Y) + 1 (A + B)")), "A + B")

	def test_simplify_or_constant_parenthesis(self):
		self.assertEqual(format_expression(self._simplify("X + 1")), "1")
		self.assertEqual(format_expression(self._simplify("X + 0")), "X")
		self.assertEqual(format_expression(self._simplify("(X + Y) + 1")), "1")
		self.assertEqual(format_expression(self._simplify("(X + Y) + 0")), "X + Y")
		self.assertEqual(format_expression(self._simplify("((X + Y) + 0) + ((A + B) + 1)")), "1")

		self.assertEqual(format_expression(self._simplify("1 + X")), "1")
		self.assertEqual(format_expression(self._simplify("0 + X")), "X")
		self.assertEqual(format_expression(self._simplify("1 + (X + Y)")), "1")
		self.assertEqual(format_expression(self._simplify("0 + (X + Y)")), "X + Y")
		self.assertEqual(format_expression(self._simplify("(0 + (X + Y)) + (1 + (A + B))")), "1")
