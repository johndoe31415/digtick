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

from .ExpressionParser import ParseTreeElement, Operator, BinaryOperator, UnaryOperator, Constant, Variable, Parenthesis

class ExpressionTransformer():
	_KNOWN_TRANSFORMERS = { }
	_Name = None

	@classmethod
	def new(cls, transformer_name: str, *args, **kwargs):
		transformer_class = cls._KNOWN_TRANSFORMERS[transformer_name]
		return transformer_class(*args, **kwargs)

	def __init_subclass__(cls, **kwargs):
		super().__init_subclass__(**kwargs)
		assert(cls._Name is not None)
		assert(cls._Name not in cls._KNOWN_TRANSFORMERS)
		ExpressionTransformer._KNOWN_TRANSFORMERS[cls._Name] = cls

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
	_Name = "nand"

	def _transform_unary(self, expr: "Expression"):
		match expr.op:
			case Operator.Not:
				expr = expr.rhs @ 1

			case _: # pragma unreachable
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

			case _: # pragma unreachable
				raise NotImplementedError(expr.op)
		return self._transform(expr)

class NORLogicTransformer(ExpressionTransformer):
	_Name = "nor"

	def _transform_unary(self, expr: "Expression"):
		match expr.op:
			case Operator.Not:
				expr = expr.rhs % 0

			case _: # pragma unreachable
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

			case _: # pragma unreachable
				raise NotImplementedError(expr.op)
		return self._transform(expr)

class SimplificationTransformer(ExpressionTransformer):
	_Name = "simplify"

	def _transform_parenthesis(self, expr: "Expression"):
		match (expr.inner):
			case Parenthesis(inner):
				return Parenthesis(self._transform(inner))

			case Constant(value):
				return Constant(value)

			case Variable(varname):
				return Variable(varname)

		return Parenthesis(self._transform(expr.inner))

	def _transform_unary(self, expr: "Expression"):
		match (expr.op, expr.rhs):
			case (Operator.Not, Constant(value)):
				return Constant(value ^ 1)

		return UnaryOperator(expr.op, self._transform(expr.rhs))

	@staticmethod
	def _literal_sort_key(literal: ParseTreeElement):
		if isinstance(literal, Variable):
			return literal.varname
		elif isinstance(literal, UnaryOperator):
			return literal.rhs.varname
		else:
			raise NotImplementedError(f"Can only compare literals, not: {literal}")

	def _transform_binary(self, expr: "Expression"):
		match expr:
			# Annulment
			case BinaryOperator(_, Operator.And, Constant(0)) | BinaryOperator(Constant(0), Operator.And, _):
				return Constant(0)

			# Identity
			case BinaryOperator(side, Operator.And, Constant(1)) | BinaryOperator(Constant(1), Operator.And, side):
				return side

			# Annulment
			case BinaryOperator(_, Operator.Or, Constant(1)) | BinaryOperator(Constant(1), Operator.Or, _):
				return Constant(1)

			# Identity
			case BinaryOperator(side, Operator.Or, Constant(0)) | BinaryOperator(Constant(0), Operator.Or, side):
				return side

			# Idempotence
			case BinaryOperator(lhs, Operator.Or, rhs) if lhs.identical_to(rhs):
				return lhs

			# Idempotence
			case BinaryOperator(lhs, Operator.And, rhs) if lhs.identical_to(rhs):
				return lhs

			# Sort minterm literals alphabetically
			case BinaryOperator(_, Operator.And, _) if expr.is_minterm():
				terms = sorted(expr.collect_literals(), key = self._literal_sort_key)
				replacement = BinaryOperator.join(Operator.And, terms)
				return replacement

			# Sort maxterm literals alphabetically
			case BinaryOperator(_, Operator.Or, _) if expr.is_maxterm():
				terms = sorted(expr.collect_literals(), key = self._literal_sort_key)
				replacement = BinaryOperator.join(Operator.Or, terms)
				return replacement

			# Cascaded NAND inverter
			case BinaryOperator(BinaryOperator(other, Operator.Nand, Constant(1)), Operator.Nand, Constant(1)):
				return other

			# Cascaded NOR inverter
			case BinaryOperator(BinaryOperator(other, Operator.Nor, Constant(0)), Operator.Nor, Constant(0)):
				return other

			# Complement
			case BinaryOperator(lhs, Operator.And, rhs) if (lhs.variables == rhs.variables) and (lhs == ~rhs):
				return Constant(0)

			# Complement
			case BinaryOperator(lhs, Operator.Or, rhs) if (lhs.variables == rhs.variables) and (lhs == ~rhs):
				return Constant(1)

			# Parenthesis removal
			case BinaryOperator(lhs, op1, Parenthesis(BinaryOperator(_, op2, _) as rhs)) if (op1.precedence <= op2.precedence):
				return BinaryOperator(lhs, op1, rhs)

			# Parenthesis removal
			case BinaryOperator(Parenthesis(BinaryOperator(_, op1, _) as lhs), op2, rhs) if (op1.precedence <= op2.precedence):
				return BinaryOperator(lhs, op2, rhs)


		return BinaryOperator(self._transform(expr.lhs), expr.op, self._transform(expr.rhs))

	def transform(self, expression: ParseTreeElement):
		while True:
			transformed = self._transform(expression)
			if transformed.identical_to(expression):
				# No more simplification possible
				break
			else:
				expression = transformed

		# Remove outer layers of parenthesis
		while isinstance(transformed, Parenthesis):
			transformed = transformed.inner
		return transformed
