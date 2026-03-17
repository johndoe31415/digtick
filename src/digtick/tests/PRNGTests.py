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

import os
import unittest
import collections
from digtick.PRNG import PRNG

class PRNGTests(unittest.TestCase):
	def test_bytes(self):
		prng1 = PRNG(b"foobar")
		prng2 = PRNG(b"barfoo")
		prng3 = PRNG(b"foobar")
		x = prng1.get_bytes(100)
		y = prng2.get_bytes(100)
		z = prng3.get_bytes(100)
		self.assertEqual(x, z)
		self.assertNotEqual(x, y)
		self.assertEqual(len(x), 100)
		self.assertEqual(len(y), 100)

	def test_min_max(self):
		prng = PRNG(os.urandom(16))
		values = set(prng.randint(0, 1) for _ in range(100))
		self.assertEqual(values, set([ 0, 1 ]))

	def test_bias(self):
		# Ensure reasonable bias-freeness
		prng = PRNG(os.urandom(16))
		values = collections.Counter(prng.randint(0, 2) for _ in range(1000))
		diff = values.most_common()[0][1] - values.most_common()[2][1]
		self.assertTrue(diff < 150)

	def test_shuffle_basic(self):
		l = list("ABCD")
		prng = PRNG(os.urandom(16))
		prng.shuffle(l)
		self.assertEqual(len(l), 4)
		self.assertEqual(set(l), set("ABCD"))

	def test_shuffle_combinations(self):
		prng = PRNG(os.urandom(16))
		l = list(range(20))
		seen = set()
		for _ in range(10000):
			prng.shuffle(l)
			seen |= set((i, e) for (i, e) in enumerate(l))
			if len(seen) == (len(l) ** 2):
				break
		else:
			raise AssertionError("Not all combinations seen.")
