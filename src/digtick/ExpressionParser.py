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

import enum
import functools
from . import tpg

class Operator(enum.Enum):
	Or = "+"
	And = "*"
	Xor = "^"
	Not = "!"
	Nand = "@"
	Nor = "%"

	@property
	def precedence(self) -> int:
		"""Lowest precedence value is highest."""
		return {
			Operator.Not: 9,
			Operator.And: 10,
			Operator.Nand: 11,
			Operator.Or: 12,
			Operator.Xor: 12,
			Operator.Nor: 12,
		}[self]

	@property
	def associative(self) -> bool:
		return {
			Operator.And: True,
			Operator.Nand: False,
			Operator.Or: True,
			Operator.Xor: True,
			Operator.Nor: False,
		}[self]

	@classmethod
	def lookup(cls, value: str):
		return {
			"+":	cls.Or,
			"|":	cls.Or,
			"*":	cls.And,
			"&":	cls.And,
			"^":	cls.Xor,
			"!":	cls.Not,
			"-":	cls.Not,
			"~":	cls.Not,
			"@":	cls.Nand,
			"%":	cls.Nor,
		}[value]

class ParseTreeElement():
	_Elements = { }

	@property
	def state_count(self):
		return 1 << len(self.variables)

	@functools.cached_property
	def variables(self):
		varnames = set()
		for element in self:
			if isinstance(element, Variable):
				varnames.add(element.varname)
		varnames = tuple(sorted(varnames))
		return varnames

	def _traverse(self):
		yield self
		if isinstance(self, UnaryOperator):
			yield from self.rhs._traverse()
		elif isinstance(self, BinaryOperator):
			yield from self.lhs._traverse()
			yield from self.rhs._traverse()
		elif isinstance(self, Parenthesis):
			yield from self.inner._traverse()

	def table(self):
		for value in range(self.state_count):
			value_dict = { varname: int((value & (1 << (len(self.variables) - 1 - varno))) != 0) for (varno, varname) in enumerate(self.variables) }
			evaluation = self.evaluate(value_dict)
			yield (value_dict, evaluation)

	def minterms(self):
		for (value_dict, evaluation) in self.table():
			if evaluation == 1:
				yield value_dict

	def maxterms(self):
		for (value_dict, evaluation) in self.table():
			if evaluation == 0:
				yield value_dict

	def find_minterms(self):
		if isinstance(self, BinaryOperator) and (self.op == Operator.Or):
			yield from self.lhs.find_minterms()
			yield from self.rhs.find_minterms()
		else:
			yield self

	def find_maxterms(self):
		if isinstance(self, BinaryOperator) and (self.op == Operator.And):
			yield from self.lhs.find_maxterms()
			yield from self.rhs.find_maxterms()
		else:
			yield self

	def compare_to_expression(self, other: "ParseTreeElement"):
		e1_vars = set(self.variables)
		e2_vars = set(other.variables)
		intersection = e1_vars & e2_vars

		if (intersection != e1_vars) and (intersection != e2_vars):
			raise ValueError("Cannot compare expressions with different variables.")

		if intersection == e2_vars:
			# self has more variables
			(dominant_expr, subordinate_expr) = (self, other)
		else:
			# other has more variables
			(dominant_expr, subordinate_expr) = (other, self)

		for (value_dict, eval1) in dominant_expr.table():
			eval2 = subordinate_expr.evaluate(value_dict)
			yield (value_dict, eval1, eval2)

	def __eq__(self, other: "ParseTreeElement"):
		for (value_dict, eval1, eval2) in self.compare_to_expression(other):
			if eval1 != eval2:
				return False
		return True

	def _wrap(self, expr: "ParseTreeElement | int | str") -> "ParseTreeElement":
		if isinstance(expr, ParseTreeElement):
			return expr
		elif isinstance(expr, int):
			return self._Elements["Constant"](expr)
		elif isinstance(expr, str):
			return self._Elements["Variable"](expr)
		else:
			raise ValueError(type(expr))

	def __invert__(self):
		return self._Elements["UnaryOperator"](Operator.Not, self)

	def __or__(self, rhs: "ParseTreeElement"):
		return self._Elements["BinaryOperator"](self, Operator.Or, self._wrap(rhs))

	def __and__(self, rhs: "ParseTreeElement"):
		return self._Elements["BinaryOperator"](self, Operator.And, self._wrap(rhs))

	def __xor__(self, rhs: "ParseTreeElement"):
		return self._Elements["BinaryOperator"](self, Operator.Xor, self._wrap(rhs))

	def __matmul__(self, rhs: "ParseTreeElement"):
		return self._Elements["BinaryOperator"](self, Operator.Nand, self._wrap(rhs))

	def __mod__(self, rhs: "ParseTreeElement"):
		return self._Elements["BinaryOperator"](self, Operator.Nor, self._wrap(rhs))

	def __init_subclass__(cls, **kwargs):
		super().__init_subclass__(**kwargs)
		ParseTreeElement._Elements[cls.__name__] = cls

	def __iter__(self):
		yield from self._traverse()

