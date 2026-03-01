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

import random
import string
from .MultiCommand import BaseAction
from .ValueTable import ValueTable, CompactStorage

class ActionRandomTable(BaseAction):
	def run(self):
		if (self._args.zero_percentage + self._args.one_percentage) > 100:
			raise ValueError(f"With {self._args.zero_percentage}% chance to get a zero and {self._args.one_percentage}% chance to get a zero the total proability is greater than 100% ({self._args.zero_percentage + self._args.one_percentage}%).")

		variable_names = [ string.ascii_uppercase[i] for i in range(self._args.var_count) ]
		entry_count = 2 ** self._args.var_count
		zero_entries = round(self._args.zero_percentage / 100 * entry_count)
		one_entries = round(self._args.one_percentage / 100 * entry_count)
		dc_entries = entry_count - zero_entries - one_entries
		if dc_entries < 0:
			raise ValueError("Cannot have {dc_entries} D/C entries. Probabilities do not seem to add up.")

		if len(self._args.output_variable_name) == 0:
			output_var_names = [ "Y" ]
		else:
			output_var_names = self._args.output_variable_name

		output_values = [ ]
		for output_var_name in output_var_names:
			entries = ([ 0 ] * zero_entries) + ([ 1 ] * one_entries) + ([ "*" ] * dc_entries)
			random.shuffle(entries)
			storage = CompactStorage(len(variable_names))
			for (index, entry) in enumerate(entries):
				storage[index] = entry
			output_values.append(storage)
		vt = ValueTable(variable_names, output_var_names, output_values)
		vt.print(ValueTable.PrintFormat(self._args.tbl_format))
