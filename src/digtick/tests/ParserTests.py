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
from digtick.ExpressionParser import parse_expression, BinaryOperator, Operator

class ParserTests(unittest.TestCase):
	def _assert_expression_equal(self, expr1_str: str, expr2_str: str):
		expr1 = parse_expression(expr1_str)
		expr2 = parse_expression(expr2_str)
		self.assertEqual(expr1, expr2)

	def test_precedence_and_or(self):
		self._assert_expression_equal("A + B C", "A + (B C)")
		self._assert_expression_equal("A B + C", "(A B) + C")
		self._assert_expression_equal("A B + C D", "(A B) + (C D)")

	def test_precedence_nand(self):
		self._assert_expression_equal("A + B @ C", "A + (B @ C)")
		self._assert_expression_equal("A % B @ C", "A % (B @ C)")
		self._assert_expression_equal("A + -B @ C", "A + ((-B) @ C)")
		self._assert_expression_equal("A % -B @ C", "A % ((-B) @ C)")
		self._assert_expression_equal("A @ B @ C", "(A @ B) @ C")
		self._assert_expression_equal("A * B @ C", "(A * B) @ C")
		self._assert_expression_equal("A @ B * C", "A @ (B * C)")
		self._assert_expression_equal("A @ B C", "A @ (B * C)")
		self._assert_expression_equal("(A @ B) C", "(A @ B) * C")

	def test_precedence_nor(self):
		self._assert_expression_equal("A % B % C", "(A % B) % C")
		self._assert_expression_equal("A + B % C", "(A + B) % C")
		self._assert_expression_equal("A % B + C", "(A % B) + C")
		self._assert_expression_equal("A % B % C % D", "((A % B) % C) % D")
		self._assert_expression_equal("A ^ B % C % D", "((A ^ B) % C) % D")
		self._assert_expression_equal("A % B ^ C % D", "((A % B) ^ C) % D")
		self._assert_expression_equal("A % B % C ^ D", "((A % B) % C) ^ D")

	def test_compare_impossible(self):
		expr1 = parse_expression("A B D")
		expr2 = parse_expression("A B C")
		with self.assertRaises(ValueError):
			list(expr1.compare_to_expression(expr2))

	def test_compare_subset(self):
		expr1 = parse_expression("A B")
		expr2 = parse_expression("A B C")
		list(expr1.compare_to_expression(expr2))

	def test_wrap_failure(self):
		with self.assertRaises(TypeError):
			expr = parse_expression("A") | 1.2345

	def test_join_empty(self):
		with self.assertRaises(ValueError):
			BinaryOperator.join(Operator.And, [ ])

	def test_parse_empty_disallow(self):
		with self.assertRaises(ValueError):
			parse_expression("")

	def test_parse_empty_allow(self):
		self.assertEqual(parse_expression("", default_empty = "0"), parse_expression("0"))

	def test_variable_names_with_underscore_and_digits(self):
		expr = parse_expression("foo_1 + bar2 baz_3")
		self.assertEqual(expr.evaluate({
			"foo_1": 0,
			"bar2": 1,
			"baz_3": 1,
			}), 1)

		self.assertEqual(expr.evaluate({
			"foo_1": 0,
			"bar2": 1,
			"baz_3": 0,
			}), 0)

	def test_constants_inside_expression_evaluate_correctly(self):
		self.assertEqual(parse_expression("A 1").evaluate({ "A": 1 }), 1)
		self.assertEqual(parse_expression("A 1").evaluate({ "A": 0 }), 0)
		self.assertEqual(parse_expression("A + 0").evaluate({ "A": 0 }), 0)
		self.assertEqual(parse_expression("A + 0").evaluate({ "A": 1 }), 1)
		self.assertEqual(parse_expression("A ^ 1").evaluate({ "A": 0 }), 1)
		self.assertEqual(parse_expression("A ^ 1").evaluate({ "A": 1 }), 0)

	def test_parentheses_are_preserved_structurally(self):
		plain = parse_expression("A + B + C")
		wrapped = parse_expression("A + (B + C)")

		# Equal yes (only compares eval), identical no (compares AST structure)
		self.assertEqual(plain, wrapped)
		self.assertFalse(plain.identical_to(wrapped))

		# Spot check explicitly
		for input_vals in [ {"A": 0, "B": 0, "C": 0},
						{"A": 0, "B": 1, "C": 0},
						{"A": 1, "B": 0, "C": 0},
						{"A": 1, "B": 1, "C": 1}, ]:
			self.assertEqual(plain.evaluate(input_vals), wrapped.evaluate(input_vals))

	def test_parse_malformed_expression_raises(self):
		for expr_str in [ "A +",
					"@ A B",
					"A (B + C",
					"A ++ B", ]:
			with self.subTest(text = expr_str):
				with self.assertRaises(Exception):
					parse_expression(expr_str)
