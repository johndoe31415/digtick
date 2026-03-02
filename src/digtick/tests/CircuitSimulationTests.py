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
from digtick.CircuitSimulation import Circuit, CmpSource, CmpNOT, CmpSink

class CircuitSimulationTests(unittest.TestCase):
	def test_input_output(self):
		circ = Circuit()
		source = circ.add(CmpSource(0))
		sink = circ.add(CmpSink())
		circ.connect(source, "OUT", sink, "IN")
		circ.reset()

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
		circ.reset()

		self.assertEqual(sink.level, 0)
		# Propagation happens only on tick
		circ.tick()
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
		circ.reset()

		self.assertEqual(sink.level, 0)
		# Propagation happens only on tick
		circ.tick()
		self.assertEqual(sink.level, 0)

		source.level = 1
		self.assertEqual(sink.level, 0)
		circ.tick()
		self.assertEqual(sink.level, 1)