class Variable(ParseTreeElement):
	__match_args__ = ("varname", )

	def __init__(self, varname):
		self._varname = varname

	@property
	def precedence(self) -> int:
		return 5

	@property
	def varname(self):
		return self._varname

	def evaluate(self, var_dict: dict):
		return var_dict[self.varname]

	def identical_to(self, other: ParseTreeElement) -> bool:
		return isinstance(other, Variable) and (self.varname == other.varname)

	def __repr__(self):
		return self.varname

class Constant(ParseTreeElement):
	__match_args__ = ("value", )

	def __init__(self, value: int):
		assert(value in (0, 1))
		self._value = value

	@property
	def precedence(self) -> int:
		return 5

	@property
	def value(self):
		return self._value

	def evaluate(self, var_dict: dict):
		return self.value

	def identical_to(self, other: ParseTreeElement) -> bool:
		return isinstance(other, Constant) and (self.value == other.value)

	def __repr__(self):
		return str(self.value)

class UnaryOperator(ParseTreeElement):
	def __init__(self, op, rhs):
		if isinstance(op, Operator):
			self._op = op
		else:
			self._op = Operator.lookup(op)
		self._rhs = rhs

	@property
	def precedence(self) -> int:
		return self._op.precedence

	@property
	def op(self):
		return self._op

	@property
	def rhs(self):
		return self._rhs

	def evaluate(self, var_dict: dict):
		assert(self._op == Operator.Not)
		return int(not self.rhs.evaluate(var_dict))

	def identical_to(self, other: ParseTreeElement) -> bool:
		return isinstance(other, UnaryOperator) and (self.op == other.op) and (self.rhs.identical_to(other.rhs))

	def __repr__(self):
		return f"[{self.op.value}{self.rhs}]"

class BinaryOperator(ParseTreeElement):
	__match_args__ = ("lhs", "op", "rhs")

	def __init__(self, lhs: ParseTreeElement, op: Operator | str, rhs: ParseTreeElement):
		self._lhs = lhs
		if isinstance(op, Operator):
			self._op = op
		else:
			self._op = Operator.lookup(op)
		self._rhs = rhs

	@property
	def precedence(self) -> int:
		return self._op.precedence

	@property
	def lhs(self):
		return self._lhs

	@property
	def op(self):
		return self._op

	@property
	def rhs(self):
		return self._rhs

	@classmethod
	def join(cls, op: Operator, terms: ParseTreeElement) -> ParseTreeElement:
		result = None
		for term in terms:
			if result is None:
				result = term
			else:
				result = BinaryOperator(result, op, term)
		if result is None:
			raise ValueError("Cannot join empty sequence.")
		return result

	def identical_to(self, other: ParseTreeElement) -> bool:
		return isinstance(other, BinaryOperator) and (self.op == other.op) and (self.lhs.identical_to(other.lhs)) and (self.rhs.identical_to(other.rhs))

	def evaluate(self, var_dict: dict):
		lhs = self.lhs.evaluate(var_dict)
		rhs = self.rhs.evaluate(var_dict)
		fnc = {
			Operator.Or: lambda x, y: x | y,
			Operator.And: lambda x, y: x & y,
			Operator.Xor: lambda x, y: x ^ y,
			Operator.Nand: lambda x, y: int(not (x & y)),
			Operator.Nor: lambda x, y: int(not (x | y)),
		}[self.op]
		return fnc(lhs, rhs)

	def __repr__(self):
		return f"[{self.lhs} {self.op.value} {self.rhs}]"

