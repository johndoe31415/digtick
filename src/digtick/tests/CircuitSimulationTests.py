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
import os
import unittest
import pkgutil
import contextlib
from digtick.sim import Circuit, CmpSource, CmpNOT, CmpSink, CmpAND, CmpOR, CmpXOR, CmpNAND, CmpDFlipFlop, LogisimLoader
from digtick.sim.LogisimInterface import Vec2D
from digtick.ExpressionParser import parse_expression
from digtick.Exceptions import CircuitAstableException, DuplicateLabelException, WrongCircuitPowerStateException, UnknownComponentException, NoSuchCircuitException
from digtick.ValueTable import ValueTable

_run_slow_tests = (os.getenv("UNITTEST_RUN_ALL") == "1")

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

	def test_parse_and_run(self):
		circ = pkgutil.get_data("digtick.tests.data", "awful.circ")
		# Reference table as generated by Logisim Evolution v4.1.0
		reference_output = ValueTable.from_compact_representation(":A,B,C,D,E,F:V,Q,R,S,T,U:55555555555500005555550055550000,55555555000000000000000000000000,54545454545454545454545454545454,55005500000000005500550000000000,1550155555555550155015555555555,1010101010101010101010101010101")

		circuit = LogisimLoader.load_from_xmldata(circ).parse()
		circuit.power_on()
		computed_output = circuit.build_table()
		self.assertEqual(computed_output, reference_output)

	def test_parse_and_run_stateful(self):
		circ = pkgutil.get_data("digtick.tests.data", "stateful.circ")
		circuit = LogisimLoader.load_from_xmldata(circ).parse()
		circuit.power_on()

		computed_output = circuit.build_next_state_table(storage_element_labels = [ "FF1", "FF2", "FF3", "FF4" ], clock_label = "CLK")
		# Reference table manually verified by Logisim Evolution v4.1.0
		reference_output = ValueTable.from_compact_representation(":FF1,FF2,FF3,FF4:FF1',FF2',FF3',FF4':44444444,44441111,55005500,14141414")
		self.assertEqual(computed_output, reference_output)

	def test_powered_only(self):
		circ = Circuit()
		a = circ.new("Source", label = "A")
		with self.assertRaises(WrongCircuitPowerStateException):
			circ.tick()

	def test_unpowered_only(self):
		circ = Circuit()
		a = circ.new("Source", label = "A")
		circ.power_on()
		with self.assertRaises(WrongCircuitPowerStateException):
			circ.new("Source", label = "B")
		with self.assertRaises(WrongCircuitPowerStateException):
			circ.connect(a, "OUT", a, "OUT")

	def test_circuit_dump(self):
		circ = pkgutil.get_data("digtick.tests.data", "stateful.circ")
		circuit = LogisimLoader.load_from_xmldata(circ).parse()
		with contextlib.redirect_stdout(None):
			circuit.dump()

	def test_circuit_print(self):
		circ = pkgutil.get_data("digtick.tests.data", "stateful.circ")
		circuit = LogisimLoader.load_from_xmldata(circ).parse()
		with contextlib.redirect_stdout(None):
			circuit.print()

	def test_circuit_snake(self):
		circ = pkgutil.get_data("digtick.tests.data", "notgatesnake.circ")
		logisim_loader = LogisimLoader.load_from_xmldata(circ)
		logisim_loader.parse()
		with contextlib.redirect_stderr(io.StringIO()):
			logisim_loader.dump_nets()

	def test_circuit_unknown_component(self):
		circ = pkgutil.get_data("digtick.tests.data", "unknown_component.circ")
		with self.assertRaises(UnknownComponentException):
			circuit = LogisimLoader.load_from_xmldata(circ).parse()

	def test_circuit_not_found(self):
		circ = pkgutil.get_data("digtick.tests.data", "other_circuit_name.circ")
		with self.assertRaises(NoSuchCircuitException):
			LogisimLoader.load_from_xmldata(circ)
		LogisimLoader.load_from_xmldata(circ, circuit_name = "schnubbelwurz")

	def test_logisim_vec2d(self):
		v = Vec2D(123, 456)
		self.assertEqual(repr(v), "<123, 456>")
		self.assertEqual(v.x, 123)
		self.assertEqual(v.y, 456)
		v = v + Vec2D(10, -10)
		self.assertEqual(v.x, 133)
		self.assertEqual(v.y, 446)

	def _test_loadfile_conforms_to(self, filename: str, reference_output: ValueTable, circuit_name: str = "main"):
		circ = pkgutil.get_data("digtick.tests.data", filename)
		circuit = LogisimLoader.load_from_xmldata(circ, circuit_name = circuit_name).parse()
		circuit.power_on()
		computed_output = circuit.build_table()
		self.assertEqual(computed_output, reference_output)

	def test_circuit_invgate(self):
		self._test_loadfile_conforms_to("invgate.circ", ValueTable.from_compact_representation(":A,B:Y:10"))

	def test_circuit_invgates(self):
		self._test_loadfile_conforms_to("invgates.circ", ValueTable.from_compact_representation(":A,B,E,F:U1,U2,U3,U4,U5,U6,U7,U8,U9,U10,U11,U12,L1,L2,L3,L4,L5,L6,L7,L8:55000000,5500,550000,55,555555,55550055,55005555,55555500,55,550000,5500,55000000,54545454,51515151,45454545,15151515,14141414,41414141,41414141,14141414"))

	def test_circuit_invgates_multiinput(self):
		vt = ValueTable.parse_string(pkgutil.get_data("digtick.tests.data", "invgates_multiinput.txt").decode("ascii"), set_undefined_values_to = "forbidden")
		self._test_loadfile_conforms_to("invgates_multiinput.circ", vt)

	@unittest.skipUnless(_run_slow_tests, "slow tests disabled (set environment variable UNITTEST_RUN_ALL=1)")
	def test_circuit_5_bit_adder(self):
		vt = ValueTable.parse_string(pkgutil.get_data("digtick.tests.data", "5_bit_adder.txt").decode("ascii"), set_undefined_values_to = "forbidden")
		self._test_loadfile_conforms_to("5_bit_adder.circ", vt, circuit_name = "main_gates")

	def test_circuit_xorgates(self):
		vt = ValueTable.parse_string(pkgutil.get_data("digtick.tests.data", "xorgates.txt").decode("ascii"), set_undefined_values_to = "forbidden")
		self._test_loadfile_conforms_to("xorgates.circ", vt)

	def test_circuit_nandgates(self):
		vt = ValueTable.parse_string(pkgutil.get_data("digtick.tests.data", "nandgates.txt").decode("ascii"), set_undefined_values_to = "forbidden")
		self._test_loadfile_conforms_to("nandgates.circ", vt)
