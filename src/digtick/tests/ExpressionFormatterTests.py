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

import os
import unittest
from digtick.Enums import ExpressionFormat
from digtick.ExpressionParser import parse_expression, Variable
from digtick.ExpressionFormatter import format_expression
from digtick.RandomExpressionGenerator import RandomExpressionGenerator

_run_slow_tests = (os.getenv("UNITTEST_RUN_ALL") == "1")

class ExpressionFormatterTests(unittest.TestCase):
	def _assert_expression_reformattable(self, expr_str: str):
		parsed1 = parse_expression(expr_str)
		formatted = format_expression(parsed1)
		parsed2 = parse_expression(formatted)
		self.assertEqual(parsed1, parsed2)
		self.assertTrue(parsed1.identical_to(parsed2))

	def test_string_input(self):
		for expression in """
				A + B C
				A + (B C)
				A B + C
				A B + C D
				(A B) + C
				(A B) + (C D)
				(A B) + C D

				A + B @ C
				A % B @ C
				A + -B @ C
				A % -B @ C
				A @ B @ C
				A * B @ C
				A @ B * C
				A @ B C
				(A @ B) C
				A % B % C
				A + B % C
				A % B + C
				A % B % C % D
				A ^ B % C % D
				A % B ^ C % D
				A % B % C ^ D

				A + (B @ C)
				A % (B @ C)
				A + ((-B) @ C)
				A % ((-B) @ C)
				(A @ B) @ C
				(A * B) @ C
				A @ (B * C)
				A @ (B * C)
				(A @ B) * C
				(A % B) % C
				(A + B) % C
				(A % B) + C
				((A % B) % C) % D
				((A ^ B) % C) % D
				((A % B) ^ C) % D
				((A % B) % C) ^ D
		""".strip("\r\n\t ").split("\n"):
			expression = expression.strip("\r\n\t ")
			if expression == "":
				continue
			self._assert_expression_reformattable(expression)

	def test_internal_input(self):
		(A, B, C, D) = (Variable("A"), Variable("B"), Variable("C"), Variable("D"))

		self.assertEqual(format_expression(A), "A")
		self.assertEqual(format_expression(A & B), "A B")
		self.assertEqual(format_expression(A & C & B), "A C B")

		self.assertEqual(format_expression((A & C) | B), "A C + B")
		self.assertEqual(format_expression((A | C) & B), "(A + C) B")
		self.assertEqual(format_expression((A | B) & (C | D)), "(A + B) (C + D)")

		self.assertEqual(format_expression((A @ B) @ C), "A @ B @ C")
		self.assertEqual(format_expression(A @ (B @ C)), "A @ (B @ C)")
		self.assertEqual(format_expression((A % B) % C), "A % B % C")
		self.assertEqual(format_expression(A % (B % C)), "A % (B % C)")

		self.assertEqual(format_expression(A ^ (B | C)), "A ^ (B + C)")
		self.assertEqual(format_expression(A | (B ^ C)), "A + (B ^ C)")
		self.assertEqual(format_expression(A | (B % C)), "A + (B % C)")
		self.assertEqual(format_expression(A % (B | C)), "A % (B + C)")

	@unittest.skipUnless(_run_slow_tests, "slow tests disabled (set environment variable UNITTEST_RUN_ALL=1)")
	def test_random_expressions(self):
		reg = RandomExpressionGenerator(6)
		for _ in range(100):
			expr = reg.generate(20)
			as_string = format_expression(expr)
			parsed = parse_expression(as_string)
			self.assertEqual(expr, parsed)

	def test_tex_output(self):
		(A, B, C, D) = (Variable("A"), Variable("B"), Variable("C"), Variable("D"))
		formatter = expression_formatter(OptionEnum(ExpressionFormat.TeX, [ "use-mathrm=0" ]))
		self.assertEqual(format_expression(A & B, ExpressionFormat.TeX), "\\mathrm{A B}")
		self.assertEqual(formatter(A & B), "A B")
		self.assertEqual(formatter(A & ~B), "A \\overline{B}")
		self.assertEqual(formatter(A & ~B & C), "A \\overline{B} C")
		self.assertEqual(formatter(A & ~B & ~C), "A \\overline{B}\\,\\overline{C}")
		self.assertEqual(formatter(A & ~B & ~C & ~D), "A \\overline{B}\\,\\overline{C}\\,\\overline{D}")
		self.assertEqual(formatter(A & ~B & ~C & ~D), "A \\overline{B}\\,\\overline{C}\\,\\overline{D}")
		self.assertEqual(formatter(A & ~B & C & ~D), "A \\overline{B} C \\overline{D}")

		self.assertEqual(formatter(A & (~B | C)), "A (\\overline{B} \\vee C)")

		self.assertEqual(formatter(parse_expression("A !B !C + B C")), "A \\overline{B}\\,\\overline{C} \\vee B C")
		self.assertEqual(formatter(parse_expression("A (B + C)")), "A (B \\vee C)")
		self.assertEqual(formatter(parse_expression("A C (B + D) + E + F")), "A C (B \\vee D) \\vee E \\vee F")
		self.assertEqual(formatter(parse_expression("A C !(B + !(D + !E)) + E + !F")), "A C \\overline{(B \\vee \\overline{(D \\vee \\overline{E})})} \\vee E \\vee \\overline{F}")
		self.assertEqual(formatter(parse_expression("A B !C D !E F !G !H !I !J")), "A B \\overline{C} D \\overline{E} F \\overline{G}\\,\\overline{H}\\,\\overline{I}\\,\\overline{J}")
		self.assertEqual(formatter(parse_expression("A @ B % C")), "A\\overset{\\sim}{\\wedge}B\\overset{\\sim}{\\vee}C")

		self.assertEqual(formatter(parse_expression("A !B !C + B C")), "A \\neg B \\neg C \\vee B C")
		self.assertEqual(formatter(parse_expression("A (B + C)")), "A (B \\vee C)")
		self.assertEqual(formatter(parse_expression("A C (B + D) + E + F")), "A C (B \\vee D) \\vee E \\vee F")
		self.assertEqual(formatter(parse_expression("A C !(B + !(D + !E)) + E + !F")), "A C \\neg (B \\vee \\neg (D \\vee \\neg E)) \\vee E \\vee \\neg F")
		self.assertEqual(formatter(parse_expression("A B !C D !E F !G !H !I !J")), "A B \\neg C D \\neg E F \\neg G \\neg H \\neg I \\neg J")
		self.assertEqual(formatter(parse_expression("A @ B % C")), "A\\overset{\\sim}{\\wedge}B\\overset{\\sim}{\\vee}C")

		self.assertEqual(formatter((~C & A & ~B) | (A & ~C) | (B & ~C & D)), "\\overline{C} A \\overline{B} \\vee A \\overline{C} \\vee B \\overline{C} D")
