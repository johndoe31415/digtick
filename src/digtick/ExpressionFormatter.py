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

from .Enums import ExpressionFormatOpts
from .ExpressionParser import ParseTreeElement, Operator, Variable, Constant, UnaryOperator, BinaryOperator, Parenthesis

class ExpressionFormatterTex():
	def __init__(self, expression_format: ExpressionFormatOpts):
		self._format = expression_format
		self._ops = {
			Operator.Or: " \\vee ",
			Operator.And: " \\wedge ",
			Operator.Xor: " \\oplus ",
			Operator.Not: "\\neg ",
			Operator.Nand: "\\overset{\\sim}{\\wedge}",
			Operator.Nor: "\\overset{\\sim}{\\vee}",
		}
		if self._format["implicit-and"]:
			self._ops[Operator.And] = " "

	def _op(self, op):
		return self._ops[op]

	def _parenthesize(self, expr: ParseTreeElement, needs_parenthesis: bool):
		if needs_parenthesis:
			return (f"({self._format_expression(expr)[0]})", False)
		else:
			return self._format_expression(expr)

	def _format_expression(self, expr: ParseTreeElement):
		if isinstance(expr, Variable):
			return (expr.varname, False)
		elif isinstance(expr, BinaryOperator):
			lhs_needs_parenthesis = expr.lhs.precedence > expr.precedence
			rhs_needs_parenthesis = (expr.rhs.precedence > expr.precedence) or ((expr.rhs.precedence == expr.precedence) and (not expr.op.associative or (expr.op != expr.rhs.op)))

			(formatted_lhs, lhs_inverted) = self._parenthesize(expr.lhs, lhs_needs_parenthesis)
			(formatted_rhs, rhs_inverted) = self._parenthesize(expr.rhs, rhs_needs_parenthesis)

			if lhs_inverted and rhs_inverted and (expr.op == Operator.And) and self._format["implicit-and"]:
				# Need to separate those two because otherwise the overlines get combined
				op_str = "\\,"
			else:
				op_str = self._op(expr.op)
			return (f"{formatted_lhs}{op_str}{formatted_rhs}", rhs_inverted)
		elif isinstance(expr, UnaryOperator):
			if self._format["neg-overline"]:
				return (f"\\overline{{{self._format_expression(expr.rhs)[0]}}}", True)
			else:
				rhs_needs_parenthesis = (expr.rhs.precedence > expr.precedence)
				return (f"{self._op(expr.op)}{self._parenthesize(expr.rhs, rhs_needs_parenthesis)[0]}", False)
		elif isinstance(expr, Constant):
			if not self._format["math-constants"]:
				return (str(expr), False)
			elif expr.value == 0:
				return ("\\bot", False)
			else:
				return ("\\top", False)
		elif isinstance(expr, Parenthesis):
			return (f"({self._format_expression(expr.inner)[0]})", False)
		raise NotImplementedError(expr)

	def format_expression(self, expr: ParseTreeElement):
		if self._format["use-mathrm"]:
			return f"\\mathrm{{{self._format_expression(expr)[0]}}}"
		else:
			return self._format_expression(expr)[0]


