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
from digtick.sim import Circuit, Component, CmpSource, CmpNOT, CmpSink, CmpAND, CmpOR, CmpXOR, CmpNAND, CmpDFlipFlop
from digtick.ExpressionParser import parse_expression
from digtick.Exceptions import CircuitAstableException, DuplicateLabelException

class CircuitSimulationTests(unittest.TestCase):
	def test_input_output(self):
		circ = Circuit()
		source = circ.add(CmpSource(level = 0))
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
		source = circ.add(CmpSource(level = 0))
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
		source = circ.add(CmpSource(level = 0))
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
		(A, B, C, D) = (circ.add(CmpSource(level = 0)), circ.add(CmpSource(level = 0)), circ.add(CmpSource(level = 0)), circ.add(CmpSource(level = 0)))
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

	def test_nand_net_both_pins(self):
		circ = Circuit()
		source = circ.add(CmpSource(level = 0))
		gate = circ.add(CmpNAND())
		sink = circ.add(CmpSink())
		circ.connect(source, "OUT", gate, "A", gate, "B")
		circ.connect(gate, "Y", sink, "IN")
		circ.power_on()

		circ.tick()
		self.assertEqual(sink.level, 1)

		source.level = 1
		self.assertEqual(sink.level, 1)
		circ.tick()
		self.assertEqual(sink.level, 0)

	def test_nand_net_merge(self):
		circ = Circuit()
		source = circ.add(CmpSource(level = 0))
		unused_sink = circ.add(CmpSink())
		gate = circ.add(CmpNAND())
		sink = circ.add(CmpSink())

		circ.connect(source, "OUT", gate, "A")
		circ.connect(unused_sink, "IN", gate, "B")
		circ.connect(gate, "A", gate, "B")
		circ.connect(gate, "Y", sink, "IN")
		circ.power_on()

		circ.tick()
		self.assertEqual(sink.level, 1)

		source.level = 1
		self.assertEqual(sink.level, 1)
		circ.tick()
		self.assertEqual(sink.level, 0)

	def test_astable_circuit(self):
		circ = Circuit()
		gate = circ.add(CmpNOT())
		circ.connect(gate, "A", gate, "Y")
		with self.assertRaises(CircuitAstableException):
			circ.power_on()

	def test_d_flipflop(self):
		circ = Circuit()

		d = circ.add(CmpSource(level = 0))
		clk = circ.add(CmpSource(level = 0))
		ff = circ.add(CmpDFlipFlop())
		q = circ.add(CmpSink())
		notq = circ.add(CmpSink())

		circ.connect(d, "OUT", ff, "D")
		circ.connect(clk, "OUT", ff, "CLK")
		circ.connect(ff, "Q", q, "IN")
		circ.connect(ff, "!Q", notq, "IN")
		circ.power_on()

		self.assertEqual(d.level, 0)
		self.assertEqual(clk.level, 0)
		self.assertEqual(q.level, 0)
		self.assertEqual(notq.level, 1)

		for i in range(10):
			d.toggle()
			circ.tick()
			self.assertEqual(clk.level, 0)
			self.assertEqual(q.level, 0)
			self.assertEqual(notq.level, 1)

		d.level = 1
		circ.tick()
		self.assertEqual(q.level, 0)
		self.assertEqual(notq.level, 1)

		clk.level = 1
		self.assertEqual(q.level, 0)
		self.assertEqual(notq.level, 1)
		circ.tick()
		self.assertEqual(q.level, 1)
		self.assertEqual(notq.level, 0)

	def test_d_flipflop_cyclic(self):
		circ = Circuit()
		d = circ.add(CmpSource(level = 0))
		clk = circ.add(CmpSource(level = 0))
		ff = circ.add(CmpDFlipFlop())
		q = circ.add(CmpSink())
		notq = circ.add(CmpSink())
		circ.connect(ff, "!Q", ff, "D")
		circ.connect(clk, "OUT", ff, "CLK")
		circ.connect(ff, "Q", q, "IN")
		circ.connect(ff, "!Q", notq, "IN")
		circ.power_on()

		self.assertEqual(d.level, 0)
		self.assertEqual(clk.level, 0)
		self.assertEqual(q.level, 0)
		self.assertEqual(notq.level, 1)

		clk.level = 1
		circ.tick()
		self.assertEqual(q.level, 1)
		self.assertEqual(notq.level, 0)

		clk.level = 0
		circ.tick()
		self.assertEqual(q.level, 1)
		self.assertEqual(notq.level, 0)

		clk.level = 1
		circ.tick()
		self.assertEqual(q.level, 0)
		self.assertEqual(notq.level, 1)

	def test_rs_nand_flipflop(self):
		circ = Circuit()
		s = circ.add(CmpSource(level = 1))
		r = circ.add(CmpSource(level = 1))
		nand1 = circ.add(CmpNAND())
		nand2 = circ.add(CmpNAND())
		q = circ.add(CmpSink())
		notq = circ.add(CmpSink())

		circ.connect(s, "OUT", nand1, "A")
		circ.connect(r, "OUT", nand2, "A")
		circ.connect(nand1, "Y", nand2, "B")
		circ.connect(nand2, "Y", nand1, "B")
		circ.connect(nand1, "Y", q, "IN")
		circ.connect(nand2, "Y", notq, "IN")
		circ.power_on()

		# We cannot be sure which level we wake up in because we initialized in
		# "keep"
		self.assertEqual(q.level, 1 ^ notq.level)

		# Set
		s.level = 0
		circ.tick()
		self.assertEqual(q.level, 1)
		self.assertEqual(notq.level, 0)

		# Keep
		s.level = 1
		circ.tick()
		self.assertEqual(q.level, 1)
		self.assertEqual(notq.level, 0)

		# Reset
		r.level = 0
		circ.tick()
		self.assertEqual(q.level, 0)
		self.assertEqual(notq.level, 1)

		# Keep
		r.level = 0
		circ.tick()
		self.assertEqual(q.level, 0)
		self.assertEqual(notq.level, 1)

		# "Illegal" state, Set & Reset
		s.level = 0
		r.level = 0
		circ.tick()
		self.assertEqual(q.level, 1)
		self.assertEqual(notq.level, 1)

		# Transition after which we do NOT know what state we're in (this is
		# *truly* illegal)
		s.level = 1
		r.level = 1
		circ.tick()
		self.assertEqual(q.level, 1 ^ notq.level)

	def test_named_instances(self):
		circ = Circuit()
		a = circ.new("Source", label = "A")
		b = circ.new("Source", label = "B")
		gate = circ.new("NAND")
		y = circ.new("Sink", label = "Y")
		circ.connect(a, "OUT", gate, "A")
		circ.connect(b, "OUT", gate, "B")
		circ.connect(gate, "Y", y, "IN")
		circ.power_on()

		table = circ.build_table()
		self.assertEqual(table.compact_representation, ":A,B:Y:15")

	def test_label(self):
		circ = Circuit()
		a = circ.new("Source", label = "blah")
		with self.assertRaises(DuplicateLabelException):
			b = circ.new("Source", label = "blah")
		b = circ.new("Source", label = "blubb")
		self.assertTrue(circ["blah"] is a)
		self.assertTrue(circ["blubb"] is b)
