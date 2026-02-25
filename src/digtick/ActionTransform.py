#	digtick - Digital systems toolkit: simplify, minimize and transform Boolean expressions, draw KV-maps, etc.
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

from .MultiCommand import BaseAction
from .ExpressionParser import parse_expression, ParseTreeElement, Operator, BinaryOperator, UnaryOperator, Constant, Variable, Parenthesis
from .ExpressionFormatter import format_expression

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
				expr = expr.rhs @ 1

			case _:
				raise NotImplementedError(expr.op)
		return self._transform(expr)

	def _transform_binary(self, expr: "Expression"):
		match expr.op:
			case Operator.Or:
				expr = (expr.lhs @ 1) @ (expr.rhs @ 1)

			case Operator.Nor:
				expr = ~(expr.lhs | expr.rhs)

			case Operator.And:
				expr = (expr.lhs @ expr.rhs) @ 1

			case Operator.Nand:
				return BinaryOperator(self._transform(expr.lhs), "@", self._transform(expr.rhs))

			case Operator.Xor:
				option1 = ~expr.lhs @ expr.rhs
				option2 = expr.lhs @ ~expr.rhs
				expr = option1 @ option2

			case _:
				raise NotImplementedError(expr.op)
		return self._transform(expr)

class NORLogicTransformer(ExpressionTransformer):
	def _transform_unary(self, expr: "Expression"):
		match expr.op:
			case Operator.Not:
				expr = expr.rhs % 0

			case _:
				raise NotImplementedError(expr.op)
		return self._transform(expr)

	def _transform_binary(self, expr: "Expression"):
		match expr.op:
			case Operator.Or:
				expr = ~(expr.lhs % expr.rhs)

			case Operator.Nor:
				return self._transform(expr.lhs) % self._transform(expr.rhs)

			case Operator.And:
				expr = ~(~expr.lhs | ~expr.rhs)

			case Operator.Nand:
				expr = ~(expr.lhs & expr.rhs)

			case Operator.Xor:
				option1 = ~expr.lhs % expr.rhs
				option2 = expr.lhs % ~expr.rhs
				expr = ~(option1 % option2)

			case _:
				raise NotImplementedError(expr.op)
		return self._transform(expr)

class SimplificationTransformer(ExpressionTransformer):
	def _transform_parenthesis(self, expr: "Expression"):
		match (expr.inner):
			case (Parenthesis(inner)):
				return Parenthesis(self._transform(inner))
		return expr

	def _transform_unary(self, expr: "Expression"):
		match (expr.op, expr.rhs):
			case (Operator.Not, Constant(0)):
				return Constant(1)

			case (Operator.Not, Constant(1)):
				return Constant(0)

			case (Operator.Parenthesis, Operator.Parenthesis(inner)):
				return Constant(0)

		return expr

	def _transform_binary(self, expr: "Expression"):
		match (expr.lhs, expr.op, expr.rhs):
			case (_, Operator.And, Constant(0)):
				return Constant(0)

			case (lhs, Operator.And, Constant(1)):
				return lhs

			case (_, Operator.Or, Constant(1)):
				return Constant(1)

			case (lhs, Operator.Or, Constant(0)):
				return lhs

			case (lhs, Operator.Or, rhs) if (lhs.identical_to(rhs)):
				return lhs

			case (lhs, Operator.And, rhs) if (lhs.identical_to(rhs)):
				return lhs
		return expr


class ActionTransform(BaseAction):
	def run(self):
		expr = parse_expression(self._args.expression)

		for transformation_name in self._args.transform:
			match transformation_name:
				case "nand":
					transformer = NANDLogicTransformer()

				case "nor":
					transformer = NORLogicTransformer()

				case "simplify":
					transformer = SimplificationTransformer()

				case _:
					raise NotImplementedError(self._args.logic)

			transformed = transformer.transform(expr)
			print(format_expression(expression = transformed, expression_format = self._args.expr_format, implicit_and = not self._args.no_implicit_and))
			assert(expr == transformed)
