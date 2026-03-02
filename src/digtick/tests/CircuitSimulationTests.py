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
from digtick.CircuitSimulation import Circuit, CmpSource, CmpNOT, CmpSink, CmpAND, CmpOR, CmpXOR, CmpNAND
from digtick.ExpressionParser import parse_expression

class CircuitSimulationTests(unittest.TestCase):
	def test_input_output(self):
		circ = Circuit()
		source = circ.add(CmpSource(0))
		sink = circ.add(CmpSink())
		circ.connect(source, "OUT", sink, "IN")
		circ.power_on()

		circ.tick()
		self.assertEqual(sink.level, 0)

		source.level = 1
		self.assertEqual(sink.level, 0)
		circ.tick()
		self.assertEqual(sink.level, 1)

	def test_inverter(self):
		# Single inverter circuit
		circ = Circuit()
		source = circ.add(CmpSource(0))
		inverter1 = circ.add(CmpNOT())
		sink = circ.add(CmpSink())
		circ.connect(source, "OUT", inverter1, "A")
		circ.connect(inverter1, "Y", sink, "IN")
		circ.power_on()

		self.assertEqual(sink.level, 1)

		source.level = 1
		self.assertEqual(sink.level, 1)
		circ.tick()
		self.assertEqual(sink.level, 0)

	def test_inverter_2(self):
		# 2 inverters in a row
		circ = Circuit()
		source = circ.add(CmpSource(0))
		inverter1 = circ.add(CmpNOT())
		inverter2 = circ.add(CmpNOT())
		sink = circ.add(CmpSink())
		circ.connect(source, "OUT", inverter1, "A")
		circ.connect(inverter1, "Y", inverter2, "A")
		circ.connect(inverter2, "Y", sink, "IN")
		circ.power_on()

		self.assertEqual(sink.level, 0)
		# Propagation happens only on tick
		circ.tick()
		self.assertEqual(sink.level, 0)

		source.level = 1
		self.assertEqual(sink.level, 0)
		circ.tick()
		self.assertEqual(sink.level, 1)

	def test_combinatorial_circuit(self):
		expression = parse_expression("!((A^B) @ C) | D A")
		circ = Circuit()
		(A, B, C, D) = (circ.add(CmpSource(0)), circ.add(CmpSource(0)), circ.add(CmpSource(0)), circ.add(CmpSource(0)))
		g_not = circ.add(CmpNOT())
		g_and = circ.add(CmpAND())
		g_or = circ.add(CmpOR())
		g_xor = circ.add(CmpXOR())
		g_nand = circ.add(CmpNAND())
		Y = circ.add(CmpSink())

		circ.connect(A, "OUT", g_xor, "A")
		circ.connect(B, "OUT", g_xor, "B")
		circ.connect(g_xor, "Y", g_nand, "A")
		circ.connect(C, "OUT", g_nand, "B")
		circ.connect(g_nand, "Y", g_not, "A")
		circ.connect(g_not, "Y", g_or, "A")
		circ.connect(D, "OUT", g_and, "A")
		circ.connect(A, "OUT", g_and, "B")
		circ.connect(g_and, "Y", g_or, "B")
		circ.connect(g_or, "Y", Y, "IN")
		circ.power_on()
		for (input_values, output) in expression.table():
			A.level = input_values["A"]
			B.level = input_values["B"]
			C.level = input_values["C"]
			D.level = input_values["D"]
			circ.tick()
			self.assertEqual(Y.level, output)
