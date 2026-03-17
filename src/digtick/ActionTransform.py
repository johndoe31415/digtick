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
from .ExpressionParser import parse_expression
from .ExpressionTransformer import ExpressionTransformer
from .PRNG import PRNG

class ActionTransform(BaseAction):
	def run(self):
		expr = parse_expression(self._args.expression)
		for transformation_name in self._args.transform:
			transformer_kwargs = { }
			if transformation_name == "shuffle":
				transformer_kwargs["prng"] = PRNG(b"foo")
			transformed = ExpressionTransformer.new(transformation_name, **transformer_kwargs).transform(expr)
			print(format_expression(expression = transformed, expression_format = self._args.expr_format, implicit_and = not self._args.no_implicit_and))
			assert(expr == transformed)
			expr = transformed