class ExpressionFormatterTypst():
	def __init__(self, expression_format: ExpressionFormatOpts):
		self._format = expression_format
		self._ops = {
			Operator.Or: " or ",
			Operator.And: " and ",
			Operator.Xor: " xor ",
			Operator.Not: "not ",
			Operator.Nand: " bnand ",
			Operator.Nor: " bnor ",
		}
		if self._format["implicit-and"]:
			self._ops[Operator.And] = " "

	def _op(self, op):
		return self._ops[op]

	def _parenthesize(self, expr: ParseTreeElement, needs_parenthesis: bool):
		if needs_parenthesis:
			return (f"({self._format_expression(expr)[0]})", False)
		else:
			return self._format_expression(expr)

	def _format_expression(self, expr: ParseTreeElement):
		if isinstance(expr, Variable):
			if self._format["literals-upright"]:
				if len(expr.varname) == 1:
					return (f"upright({expr.varname})", False)
				else:
					return (f"upright(\"{expr.varname}\")", False)
			else:
				if len(expr.varname) == 1:
					return (expr.varname, False)
				else:
					return (f"\"{expr.varname}\"", False)
		elif isinstance(expr, BinaryOperator):
			lhs_needs_parenthesis = expr.lhs.precedence > expr.precedence
			rhs_needs_parenthesis = (expr.rhs.precedence > expr.precedence) or ((expr.rhs.precedence == expr.precedence) and (not expr.op.associative or (expr.op != expr.rhs.op)))

			(formatted_lhs, lhs_inverted) = self._parenthesize(expr.lhs, lhs_needs_parenthesis)
			(formatted_rhs, rhs_inverted) = self._parenthesize(expr.rhs, rhs_needs_parenthesis)

			if lhs_inverted and rhs_inverted and (expr.op == Operator.And) and self._format["implicit-and"]:
				# Need to separate those two because otherwise the overlines get combined
				op_str = " thin "
			else:
				op_str = self._op(expr.op)
			return (f"{formatted_lhs}{op_str}{formatted_rhs}", rhs_inverted)
		elif isinstance(expr, UnaryOperator):
			if self._format["neg-overline"]:
				return (f"bnot({self._format_expression(expr.rhs)[0]})", True)
			else:
				rhs_needs_parenthesis = (expr.rhs.precedence > expr.precedence)
				return (f"{self._op(expr.op)}{self._parenthesize(expr.rhs, rhs_needs_parenthesis)[0]}", False)
		elif isinstance(expr, Constant):
			if not self._format["math-constants"]:
				return (str(expr), False)
			elif expr.value == 0:
				return ("bot", False)
			else:
				return ("top", False)
		elif isinstance(expr, Parenthesis):
			return (f"({self._format_expression(expr.inner)[0]})", False)
		raise NotImplementedError(expr)

	def format_expression(self, expr: ParseTreeElement):
		return self._format_expression(expr)[0]

class ExpressionFormatterText():
	def __init__(self, expression_format: ExpressionFormatOpts):
		self._format = expression_format
		if self._format["pretty"]:
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
		if self._format["implicit-and"]:
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
				if self._format["pretty"] and (expr.op == Operator.Not):
					return f"{self.format_expression(expr.rhs)}\u0305"
				else:
					return f"{self._op(expr.op)}{self.format_expression(expr.rhs)}"
			else:
				return f"{self._op(expr.op)}{self._parenthesize(expr.rhs, needs_parenthesis = not isinstance(expr.rhs, Parenthesis))}"
		elif isinstance(expr, Constant):
			return str(expr)
		elif isinstance(expr, Parenthesis):
			return f"({self.format_expression(expr.inner)})"
		raise NotImplementedError(expr)

class ExpressionFormatterDot():
	def __init__(self, expression_format: ExpressionFormatOpts):
		self._format = expression_format
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

def expression_formatter(expression_format: ExpressionFormatOpts | None = None):
	if expression_format is None:
		expression_format = ExpressionFormatOpts(ExpressionFormatOpts.Value.Text)
	assert(isinstance(expression_format, ExpressionFormatOpts))
	if expression_format.value == ExpressionFormatOpts.Value.Internal:
		return str
	formatter_class = {
		ExpressionFormatOpts.Value.Text: ExpressionFormatterText,
		ExpressionFormatOpts.Value.TeX: ExpressionFormatterTex,
		ExpressionFormatOpts.Value.Typst: ExpressionFormatterTypst,
		ExpressionFormatOpts.Value.Dot: ExpressionFormatterDot,
	}[expression_format.value]
	formatter = formatter_class(expression_format)
	return formatter.format_expression

def format_expression(expression: ParseTreeElement, expression_format: ExpressionFormatOpts | None = None):
	assert(isinstance(expression, ParseTreeElement))
	return expression_formatter(expression_format = expression_format)(expression)
