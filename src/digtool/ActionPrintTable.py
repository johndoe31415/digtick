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

from .MultiCommand import BaseAction
from .ValueTable import ValueTable

class ActionPrintTable(BaseAction):
	def run(self):
		with open(self._args.filename) as f:
			vt = ValueTable.parse_from_file(f, unused_value_str = self._args.unused_value_is)
		if self._args.format == "pretty":
			vt.print()
		elif self._args.format == "text":
			vt.print_native()
		else:
			raise NotImplementedError(self._args.format)
