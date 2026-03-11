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

import unittest
from digtick.Tools import sort_signal_key

class ToolsTests(unittest.TestCase):
	@staticmethod
	def _sort_signal_key_rev(invalue):
		return sort_signal_key(invalue, suffix_order_reversed = True)

	def test_sort(self):
		sigs = [ "A2", "A3", "A1", "A0", "A10", "A20", "A4", "A11" ]
		sigs.sort(key = sort_signal_key)
		self.assertEqual(sigs, [ "A20", "A11", "A10", "A4", "A3", "A2", "A1", "A0" ])

		sigs.sort(key = self._sort_signal_key_rev)
		self.assertEqual(sigs, [ "A0", "A1", "A2", "A3", "A4", "A10", "A11", "A20" ])

	def test_sort_mixed_prefixes_and_plain_names(self):
		sigs = [ "B2", "A10", "A2", "A", "B1", "A1" ]
		sigs.sort(key = sort_signal_key)
		self.assertEqual(sigs, [ "A10", "A2", "A1", "A", "B2", "B1" ])

		sigs.sort(key = self._sort_signal_key_rev)
		self.assertEqual(sigs, [ "A", "A1", "A2", "A10", "B1", "B2" ])

	def test_sort_leading_zeroes_shorter_wins(self):
		sigs = [ "A02", "A2", "A001", "A1" ]
		sigs.sort(key = sort_signal_key)
		self.assertEqual(sigs, [ "A2", "A02", "A1", "A001" ])

		sigs.sort(key = self._sort_signal_key_rev)
		self.assertEqual(sigs, [ "A1", "A001", "A2", "A02" ])
