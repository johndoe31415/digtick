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
from digtick.ExpressionParser import parse_expression, Variable
from digtick.ExpressionFormatter import format_expression
from digtick.ExpressionTransformer import ExpressionTransformer
from digtick.Enums import ExpressionFormatOpts

class ExpressionTransformerTests(unittest.TestCase):
	def setUp(self):
		self._simplify_transformer = ExpressionTransformer.new("simplify")

	def _simplify(self, expr_str: str):
		if isinstance(expr_str, str):
			expr = parse_expression(expr_str)
		else:
			expr = expr_str
		return self._simplify_transformer.transform(expr)

	def _assert_simplification(self, complex_expr_str: str, expected_simplified_str: str):
		simplified = self._simplify(complex_expr_str)
		simplified_str = format_expression(simplified)
		if simplified_str != expected_simplified_str:
			filename = "/tmp/failed_expression_simplification.txt"
			print()
			print(f"Testcase failed. Wrote expression as DOT to {filename}: dot -Tpng -o/tmp/failed_expression_simplification.png <{filename}")
			with open(filename, "w") as f:
				print(format_expression(simplified, ExpressionFormatOpts(ExpressionFormatOpts.Value.Dot)), file = f)
		self.assertEqual(simplified_str, expected_simplified_str)

	def test_simplify_remove_parenthesis(self):
		self._assert_simplification("(((A + B)))", "A + B")
		self._assert_simplification("(((A + B)))((X))", "X (A + B)")
		self._assert_simplification("(((A + B)))((X + Y))", "(A + B) (X + Y)")
		self._assert_simplification("(((A + B)))((X Y))", "X Y (A + B)")
		self._assert_simplification("(((A B)))((X + Y))", "A B (X + Y)")
		self._assert_simplification("(((A B))) + ((X + Y))", "X + Y + A B")

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
		(A, C) = (Variable("A"), Variable("C"))
		self.assertTrue(((A | ~C) | C).is_tautology())
		self._assert_simplification((A | ~C) | C, "1")

		self._assert_simplification("F !F", "0")
		self._assert_simplification("!F F", "0")
		self._assert_simplification("(A B + C D) -(A B + C D)", "0")
		self._assert_simplification("F G !C D A C G E", "0")

		self._assert_simplification("!F + F", "1")
		self._assert_simplification("F + !F", "1")
		self._assert_simplification("(A B + C D) + -(A B + C D)", "1")
		self._assert_simplification("F + G + !C + D + A + C + G + E", "1")

	def test_idempotence(self):
		self._assert_simplification("C D C", "C D")
		self._assert_simplification("A C D C", "A C D")
		self._assert_simplification("A B C D C", "A B C D")

		self._assert_simplification("C + D + C", "C + D")
		self._assert_simplification("A + C + D + C", "A + C + D")
		self._assert_simplification("A + B + C + D + C", "A + B + C + D")

	def test_noop_transform(self):
		expr = parse_expression("(((A + B)))((X + Y))(C A + B) (X + Y)")
		noop_transform = ExpressionTransformer()
		transformed = noop_transform.transform(expr)
		self.assertTrue(transformed.identical_to(expr))

	def test_simplify_double_negative(self):
		self._assert_simplification("!!A", "A")

	def test_simplify_complex(self):
		self._assert_simplification("A + X + 0", "A + X")
		self._assert_simplification("A + 0 + !A !B !C", "A + !A !B !C")
		self._assert_simplification("A + X + 0 + !A !B !C", "A + X + !A !B !C")
		self._assert_simplification("(A + 1)(B & 0)((1)) + (!B !C !A) + (A + A) + (A A) + (X @ 1 @ 1)", "A + X + !A !B !C")
		self._assert_simplification("-((A + 1)(B & 0)((1)) + (!B !C !A) + (A + A) + (A A) + (-X @ 1 @ 1))(C 1)(D + 0)((X)+(X))((Y)(Y))(Z % 0 % 0)(K + !K)", "C D X Y Z !(A + !X + !A !B !C)")
