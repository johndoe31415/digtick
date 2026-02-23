#	digtool - Tool to compute and simplify problems in digital systems
#	Copyright (C) 2022-2026 Johannes Bauer
#
#	This file is part of digtool.
#
#	digtool is free software; you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation; this program is ONLY licensed under
#	version 3 of the License, later versions are explicitly excluded.
#
#	digtool is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with digtool; if not, write to the Free Software
#	Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#	Johannes Bauer <JohannesBauer@gmx.de>

from .ExpressionParser import ParsedExpression, Operator, Variable, Constant, UnaryOperator, BinaryOperator, Parenthesis

class ExpressionFormatterTex():
	def __init__(self, expr, neg_overline = True, implicit_and = True):
		self._expr = expr
		self._neg_overline = neg_overline
		self._implicit_and = implicit_and
		self._ops = {
			Operator.Or: "\\vee",
			Operator.And: "\\wedge",
			Operator.Xor: "\\oplus",
			Operator.Not: "\\neg",
			Operator.Nand: "\\boxdot",
		}
		if implicit_and:
			self._ops[Operator.And] = "\\ "

	def _op(self, op):
		return self._ops[op]

	def _fmt(self, expr, prev = None):
		if isinstance(expr, Variable):
			return f"\\textnormal{{{expr.varname}}}"
		elif isinstance(expr, BinaryOperator):
			if (prev is None) or ((prev is not None) and ((prev.op == expr.op) or ((prev.op, expr.op) == (Operator.Or, Operator.And)))):
				return f"{self._fmt(expr.lhs, expr)} {self._op(expr.op)} {self._fmt(expr.rhs, expr)}"
			else:
				return f"({self._fmt(expr.lhs, expr)} {self._op(expr.op)} {self._fmt(expr.rhs, expr)})"
		elif isinstance(expr, UnaryOperator):
			if self._neg_overline:
				return f"\\overline{{{self._fmt(expr.rhs, expr)}}}"
			else:
				return f"{self._op(expr.op)} {self._fmt(expr.rhs, expr)}"
		elif isinstance(expr, Constant):
			return str(expr)
		elif isinstance(expr, Parenthesis):
			return f"({self._fmt(expr.inner)})"
		raise NotImplementedError(expr)

	def __str__(self):
		return self._fmt(self._expr.expr).replace("  ", " ")

class ExpressionFormatterText():
	def __init__(self, expr, pretty_print: bool = False, implicit_and: bool = True):
		self._expr = expr
		self._pretty_print = pretty_print
		self._implicit_and = implicit_and
		if pretty_print:
			self._ops = {
				Operator.Or: " ∨ ",
				Operator.And: " ∧ ",
				Operator.Xor: " ⊕ ",
				Operator.Not: "!",
				Operator.Nand: " NAND ",
			}
		else:
			self._ops = {
				Operator.Or: " + ",
				Operator.And: " * ",
				Operator.Xor: " XOR ",
				Operator.Not: "!",
				Operator.Nand: " NAND ",
			}
		if self._implicit_and:
			self._ops[Operator.And] = " "

	def _op(self, op):
		return self._ops[op]

	def _fmt(self, expr, prev = None):
		if isinstance(expr, Variable):
			return expr.varname
		elif isinstance(expr, BinaryOperator):
			if (prev is None) or ((prev is not None) and ((prev.op == expr.op) or ((prev.op, expr.op) == (Operator.Or, Operator.And)))):
				return f"{self._fmt(expr.lhs, expr)}{self._op(expr.op)}{self._fmt(expr.rhs, expr)}"
			else:
				return f"({self._fmt(expr.lhs, expr)}{self._op(expr.op)}{self._fmt(expr.rhs, expr)})"
		elif isinstance(expr, UnaryOperator):
			if isinstance(expr.rhs, Variable) or isinstance(expr.rhs, Constant):
				if self._pretty_print and (expr.op == Operator.Not):
					return f"{self._fmt(expr.rhs, expr)}\u0305"
				else:
					return f"{self._op(expr.op)}{self._fmt(expr.rhs, expr)}"
			else:
				return f"{self._op(expr.op)}({self._fmt(expr.rhs, expr)})"
		elif isinstance(expr, Constant):
			return str(expr)
		elif isinstance(expr, Parenthesis):
			return f"({self._fmt(expr.inner)})"
		raise NotImplementedError(expr)

	def __str__(self):
		return self._fmt(self._expr.expr)

def format_expression(expression: ParsedExpression, expression_format: str = "text", implicit_and: bool = True):
	assert(isinstance(expression, ParsedExpression))
	match expression_format:
		case "internal":
			return str(expression)

		case "text":
			return str(ExpressionFormatterText(expression, pretty_print = False, implicit_and = implicit_and))

		case "pretty-text":
			return str(ExpressionFormatterText(expression, pretty_print = True, implicit_and = implicit_and))

		case "tex-tech":
			return str(ExpressionFormatterTex(expression, neg_overline = True, implicit_and = implicit_and))

		case "tex-math":
			return str(ExpressionFormatterTex(expression, neg_overline = False, implicit_and = implicit_and))

		case _:
			raise NotImplementedError(expression_format)
