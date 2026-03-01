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
from digtick.ExpressionParser import parse_expression
from digtick.ValueTable import ValueTable, CompactStorage
from digtick.QuineMcCluskey import QuineMcCluskey

class QMCTests(unittest.TestCase):
	_VALUE_TABLES = [
		ValueTable.from_compact_representation(":A,B,C,D:Y:61590100"),		# Wikipedia example
		ValueTable.from_compact_representation(":A,B,C,D,E,F:Y:1064158620815865a044911508155600"),
	]

	def _assert_satisfies(self, vt: ValueTable, expr: "ParseTreeElement"):
		for (index, (input_dict, output_dict)) in enumerate(vt.iter_inputdict):
			expected_value = output_dict["Y"]
			eval_value = expr.evaluate(input_dict)
			satisfied = (expected_value == CompactStorage.Entry.DontCare) or (expected_value == eval_value)
			self.assertTrue(satisfied)

	def test_qmc_dnf(self):
		for vt in self._VALUE_TABLES:
			qmc = QuineMcCluskey(vt, "Y")
			expr = qmc.optimize()
			self._assert_satisfies(vt, expr)

	def test_qmc_cnf(self):
		for vt in self._VALUE_TABLES:
			qmc = QuineMcCluskey(vt, "Y")
			expr = qmc.optimize(emit_dnf = False)
			self._assert_satisfies(vt, expr)

	def test_qmc_pruning(self):
		# When greedy pruning during the Petrick's Method step of QMC is used,
		# QMC will find a sub-optimal 5-minterm solution when there exists a
		# 4-minterm solution.
		vt = ValueTable.from_compact_representation(":A,B,C,D:Y:155144")
		optimal = parse_expression("!A B !D + A !B !D + !B !C D + !A C D")
		self._assert_satisfies(vt, optimal)

		generated = QuineMcCluskey(vt, "Y").optimize()
		self._assert_satisfies(vt, generated)
		minterms = list(generated.collect_minterms())
		self.assertEqual(len(minterms), 4)

	def test_qmc_absorb(self):
		# Implicands are represented by bitsets, ORing them together means the
		# logical AND of those implicants.
		(I1, I2, I3) = (1, 2, 4)
		self.assertEqual(QuineMcCluskey._absorb(set([ I1, I1 | I2 ])), set([ I1 ]))
		self.assertEqual(QuineMcCluskey._absorb(set([ I1 | I2, I1 | I3 ])), set([ I1 | I2, I1 | I3 ]))
		self.assertEqual(QuineMcCluskey._absorb(set([ I1 | I2, I1 | I3, I1 ])), set([ I1 ]))
		self.assertEqual(QuineMcCluskey._absorb(set([ I1 | I2, I1 | I3, I3 ])), set([ I1 | I2, I3 ]))
