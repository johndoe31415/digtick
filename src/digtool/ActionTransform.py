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
from .ExpressionParser import parse_expression, ParseTreeElement, Operator, BinaryOperator, UnaryOperator, Constant, Variable, Parenthesis

class ExpressionTransformer():
	def _transform_unary(self, expr: ParseTreeElement):
		return UnaryOperator(op = expr.op, rhs = self._transform(expr.rhs))

	def _transform_binary(self, expr: ParseTreeElement):
		return BinaryOperator(lhs = self._transform(expr.lhs), op = expr.op, rhs = self._transform(expr.rhs))

	def _transform_constant(self, expr: ParseTreeElement):
		return expr

	def _transform_variable(self, expr: ParseTreeElement):
		return expr

	def _transform_parenthesis(self, expr: ParseTreeElement):
		return Parenthesis(self._transform(expr.inner))

	def _transform(self, expr: ParseTreeElement):
		if isinstance(expr, BinaryOperator):
			return self._transform_binary(expr)
		elif isinstance(expr, UnaryOperator):
			return self._transform_unary(expr)
		elif isinstance(expr, Constant):
			return self._transform_constant(expr)
		elif isinstance(expr, Variable):
			return self._transform_variable(expr)
		elif isinstance(expr, Parenthesis):
			return self._transform_parenthesis(expr)
		else:
			raise NotImplementedError(type(expr))

	def transform(self, expression: ParseTreeElement):
		return self._transform(expression)

class NANDLogicTransformer(ExpressionTransformer):
	def _transform_unary(self, expr: "Expression"):
		match expr.op:
			case Operator.Not:
				expr = Parenthesis(expr.rhs @ 1)

			case _:
				raise NotImplementedError(expr.op)
		return self._transform(expr)

	def _transform_binary(self, expr: "Expression"):
		match expr.op:
			case Operator.Or:
				expr = Parenthesis(Parenthesis(expr.lhs @ 1) @ Parenthesis(expr.rhs @ 1))

			case Operator.Nor:
				expr = ~(expr.lhs | expr.rhs)

			case Operator.And:
				expr = Parenthesis(Parenthesis(expr.lhs @ expr.rhs) @ 1)

			case Operator.Nand:
				return BinaryOperator(self._transform(expr.lhs), "@", self._transform(expr.rhs))

			case Operator.Xor:
				option1 = Parenthesis(Parenthesis(expr.lhs @ 1) @ expr.rhs)
				option2 = Parenthesis(expr.lhs @ Parenthesis(expr.rhs @ 1))
				expr = option1 @ option2

			case _:
				raise NotImplementedError(expr.op)
		return self._transform(expr)

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
				transformer = NANDLogicTransformer()

			case "nor":
				transformer = NORLogicTransformer()

			case _:
				raise NotImplementedError(self._args.logic)

		transformed = transformer.transform(expr)
		print(transformed)
		assert(expr == transformed)