class Parenthesis(ParseTreeElement):
	__match_args__ = ("inner", )

	def __init__(self, inner: ParseTreeElement):
		self._inner = inner

	@property
	def precedence(self) -> int:
		return 5

	@property
	def inner(self):
		return self._inner

	def evaluate(self, var_dict: dict):
		return self._inner.evaluate(var_dict)

	def identical_to(self, other: ParseTreeElement) -> bool:
		return isinstance(other, Parenthesis) and (self.inner.identical_to(other.inner))

	def __repr__(self):
		return f"({self.inner})"

class ExpressionParser(tpg.Parser):
	r"""
		separator space '\s+';

		token or_op     '[|+]';
		token and_op    '[&*]';
		token xor_op    '[\^]';
		token nand_op   '@';
		token nor_op    '%';
		token neg_op	'[!-]';
		token const 	'[01]';
		token variable  '[a-zA-Z_][a-zA-Z0-9_]*'		$ Variable

		START/e ->
				Expr/e
		;

		Expr/lhs -> Term/lhs ( or_op/op Term/rhs		$ lhs = BinaryOperator(lhs, op, rhs)
							| xor_op/op Term/rhs		$ lhs = BinaryOperator(lhs, op, rhs)
							| nor_op/op Term/rhs		$ lhs = BinaryOperator(lhs, op, rhs)
					)*
		;

		Term/lhs -> Factor/lhs ( nand_op/op Factor/rhs		$ lhs = BinaryOperator(lhs, op, rhs)
					)*
		;

		Factor/lhs -> Atom/lhs ( and_op/op Atom/rhs		$ lhs = BinaryOperator(lhs, op, rhs)
							| Atom/rhs					$ lhs = BinaryOperator(lhs, "*", rhs)
					)*
		;

		Atom/a ->
				variable/a
			|	const/a					$ a = Constant(int(a))
			|	neg_op/op Atom/a		$ a = UnaryOperator(op, a)
			| '\(' Expr/inner '\)'		$ a = Parenthesis(inner)
		;

	"""

def parse_expression(expr: str, default_empty: str | None = None) -> ParseTreeElement:
	if (expr == ""):
		if default_empty is None:
			raise ValueError("Expression may not be empty unless default empty is given.")
		else:
			expr = default_empty
	parser = ExpressionParser()
	parse_result = parser(expr)
	return parse_result

if __name__ == "__main__":
	parser = ExpressionParser()

	testcases = [
			"A + B",
			"A + B + C",
			"A + (B + C)",
			"A * B + C",
			"A + B * C",
			"A + B ^ C",
			"A ^ B ^ C",
			"A ^ B + C",
			"A B C + !A !B !C + A !B C Foo",
			"A ^ !B",
			"A ^ !B + C",
			"A ^ !(B + C)",
			"!(A ^ B)",
			"A + 1 + 0",
	]
	for input_value in testcases:
		try:
			parsed = parser(input_value)
			print(parsed)
		except Exception as e:
			print(tpg.exc())
			raise

	A = Variable("A")
	Zero = Constant(0)
	print((A & 1) | (A & 0) == A)
