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
from .ExpressionFormatter import format_expression
from .ValueTable import ValueTable
from .QuineMcCluskey import QuineMcCluskey
from .RandomDist import RandomDist

class ActionRandomTable(BaseAction):
	def run(self):
		variable_names = [ string.ascii_uppercase[i] for i in range(self._args.var_count) ]
		entry_count = 2 ** self._args.var_count
		zero_entries = round(self._args.zero_percentage / 100 * entry_count)
		one_entries = round(self._args.one_percentage / 100 * entry_count)
		dc_entries = entry_count - zero_entries - one_entries
		if dc_entries < 0:
			raise ValueError("Cannot have {dc_entries} D/C entries. Probabilities do not seem to add up.")

		entries = ([ 0 ] * zero_entries) + ([ 1 ] * one_entries) + ([ None ] * dc_entries)
		random.shuffle(entries)

		vt = ValueTable(variable_names, entries)
		vt.print_native()
