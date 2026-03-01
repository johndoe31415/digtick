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
from digtick.ExpressionParser import Variable, parse_expression
from digtick.ValueTable import ValueTable

class ExpressionTreeTests(unittest.TestCase):
	def test_or_operator(self):
		vt = ValueTable.create_from_expression("Y", Variable("A") | Variable("B"))
		self.assertEqual(vt.compact_representation, ":A,B:Y:54")

	def test_and_operator(self):
		vt = ValueTable.create_from_expression("Y", Variable("A") & Variable("B"))
		self.assertEqual(vt.compact_representation, ":A,B:Y:40")

	def test_nor_operator(self):
		vt = ValueTable.create_from_expression("Y", Variable("A") % Variable("B"))
		self.assertEqual(vt.compact_representation, ":A,B:Y:1")

	def test_nand_operator(self):
		vt = ValueTable.create_from_expression("Y", Variable("A") @ Variable("B"))
		self.assertEqual(vt.compact_representation, ":A,B:Y:15")

	def test_not_operator(self):
		vt = ValueTable.create_from_expression("Y", ~Variable("A"))
		self.assertEqual(vt.compact_representation, ":A:Y:1")

	def test_const_operator(self):
		vt = ValueTable.create_from_expression("Y", Variable("A") & 0)
		self.assertEqual(vt.compact_representation, ":A:Y:0")

		vt = ValueTable.create_from_expression("Y", Variable("A") & 1)
		self.assertEqual(vt.compact_representation, ":A:Y:4")

		vt = ValueTable.create_from_expression("Y", Variable("A") | 0)
		self.assertEqual(vt.compact_representation, ":A:Y:4")

		vt = ValueTable.create_from_expression("Y", Variable("A") | 1)
		self.assertEqual(vt.compact_representation, ":A:Y:5")

	def test_rand_operator(self):
		vt = ValueTable.create_from_expression("Y", 1 & Variable("A"))
		self.assertEqual(vt.compact_representation, ":A:Y:4")

	def test_ror_operator(self):
		vt = ValueTable.create_from_expression("Y", 1 | Variable("A"))
		self.assertEqual(vt.compact_representation, ":A:Y:5")

	def test_rxor_operator(self):
		vt = ValueTable.create_from_expression("Y", 1 ^ Variable("A"))
		self.assertEqual(vt.compact_representation, ":A:Y:1")

	def test_rnand_operator(self):
		self.assertTrue(("A" @ Variable("B")).identical_to(parse_expression("A @ B")))
