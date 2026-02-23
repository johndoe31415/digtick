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

import random
import string
from .BaseAction import BaseAction
from .ExpressionParser import parse_expression

class ActionRandom(BaseAction):
	def run(self):
		minterms = list(range(1 << self._args.var_count))
		random.shuffle(minterms)
		minterms = minterms[:self._args.minterm_count]
		minterms.sort()
		minterms_str = [ ]
		for minterm in minterms:
			minterm_str = [ ]
			for i in range(self._args.var_count):
				varname = string.ascii_uppercase[i]
				inverted = (minterm & (1 << i)) != 0
				minterm_str.append(f"{'-' if inverted else ''}{varname}")
			minterms_str.append(" ".join(minterm_str))
		print(" + ".join(minterms_str))
