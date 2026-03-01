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

from .ExpressionParser import ParseTreeElement, Operator, Variable, Constant, UnaryOperator, BinaryOperator, Parenthesis

class ExpressionFormatterTex():
	def __init__(self, neg_overline: bool = True, implicit_and: bool = True):
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

	def _format_expression(self, expr: ParseTreeElement, prev: ParseTreeElement | None = None):
		if isinstance(expr, Variable):
			return f"\\textnormal{{{expr.varname}}}"
		elif isinstance(expr, BinaryOperator):
			if (prev is None) or ((prev is not None) and ((prev.op == expr.op) or ((prev.op, expr.op) == (Operator.Or, Operator.And)))):
				return f"{self._format_expression(expr.lhs, expr)} {self._op(expr.op)} {self._format_expression(expr.rhs, expr)}"
			else:
				return f"({self._format_expression(expr.lhs, expr)} {self._op(expr.op)} {self._format_expression(expr.rhs, expr)})"
		elif isinstance(expr, UnaryOperator):
			if self._neg_overline:
				return f"\\overline{{{self._format_expression(expr.rhs, expr)}}}"
			else:
				return f"{self._op(expr.op)} {self._format_expression(expr.rhs, expr)}"
		elif isinstance(expr, Constant):
			return str(expr)
		elif isinstance(expr, Parenthesis):
			return f"({self._format_expression(expr.inner)})"
		raise NotImplementedError(expr)

	def format_expression(self, expr: ParseTreeElement):
		return self._format_expression(expr).replace("  ", " ")

class ExpressionFormatterText():
	def __init__(self, pretty_print: bool = False, implicit_and: bool = True):
		self._pretty_print = pretty_print
		self._implicit_and = implicit_and
		if pretty_print:
			self._ops = {
				Operator.Or: " ∨ ",
				Operator.And: " ∧ ",
				Operator.Xor: " ⊕ ",
				Operator.Not: "!",
				Operator.Nand: " NAND ",
				Operator.Nor: " NOR ",
			}
		else:
			self._ops = {
				Operator.Or: " + ",
				Operator.And: " * ",
				Operator.Xor: " ^ ",
				Operator.Not: "!",
				Operator.Nand: " @ ",
				Operator.Nor: " % ",
			}
		if self._implicit_and:
			self._ops[Operator.And] = " "

	def _op(self, op):
		return self._ops[op]

	def _parenthesize(self, expr: ParseTreeElement, needs_parenthesis: bool):
			if needs_parenthesis:
				return f"({self.format_expression(expr)})"
			else:
				return f"{self.format_expression(expr)}"

	def format_expression(self, expr: ParseTreeElement):
		if isinstance(expr, Variable):
			return expr.varname
		elif isinstance(expr, BinaryOperator):
			lhs_needs_parenthesis = expr.lhs.precedence > expr.precedence
			rhs_needs_parenthesis = (expr.rhs.precedence > expr.precedence) or ((expr.rhs.precedence == expr.precedence) and (not expr.op.associative or (expr.op != expr.rhs.op)))
			return f"{self._parenthesize(expr.lhs, lhs_needs_parenthesis)}{self._op(expr.op)}{self._parenthesize(expr.rhs, rhs_needs_parenthesis)}"
		elif isinstance(expr, UnaryOperator):
			if isinstance(expr.rhs, Variable) or isinstance(expr.rhs, Constant):
				if self._pretty_print and (expr.op == Operator.Not):
					return f"{self.format_expression(expr.rhs)}\u0305"
				else:
					return f"{self._op(expr.op)}{self.format_expression(expr.rhs)}"
			else:
				return f"{self._op(expr.op)}({self.format_expression(expr.rhs)})"
		elif isinstance(expr, Constant):
			return str(expr)
		elif isinstance(expr, Parenthesis):
			return f"({self.format_expression(expr.inner)})"
		raise NotImplementedError(expr)

class GraphvizFormatter():
	def __init__(self):
		self._op_label = {
			Operator.Or: "\\|\\|",
			Operator.And: "&&",
			Operator.Xor: " ⊕ ",
			Operator.Not: "~",
			Operator.Nand: "NAND",
			Operator.Nor: "NOR",
		}

	def format_expression(self, expr: ParseTreeElement):
		# Enumerate tree fully first so we can easily refer to the unique IDs
		# of nodes within the tree
		nodeno = { }
		for node in expr:
			nodeno[id(node)] = len(nodeno)

		lines = [ ]
		lines += [ "digraph g {" ]
		lines += [ "	node [ shape=box, style=\"filled,rounded\", fontname=\"Fira Mono\", fontsize=12, fontcolor=\"#111111\" ];" ]
		for node in expr:
			if isinstance(node, Variable):
				lines.append(f"	n{nodeno[id(node)]} [ label=\"{node.varname}\", fillcolor=\"#d9c2ff\" ];")
			elif isinstance(node, BinaryOperator):
				lines.append(f"	n{nodeno[id(node)]} [ label=\"{self._op_label[node.op]}\", fillcolor=\"#fff3b0\" ];")
				lines.append(f"	n{nodeno[id(node)]} -> n{nodeno[id(node.lhs)]};")
				lines.append(f"	n{nodeno[id(node)]} -> n{nodeno[id(node.rhs)]};")
			elif isinstance(node, UnaryOperator):
				lines.append(f"	n{nodeno[id(node)]} [ label=\"{self._op_label[node.op]}\", fillcolor=\"#b9d7ff\" ];")
				lines.append(f"	n{nodeno[id(node)]} -> n{nodeno[id(node.rhs)]};")
			elif isinstance(node, Parenthesis):
				lines.append(f"	n{nodeno[id(node)]} [ label=\"( )\", fillcolor=\"#c6f6c6\" ];")
				lines.append(f"	n{nodeno[id(node)]} -> n{nodeno[id(node.inner)]};")
			elif isinstance(node, Constant):
				lines.append(f"	n{nodeno[id(node)]} [ label=\"{node.value}\", fillcolor=\"#ffd2a6\" ];")
			else:
				raise NotImplementedError(type(node))
		lines += [ "}" ]
		return "\n".join(lines)

def format_expression(expression: ParseTreeElement, expression_format: str = "text", implicit_and: bool = True):
	assert(isinstance(expression, ParseTreeElement))
	match expression_format:
		case "internal":
			return str(expression)

		case "text":
			formatter = ExpressionFormatterText(pretty_print = False, implicit_and = implicit_and)

		case "pretty-text":
			formatter = ExpressionFormatterText(pretty_print = True, implicit_and = implicit_and)

		case "tex-tech":
			formatter = ExpressionFormatterTex(neg_overline = True, implicit_and = implicit_and)

		case "tex-math":
			formatter = ExpressionFormatterTex(neg_overline = False, implicit_and = implicit_and)

		case "dot":
			formatter = GraphvizFormatter()

		case _:
			raise NotImplementedError(expression_format)
	return formatter.format_expression(expression)
