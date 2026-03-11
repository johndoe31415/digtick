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

	def _assert_simplification(self, complex_expr_str: str, expected_simplified_str: str):
		simplified = self._simplify(complex_expr_str)
		simplified_str = format_expression(simplified)
		if simplified_str != expected_simplified_str:
			with open("/tmp/failed_expression_simplification.txt", "w") as f:
				print(format_expression(simplified, "dot"), file = f)
		self.assertEqual(simplified_str, expected_simplified_str)

	def test_simplify_remove_parenthesis(self):
		self._assert_simplification("(((A + B)))", "A + B")
		self._assert_simplification("(((A + B)))((X))", "(A + B) X")
		self._assert_simplification("(((A + B)))((X + Y))", "(A + B) (X + Y)")
		self._assert_simplification("(((A + B)))((X Y))", "(A + B) X Y")
		self._assert_simplification("(((A B)))((X + Y))", "A B (X + Y)")
		self._assert_simplification("(((A B))) + ((X + Y))", "A B + X + Y")

	def test_simplify_and_constant_parenthesis(self):
		self._assert_simplification("X 1", "X")
		self._assert_simplification("X 0", "0")
		self._assert_simplification("(X + Y) 1", "X + Y")
		self._assert_simplification("(X + Y) 0", "0")
		self._assert_simplification("(X + Y) 0 + (A + B) 1", "A + B")

		self._assert_simplification("1 X", "X")
		self._assert_simplification("0 X", "0")
		self._assert_simplification("1 (X + Y)", "X + Y")
		self._assert_simplification("0 (X + Y)", "0")
		self._assert_simplification("0 (X + Y) + 1 (A + B)", "A + B")

	def test_simplify_or_constant_parenthesis(self):
		self._assert_simplification("X + 1", "1")
		self._assert_simplification("X + 0", "X")
		self._assert_simplification("(X + Y) + 1", "1")
		self._assert_simplification("(X + Y) + 0", "X + Y")
		self._assert_simplification("((X + Y) + 0) + ((A + B) + 1)", "1")

		self._assert_simplification("1 + X", "1")
		self._assert_simplification("0 + X", "X")
		self._assert_simplification("1 + (X + Y)", "1")
		self._assert_simplification("0 + (X + Y)", "X + Y")
		self._assert_simplification("(0 + (X + Y)) + (1 + (A + B))", "1")

	def test_simplify_neg_constant(self):
		self._assert_simplification("-0", "1")
		self._assert_simplification("-1", "0")

	def test_simplify_order_literals(self):
		self._assert_simplification("A10 A9 A11 A0 A1", "A11 A10 A9 A1 A0")
		self._assert_simplification("A10 !A9 A11 !A0 A1", "A11 A10 !A9 A1 !A0")

	def test_complement(self):
		self._assert_simplification("F !F", "0")
		self._assert_simplification("!F F", "0")
		self._assert_simplification("(A B + C D) -(A B + C D)", "0")

		self._assert_simplification("!F + F", "1")
		self._assert_simplification("F + !F", "1")
		self._assert_simplification("(A B + C D) + -(A B + C D)", "1")

	def test_noop_transform(self):
		expr = parse_expression("(((A + B)))((X + Y))(C A + B) (X + Y)")
		noop_transform = ExpressionTransformer()
		transformed = noop_transform.transform(expr)
		self.assertTrue(transformed.identical_to(expr))
