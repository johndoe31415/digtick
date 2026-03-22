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
from .Tools import sort_signal_key

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

	def _debug(self, msg: str):
		pass

	def _transform_parenthesis(self, expr: "Expression"):
		# Parenthesis are never a needed element since the AST already
		# represents the order of operations perfectly. For simplifications,
		# they can be completely discarded.
		return self._transform(expr.inner)

	def _transform_unary(self, expr: "Expression"):
		self._debug(f"Transform unary begin: {expr}")
		expr = UnaryOperator(expr.op, self._transform(expr.rhs))
		match expr:
			case UnaryOperator(Operator.Not, Constant(value)):
				self._debug(f"  -> Inverted constant {value}")
				expr = Constant(value ^ 1)

			case UnaryOperator(Operator.Not, UnaryOperator(Operator.Not, rhs)):
				self._debug("  -> Double inversion")
				expr = rhs
		self._debug(f"Transform unary end: {expr}")
		return expr

	@classmethod
	def subexpression_sort_key(cls, subexpression: ParseTreeElement):
		if isinstance(subexpression, Variable):
			return (0, sort_signal_key(subexpression.varname), 0)
		elif isinstance(subexpression, UnaryOperator) and isinstance(subexpression.rhs, Variable):
			return (0, sort_signal_key(subexpression.rhs.varname), 1)
		elif isinstance(subexpression, BinaryOperator):
			return (subexpression.precedence, cls.subexpression_sort_key(subexpression.lhs), cls.subexpression_sort_key(subexpression.rhs))
		elif isinstance(subexpression, Parenthesis):
			return cls.subexpression_sort_key(subexpression.inner)
		else:
			return (subexpression.precedence, )

	def _transform_binary(self, expr: "Expression"):
		self._debug(f"Transform binary begin: {expr}")
		expr = BinaryOperator(self._transform(expr.lhs), expr.op, self._transform(expr.rhs))

		match expr:
			# Annulment
			case BinaryOperator(_, Operator.And, Constant(0)) | BinaryOperator(Constant(0), Operator.And, _):
				self._debug("  -> Annullment 0")
				expr = Constant(0)

			# Identity
			case BinaryOperator(side, Operator.And, Constant(1)) | BinaryOperator(Constant(1), Operator.And, side):
				self._debug(f"  -> Identity AND {side}")
				expr = side

			# Annulment
			case BinaryOperator(_, Operator.Or, Constant(1)) | BinaryOperator(Constant(1), Operator.Or, _):
				self._debug("  -> Annullment 1")
				expr = Constant(1)

			# Identity
			case BinaryOperator(side, Operator.Or, Constant(0)) | BinaryOperator(Constant(0), Operator.Or, side):
				self._debug(f"  -> Identity OR {side}")
				expr = side

			# Idempotence
			case BinaryOperator(lhs, Operator.Or, rhs) if lhs.identical_to(rhs):
				self._debug(f"  -> Idempotence OR {lhs}")
				expr = lhs

			# Idempotence
			case BinaryOperator(lhs, Operator.And, rhs) if lhs.identical_to(rhs):
				self._debug(f"  -> Idempotence AND {lhs}")
				expr = lhs

			# Cascaded NAND inverter
			case BinaryOperator(BinaryOperator(other, Operator.Nand, Constant(1)), Operator.Nand, Constant(1)):
				self._debug(f"  -> Cascaded NAND {other}")
				expr = other

			# Cascaded NOR inverter
			case BinaryOperator(BinaryOperator(other, Operator.Nor, Constant(0)), Operator.Nor, Constant(0)):
				self._debug(f"  -> Cascaded NOR {other}")
				expr = other

			# Complement
			case BinaryOperator(lhs, Operator.And, rhs) if lhs.complements(rhs):
				self._debug(f"  -> Complement 0")
				expr = Constant(0)

			# Complement
			case BinaryOperator(_, Operator.Or, _) if expr.is_tautology():
				self._debug(f"  -> Complement 1")
				expr = Constant(1)

			# Sort subexpressions alphabetically
			case BinaryOperator(_, op, _) if op in [ Operator.And, Operator.Or ]:
				terms = expr.gather()
				self._debug(f"  -> Sort subexpressions {op.name} (count = {len(terms)})")
				sorted_terms = sorted(set(self._transform(term) for term in terms), key = self.subexpression_sort_key)
				expr = BinaryOperator.join(op, sorted_terms)

		self._debug(f"Transform binary end: {expr}")
		return expr

	def transform(self, expression: ParseTreeElement):
		while True:
			self._debug(f"Simplification run INPUT  = {expression}")
			transformed = self._transform(expression)
			self._debug(f"Simplification run OUTPUT = {expression}")
			if transformed.identical_to(expression):
				# No more simplification possible
				self._debug("Simplification finished.")
				break
			else:
				expression = transformed
		return transformed


class ShuffleTransformer(ExpressionTransformer):
	_Name = "shuffle"

	def __init__(self, prng: "PRNG"):
		self._prng = prng

	def _transform_binary(self, expr: "Expression"):
		if expr.op in [ Operator.And, Operator.Or ]:
			terms = [ self._transform(term) for term in expr.gather() ]
			self._prng.shuffle(terms)
			return BinaryOperator.join(expr.op, terms)

		return BinaryOperator(self._transform(expr.lhs), expr.op, self._transform(expr.rhs))


class SortTransformer(ExpressionTransformer):
	_Name = "sort"

	def _transform_binary(self, expr: "Expression"):
		if expr.op in [ Operator.And, Operator.Or ]:
			terms = [ self._transform(term) for term in expr.gather() ]
			sorted_terms = sorted([ self._transform(term) for term in terms ], key = SimplificationTransformer.subexpression_sort_key)
			return BinaryOperator.join(expr.op, sorted_terms)
		return BinaryOperator(self._transform(expr.lhs), expr.op, self._transform(expr.rhs))
