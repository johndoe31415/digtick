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
import textwrap
from digtick.ValueTable import ValueTable, CompactStorage
from digtick.Exceptions import InvalidValueTableException

class ValueTableTests(unittest.TestCase):
	def test_reprs(self):
		cr = CompactStorage(3, initial_value = CompactStorage.Entry.High)
		self.assertTrue(repr(cr).startswith("Comp"))

		vt = ValueTable.from_compact_representation(":A,B,C:Y:1612")
		self.assertEqual(vt.output_variable_count, 1)

	def test_parse_errors_compact(self):
		with self.assertRaises(InvalidValueTableException):
			vt = ValueTable.from_compact_representation(":A,B,C:Y:1612,1234")
		with self.assertRaises(InvalidValueTableException):
			vt = ValueTable.from_compact_representation("::Y:1612")
		with self.assertRaises(InvalidValueTableException):
			vt = ValueTable.from_compact_representation(":A,B,C::1612")
		with self.assertRaises(InvalidValueTableException):
			vt = ValueTable.from_compact_representation(":A,B,A:Y:1612")

	def _prepstr(self, text: str) -> str:
		return textwrap.dedent(text.strip("\r\n"))

	def test_parse_errors_std(self):
		vt = ValueTable.parse_string(self._prepstr("""
			A >Y
			0 0
			1 1
		"""), set_undefined_values_to = "0")
		self.assertEqual(vt.compact_representation, ":A:Y:4")
		with self.assertRaises(InvalidValueTableException):
			vt = ValueTable.parse_string(self._prepstr("""
				A Y
				0 0
				1 1
			"""), set_undefined_values_to = "0")
		with self.assertRaises(InvalidValueTableException):
			vt = ValueTable.parse_string(self._prepstr("""
				>A >B
				0 0
				1 1
			"""), set_undefined_values_to = "0")
		with self.assertRaises(InvalidValueTableException):
			vt = ValueTable.parse_string(self._prepstr("""
				A >A
				0 0
				1 1
			"""), set_undefined_values_to = "0")
