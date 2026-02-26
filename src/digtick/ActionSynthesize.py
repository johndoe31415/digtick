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
from .ExpressionParser import parse_expression
from .ExpressionFormatter import format_expression
from .QuineMcCluskey import QuineMcCluskey
from .ValueTable import ValueTable
from .Tools import open_file

class ActionSynthesize(BaseAction):
	def run(self):
		with open_file(self._args.filename) as f:
			vt = ValueTable.parse_from_file(f, set_undefined_values_to = self._args.unused_value_is)

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

		dc_expr = parse_expression("+".join(dc_terms), default_empty = "0")
		cdnf = parse_expression("+".join(one_terms), default_empty = "0")
		ccnf = parse_expression("".join(zero_terms), default_empty = "1")

		print(f"CDNF: {format_expression(expression = cdnf, expression_format = self._args.expr_format, implicit_and = not self._args.no_implicit_and)}")
		print(f"CCNF: {format_expression(expression = ccnf, expression_format = self._args.expr_format, implicit_and = not self._args.no_implicit_and)}")

		qmc = QuineMcCluskey(vt, verbosity = self._args.verbose)
		opt_dnf = qmc.optimize(emit_dnf = True)
		opt_cnf = qmc.optimize(emit_dnf = False)
		print(f"DNF : {format_expression(expression = opt_dnf, expression_format = self._args.expr_format, implicit_and = not self._args.no_implicit_and)}")
		print(f"CNF : {format_expression(expression = opt_cnf, expression_format = self._args.expr_format, implicit_and = not self._args.no_implicit_and)}")
