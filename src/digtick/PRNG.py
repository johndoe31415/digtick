#	digtick - Digital systems toolkit: simplify, minimize and transform Boolean expressions, draw KV-maps, etc.
#	Copyright (C) 2022-2022 Johannes Bauer
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

import hashlib

class PRNG():
	_HASH_FNC = hashlib.md5

	def __init__(self, seed: bytes):
		self._key = self._HASH_FNC(seed).digest()
		self._counter = 0
		self._buffer = bytearray()

	def _block(self):
		block = self._HASH_FNC(self._key + self._counter.to_bytes(length = 4, byteorder = "little")).digest()
		self._counter += 1
		return block

	def get_bytes(self, length):
		while len(self._buffer) < length:
			self._buffer += self._block()
		(result, self._buffer) = (self._buffer[:length], self._buffer[length:])
		return result

	def randint(self, minval, maxval):
		irange = maxval - minval + 1
		bits = (irange - 1).bit_length()
		mask = (1 << bits) - 1
		bytecnt = (bits + 7) // 8
		while True:
			value = int.from_bytes(self.get_bytes(bytecnt), byteorder = "little")
			value &= mask
			if value < irange:
				return value + minval

if __name__ == "__main__":
	prng = PRNG(b"foo")
	for i in range(100000):
		print(prng.randint(9, 10))
