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
import math
import hashlib

class PRNG():
	_HASH_FNC = hashlib.md5

	def __init__(self, seed: bytes):
		self._key = self._HASH_FNC(seed).digest()
		self._counter = 0
		self._buffer = bytearray()

	@classmethod
	def randomize(cls):
		return cls(seed = os.urandom(16))

	def _block(self) -> bytes:
		block = self._HASH_FNC(self._key + self._counter.to_bytes(length = 4, byteorder = "little")).digest()
		self._counter += 1
		return block

	def get_bytes(self, length: int) -> bytes:
		while len(self._buffer) < length:
			self._buffer += self._block()
		(result, self._buffer) = (self._buffer[:length], self._buffer[length:])
		return result

	def randint(self, minval: int, maxval: int) -> int:
		irange = maxval - minval + 1
		bits = (irange - 1).bit_length()
		mask = (1 << bits) - 1
		bytecnt = (bits + 7) // 8
		while True:
			value = int.from_bytes(self.get_bytes(bytecnt), byteorder = "little")
			value &= mask
			if value < irange:
				return value + minval

	def randrange(self, length: int):
		return self.randint(0, length - 1)

	def random(self) -> float:
		bits = 80
		while True:
			value = self.randrange(2 ** bits) / (2 ** bits)
			if value < 1:
				# This may happen because we request more bits than the float
				# can carry
				return value

	def gauss(self, mu = 0.0, sigma = 1.0) -> float:
		while True:
			(u1, u2) = (self.random(), self.random())
			if u1 == 0:
				continue
			z = math.sqrt(-2 * math.log(u1)) * math.cos(2 * math.pi * u2)
			return mu + (sigma * z)

	def shuffle(self, data: list):
		for i in range(len(data) - 1):
			j = self.randint(i, len(data) - 1)
			(data[i], data[j]) = (data[j], data[i])

	def sample(self, population: list, k: int) -> list:
		if k > len(population):
			raise ValueError("Sample larger than population or is negative")
		listcopy = [ element for element in population ]
		self.shuffle(listcopy)
		return listcopy[:k]
