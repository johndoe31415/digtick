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

from .MultiCommand import BaseAction
from .ExpressionParser import parse_expression, ParsedExpression, Operator, BinaryOperator, UnaryOperator, Constant, Variable, Parenthesis

class ExpressionTransformer():
	def __init__(self, expr):
		self._expr = expr.expr

	def _transform_unary(self, expr):
		return UnaryOperator(op = expr.op, rhs = expr.rhs)

	def _transform_binary(self, expr):
		return BinaryOperator(lhs = expr.lhs, op = expr.op, rhs = expr.rhs)

	def _transform_constant(self, expr):
		return expr

	def _transform_variable(self, expr):
		return expr

	def _transform(self, node):
		if isinstance(node, BinaryOperator):
			return self._transform_binary(node)
		elif isinstance(node, UnaryOperator):
			return self._transform_unary(node)
		elif isinstance(node, Constant):
			return self._transform_constant(node)
		elif isinstance(node, Variable):
			return self._transform_variable(node)
		elif isinstance(node, Parenthesis):
			return Parenthesis(self._transform(node.inner))
		else:
			raise NotImplementedError(type(node))

	def run(self):
		return ParsedExpression(self._transform(self._expr))


class NANDLogicTransformer(ExpressionTransformer):
	def _transform_unary(self, expr: "Expression"):
		match expr.op:
			case Operator.Not:
				return Parenthesis(BinaryOperator(self._transform(expr.rhs), Operator.Nand, Constant(1)))

			case _:
				raise NotImplementedError(expr.op)

	def _transform_binary(self, expr: "Expression"):
		match expr.op:
			case Operator.Or:
				return Parenthesis(BinaryOperator(self._transform(UnaryOperator("!", self._transform(expr.lhs))), "@", self._transform(UnaryOperator("!", self._transform(expr.rhs)))))

			case Operator.Nor:
				return self._transform(UnaryOperator("!", BinaryOperator(self._transform(expr.lhs), "|", self._transform(expr.rhs))))

			case Operator.And:
				return Parenthesis(BinaryOperator(Parenthesis(BinaryOperator(self._transform(expr.lhs), "@", self._transform(expr.rhs))), "@", Constant(1)))

			case Operator.Nand:
				return BinaryOperator(self._transform(expr.lhs), "@", self._transform(expr.rhs))

			case Operator.Xor:
				option1 = Parenthesis(BinaryOperator(Parenthesis(BinaryOperator(self._transform(expr.lhs), "@", Constant(1))), "@", self._transform(expr.rhs)))
				option2 = Parenthesis(BinaryOperator(self._transform(expr.lhs), "@", Parenthesis(BinaryOperator(self._transform(expr.rhs), "@", Constant(1)))))
				return self._transform(BinaryOperator(option1, "@", option2))

			case _:
				raise NotImplementedError(expr.op)

class NORLogicTransformer(ExpressionTransformer):
	def _transform_unary(self, expr: "Expression"):
		match expr.op:
			case Operator.Not:
				return Parenthesis(BinaryOperator(self._transform(expr.rhs), Operator.Nor, Constant(0)))

			case _:
				raise NotImplementedError(expr.op)

	def _transform_binary(self, expr: "Expression"):
		match expr.op:
			case Operator.Or:
				return self._transform(UnaryOperator("!", Parenthesis(BinaryOperator(self._transform(expr.lhs), Operator.Nor, self._transform(expr.rhs)))))

			case Operator.Nor:
				return BinaryOperator(self._transform(expr.lhs), Operator.Nor, self._transform(expr.rhs))

			case Operator.And:
				return self._transform(Parenthesis(BinaryOperator(UnaryOperator("!", expr.lhs), "#", UnaryOperator("!", expr.rhs))))

			case Operator.Nand:
				return self._transform(UnaryOperator("!", BinaryOperator(expr.lhs, Operator.And, expr.rhs)))

			case Operator.Xor:
				# (((A # 0) # B) # (A # (B # 0))) # 0
				option1 = Parenthesis(BinaryOperator(expr.lhs, Operator.Nor, UnaryOperator("!", expr.rhs)))
				option2 = Parenthesis(BinaryOperator(UnaryOperator("!", expr.lhs), Operator.Nor, expr.rhs))
				return self._transform(UnaryOperator("!", BinaryOperator(option1, Operator.Nor, option2)))

			case _:
				raise NotImplementedError(expr.op)

class ActionTransform(BaseAction):
	def run(self):
		expr = parse_expression(self._args.expression)
		match self._args.logic:
			case "nand":
				xform = NANDLogicTransformer(expr)

			case "nor":
				xform = NORLogicTransformer(expr)

			case _:
				raise NotImplementedError(self._args.logic)

		xformed = xform.run()
		print(xformed)
