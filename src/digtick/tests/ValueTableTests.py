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

import io
import contextlib
import unittest
import textwrap
from digtick.ExpressionParser import parse_expression
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

	def test_str_display(self):
		vt = ValueTable.parse_string(self._prepstr("""
			A B >Y
			0 0 1
			0 1 0
			1 0 *
			1 1 1
		"""), set_undefined_values_to = "0")
		self.assertEqual(list(vt), [ (CompactStorage.Entry.High, ), (CompactStorage.Entry.Low, ), (CompactStorage.Entry.DontCare, ), (CompactStorage.Entry.High, ) ])
		self.assertEqual([ entries[0].as_str for entries in vt ], [ "1", "0", "*", "1" ])

	def test_undefined_values(self):
		vt = ValueTable.parse_string(self._prepstr("""
			A B >Y
			1 0 1
		"""), set_undefined_values_to = "*")
		self.assertEqual([ entries[0].as_str for entries in vt ], [ "*", "*", "1", "*" ])

	def test_set_values(self):
		vt = ValueTable.parse_string(self._prepstr("""
			A B >Y
		"""), set_undefined_values_to = "0")
		self.assertEqual([ entries[0].as_str for entries in vt ], [ "0", "0", "0", "0" ])
		cs = vt.get_storage("Y")
		cs[1] = "1"
		cs[2] = "*"
		cs[3] = "*"
		cs[0] = 1
		self.assertEqual([ entries[0].as_str for entries in vt ], [ "1", "1", "*", "*" ])
		cs[1] = "0"
		cs[2] = "*"
		cs[3] = "*"
		self.assertEqual([ entries[0].as_str for entries in vt ], [ "1", "0", "*", "*" ])
		cs[0] = 0
		self.assertEqual([ entries[0].as_str for entries in vt ], [ "0", "0", "*", "*" ])

	def test_add_set(self):
		vt = ValueTable.parse_string(self._prepstr("""
			A B >Y
		"""), set_undefined_values_to = "0")
		self.assertTrue(vt.has_output_named("Y"))
		self.assertFalse(vt.has_output_named("Z"))

		cs = CompactStorage(2, initial_value = 0)
		vt.add_output_variable("Z", cs)
		self.assertTrue(vt.has_output_named("Y"))
		self.assertTrue(vt.has_output_named("Z"))

	def test_overwrite_warning(self):
		iobuf = io.StringIO()
		with contextlib.redirect_stdout(iobuf):
			vt = ValueTable.parse_string(self._prepstr("""
				A B >Y
				0 0 1
				0 1 0
				0 1 0
				1 0 *
				1 1 1
			"""), set_undefined_values_to = "0")
		self.assertIn("value overwritten in line", iobuf.getvalue())

	def test_dnf_zero(self):
		vt = ValueTable.parse_string(self._prepstr("""
			A B >Y
			0 0 0
			0 1 0
			1 0 0
			1 1 0
		"""), set_undefined_values_to = "0")
		self.assertEqual(vt.cdnf("Y").value, 0)

	def test_cnf_one(self):
		vt = ValueTable.parse_string(self._prepstr("""
			A B >Y
			0 0 1
			0 1 1
			1 0 1
			1 1 1
		"""), set_undefined_values_to = "0")
		self.assertEqual(vt.ccnf("Y").value, 1)

	def test_undefined_output(self):
		vt = ValueTable.parse_string(self._prepstr("""
			A B >Y
			1 0 1
		"""), set_undefined_values_to = "*")
		with self.assertRaises(KeyError):
			list(vt.iter_output_variable("F"))

	def test_empty_file(self):
		f = io.StringIO()
		with self.assertRaises(InvalidValueTableException):
			vt = ValueTable.parse_from_file(f, set_undefined_values_to = "0")

	def test_broken_file(self):
		f = io.StringIO()
		f.write(self._prepstr("""
		A >Y
		0 1
		1
		"""))
		f.seek(0)
		with self.assertRaises(InvalidValueTableException):
			vt = ValueTable.parse_from_file(f, set_undefined_values_to = "0")

	def test_multi_output_parse_and_compact_roundtrip(self):
		text = self._prepstr("""
			A B >Y >Z
			0 0 0 1
			0 1 1 0
			1 0 1 1
			1 1 0 0
		""")
		vt = ValueTable.parse_string(text, set_undefined_values_to = "0")
		reparsed = ValueTable.from_compact_representation(vt.compact_representation)
		self.assertEqual(vt, reparsed)

	def test_output_order_is_preserved(self):
		text = self._prepstr("""
			A >Z >Y
			0 1 0
			1 0 1
		""")
		vt = ValueTable.parse_string(text, set_undefined_values_to = "0")
		self.assertEqual(vt.output_variable_count, 2)
		self.assertTrue(vt.has_output_named("Y"))
		self.assertTrue(vt.has_output_named("Z"))
		self.assertEqual(vt.compact_representation, ":A:Z,Y:1,4")

	def test_add_output_variable_rejects_duplicate_name(self):
		vt = ValueTable.parse_string("A >Y\n0 0\n1 1\n", set_undefined_values_to = "0")
		with self.assertRaises(InvalidValueTableException):
			vt.add_output_variable("Y", vt.get_storage("Y"))

	def test_add_output_different_var_count(self):
		vt = ValueTable.parse_string("A >Y\n0 0\n1 1\n", set_undefined_values_to = "0")
		cr = CompactStorage(2, initial_value = CompactStorage.Entry.High)
		with self.assertRaises(InvalidValueTableException):
			vt.add_output_variable("Z", cr)

	def test_dnf(self):
		vt = ValueTable.from_compact_representation(":A,B,C,D:Y:100000")
		self.assertEqual(vt.cdnf("Y"), parse_expression("A !B C !D"))

		vt = ValueTable.from_compact_representation(":A,B,C,D:Y:40044000")
		self.assertEqual(vt.cdnf("Y"), parse_expression("A !B !C D + A B C D + !A B C D"))

	def test_cnf(self):
		vt = ValueTable.from_compact_representation(":A,B,C,D:Y:55554555")
		self.assertEqual(vt.cdnf("Y"), parse_expression("A + !B + !C + D"))

		vt = ValueTable.from_compact_representation(":A,B,C,D:Y:55544554")
		self.assertEqual(vt.cdnf("Y"), parse_expression("(A + !B + !C + D)(A + B + C + D)(!A + B + C + D)"))

	def test_default_dump(self):
		vt = ValueTable.from_compact_representation(":A,B,C,D:Y:55554555")
		f = io.StringIO()
		with contextlib.redirect_stdout(f):
			vt.print()
		self.assertIn("A	B	C	D	>Y", f.getvalue())

	def test_compactstorage_entries(self):
		self.assertEqual(CompactStorage.Entry.from_str("*"), CompactStorage.Entry.DontCare)
		self.assertEqual(CompactStorage.Entry.from_str("-"), CompactStorage.Entry.DontCare)
		vt1 = ValueTable.from_compact_representation(":A,B,C,D:Y:55554555")
		vt2 = ValueTable.from_compact_representation(":A,B,C,D:Z:55554555")
		vt3 = ValueTable.from_compact_representation(":A,B,C,D,E:Q:55554555")
		vt4 = ValueTable.from_compact_representation(":A,B,C,D:N:45554555")
		self.assertEqual(vt1.get_storage("Y"), vt2.get_storage("Z"))
		self.assertNotEqual(vt1.get_storage("Y"), vt3.get_storage("Q"))
		self.assertNotEqual(vt1.get_storage("Y"), vt4.get_storage("N"))

		self.assertEqual(CompactStorage.Entry.from_str("WAIT WHAT", permissive = True), None)
		with self.assertRaises(ValueError):
			CompactStorage.Entry.from_str("WAIT WHAT")
