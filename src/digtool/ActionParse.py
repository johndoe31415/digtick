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

import sys
from .MultiCommand import BaseAction
from .ExpressionParser import parse_expression
from .ExpressionFormatter import format_expression

class ActionParse(BaseAction):
	def run(self):
		if not self._args.read_as_filename:
			expr = parse_expression(self._args.expression)
			print(format_expression(expression = expr, expression_format = self._args.format, implicit_and = not self._args.no_implicit_and))
		else:
			validation_successful = True
			with open(self._args.expression) as f:
				prev_expression = None
				prev_line = None

				for (lineno, line) in enumerate(f, 1):
					line = line.rstrip("\r\n")
					if line.startswith("#") or line == "":
						continue

					expr = parse_expression(line)
					print(format_expression(expression = expr, expression_format = self._args.format, implicit_and = not self._args.no_implicit_and))

					if self._args.validate_equivalence and (prev_expression is not None):
						if not prev_expression.is_equivalent_to(expr):
							print(f"Warning: expression \"{prev_expression}\" on line {prev_line} is not equivalent to expression \"{expr}\" on line {lineno}.", file = sys.stderr)
							validation_successful = False

					(prev_expression, prev_line) = (expr, lineno)
			if not validation_successful:
				print("There were validation errors, some of the equations are not equivalent to each other.", file = sys.stderr)
