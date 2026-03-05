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
import pysvgedit
from digtick.DigitalTimingDiagram import DigitalTimingDiagram
from digtick.Exceptions import UnknownCharacterException, UnsupportedTransitionException

class DTDTests(unittest.TestCase):
	def test_diagram_creation(self):
		dtd = DigitalTimingDiagram().parse_and_write("""
		A = 0011::!!::00ZZ|'Label'___ZZZ000::111ZZZ:::ZZ
		!A = 111000111000111   000
		# Comment
		""")
		self.assertTrue(isinstance(dtd.svg, pysvgedit.SVGDocument))

	def test_diagram_noticks(self):
		dtd = DigitalTimingDiagram(clock_ticks = False).parse_and_write("""
		A = 10101010
		""")

	def test_diagram_error_unknown_char(self):
		with self.assertRaises(UnknownCharacterException):
			dtd = DigitalTimingDiagram(clock_ticks = False).parse_and_write("""
			A = 10101QQQ010
			""")

	def test_diagram_error_unsupported_transition(self):
		with self.assertRaises(UnsupportedTransitionException):
			dtd = DigitalTimingDiagram(clock_ticks = False).parse_and_write("""
			A = 101011ZZZ!!!
			""")
