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
from .ExpressionParser import parse_expression
from .ExpressionFormatter import format_expression
from .QuineMcCluskey import QuineMcCluskey
from .ValueTable import ValueTable
from .Tools import open_file

class ActionSynthesize(BaseAction):
	def run(self):
		with open_file(self._args.filename) as f:
			vt = ValueTable.parse_from_file(f, unused_value_str = self._args.unused_value_is)

		zero_terms = [ ]
		one_terms = [ ]
		dc_terms = [ ]
		for (inputs, output) in vt:
			non_inverted_term = " ".join(f"{'!' if (value == 0) else ''}{varname}" for (varname, value) in sorted(inputs.items()))
			inverted_term = "+".join(f"{'!' if (value == 1) else ''}{varname}" for (varname, value) in sorted(inputs.items()))

			if output is None:
				dc_terms.append(non_inverted_term)
			elif output == 0:
				zero_terms.append(f"({inverted_term})")
			else:
				one_terms.append(non_inverted_term)

		dc_expr = parse_expression("+".join(dc_terms))
		cdnf = parse_expression("+".join(one_terms))
		ccnf = parse_expression("".join(zero_terms))

		print(f"CDNF: {format_expression(expression = cdnf, expression_format = self._args.format, implicit_and = not self._args.no_implicit_and)}")
		print(f"CCNF: {format_expression(expression = ccnf, expression_format = self._args.format, implicit_and = not self._args.no_implicit_and)}")

		opt_dnf_str = QuineMcCluskey(cdnf, dc_expr, verbosity = self._args.verbose).optimize()
		opt_dnf = parse_expression(opt_dnf_str)
		print(f"DNF : {format_expression(expression = opt_dnf, expression_format = self._args.format, implicit_and = not self._args.no_implicit_and)}")
