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

from .BaseAction import BaseAction
from .ExpressionParser import parse_expression, ParsedExpression, Operator, BinaryOperator, UnaryOperator, Constant, Variable


class ExpressionTransformer():
	def __init__(self, expr):
		self._expr = expr.expr

	def _transform_unary(self, expr, rhs):
		return UnaryOperator(op = expr.op, rhs = rhs)

	def _transform_binary(self, expr, lhs, rhs):
		return BinaryOperator(lhs = lhs, op = expr.op, rhs = rhs)

	def _transform_constant(self, expr):
		return expr

	def _transform_variable(self, expr):
		return expr

	def _transform(self, node):
		if isinstance(node, BinaryOperator):
			return self._transform_binary(node, node.lhs, node.rhs)
		elif isinstance(node, UnaryOperator):
			return self._transform_unary(node, node.rhs)
		elif isinstance(node, Constant):
			return self._transform_constant(node)
		elif isinstance(node, Variable):
			return self._transform_variable(node)
		else:
			raise NotImplementedError(type(node))

	def run(self):
		return ParsedExpression(self._transform(self._expr))


class NANDLogicTransformer(ExpressionTransformer):
	def _transform_unary(self, expr, rhs):
		if expr.op == Operator.Not:
			return BinaryOperator(self._transform(rhs), Operator.Nand, Constant(1))
		else:
			raise NotImplementedError()

	def _transform_binary(self, expr, lhs, rhs):
		if expr.op == Operator.And:
			return BinaryOperator(BinaryOperator(self._transform(lhs), "@", self._transform(rhs)), "@", Constant(1))
		elif expr.op == Operator.Or:
			return BinaryOperator(self._transform(UnaryOperator("!", self._transform(lhs))), "@", self._transform(UnaryOperator("!", self._transform(rhs))))
		elif expr.op == Operator.Nand:
			return BinaryOperator(self._transform(lhs), "@", self._transform(rhs))
		elif expr.op == Operator.Nor:
			return self._transform(UnaryOperator("!", BinaryOperator(self._transform(lhs), "|", self._transform(rhs))))
		elif expr.op == Operator.Xor:
			option1 = BinaryOperator(BinaryOperator(self._transform(lhs), "@", Constant(1)), "@", self._transform(rhs))
			option2 = BinaryOperator(self._transform(lhs), "@", BinaryOperator(self._transform(rhs), "@", Constant(1)))
			return self._transform(BinaryOperator(option1, "@", option2))
		else:
			raise NotImplementedError(expr.op)


class ActionTransform(BaseAction):
	def run(self):
		expr = parse_expression(self._args.expression)
		xform = NANDLogicTransformer(expr)
		xformed = xform.run()
		print(xformed)
