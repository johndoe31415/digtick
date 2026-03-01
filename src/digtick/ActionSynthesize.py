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

from .MultiCommand import BaseAction
from .ExpressionFormatter import format_expression
from .QuineMcCluskey import QuineMcCluskey
from .ValueTable import ValueTable
from .Tools import open_file

class ActionSynthesize(BaseAction):
	def run(self):
		with open_file(self._args.filename) as f:
			vt = ValueTable.parse_from_file(f, set_undefined_values_to = self._args.unused_value_is)

		qmc = QuineMcCluskey(vt, self._args.output_variable_name, verbosity = self._args.verbose)
		dc_expr = vt.cdnf_dc(self._args.output_variable_name)

		if self._args.compute in [ "dnf", "both" ]:
			cdnf = vt.cdnf(self._args.output_variable_name)
			print(f"CDNF: {format_expression(expression = cdnf, expression_format = self._args.expr_format, implicit_and = not self._args.no_implicit_and)}")
			opt_expressions = qmc.all_solutions(emit_dnf = True)
			for (expr_no, opt_expression) in enumerate(opt_expressions, 1):
				opt_expr_str = format_expression(expression = opt_expression, expression_format = self._args.expr_format, implicit_and = not self._args.no_implicit_and)
				if not self._args.show_all_solutions:
					print(f"DNF : {opt_expr_str}")
					break
				else:
					print(f"DNF {expr_no}/{opt_expressions.solution_count}: {opt_expr_str}")

		if self._args.compute in [ "cnf", "both" ]:
			if self._args.compute == "both":
				print()
			ccnf = vt.ccnf(self._args.output_variable_name)
			print(f"CCNF: {format_expression(expression = ccnf, expression_format = self._args.expr_format, implicit_and = not self._args.no_implicit_and)}")
			opt_expressions = qmc.all_solutions(emit_dnf = False)
			for (expr_no, opt_expression) in enumerate(opt_expressions, 1):
				opt_expr_str = format_expression(expression = opt_expression, expression_format = self._args.expr_format, implicit_and = not self._args.no_implicit_and)
				if not self._args.show_all_solutions:
					print(f"CNF : {opt_expr_str}")
					break
				else:
					print(f"CNF {expr_no}/{opt_expressions.solution_count}: {opt_expr_str}")
