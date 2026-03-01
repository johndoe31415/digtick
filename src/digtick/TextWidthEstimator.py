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

class TextWidthEstimator():
	# Do not judge me. There is no good solution for the issue: I do not want a
	# runtime dependency on freetype-py, the overline hack does not work
	# reliably (Inkscape renders it, but Firefox and Chromium do not) and just
	# hard coding the glyph width looks "off" for many wider characters.
	# Therefore this is a class that is able to estimate a subset of characters
	# widths, calibrated against Latin Modern Roman at 12px.
	_GLYPHS = { "0": 6, "1": 6, "2": 6, "3": 6, "4": 6, "5": 6, "6": 6, "7": 6, "8": 6, "9": 6,
				"A": 9, "B": 9, "C": 9, "D": 9, "E": 8, "F": 8, "G": 9, "H": 9, "I": 4, "J": 6, "K": 9, "L": 8, "M": 11, "N": 9, "O": 9, "P": 8, "Q": 9, "R": 9, "S": 7, "T": 9, "U": 9, "V": 9, "W": 12, "X": 9, "Y": 9, "Z": 7,
				"a": 6, "b": 7, "c": 5, "d": 7, "e": 5, "f": 4, "g": 6, "h": 7, "i": 3, "j": 4, "k": 6, "l": 3, "m": 10, "n": 7, "o": 6, "p": 7, "q": 6, "r": 5, "s": 5, "t": 5, "u": 7, "v": 6, "w": 9, "x": 6, "y": 6, "z": 5,
				"_": 9 }
	_MEDIAN_GLYPH_WIDTH = 7

	@classmethod
	def estimate_text_width(cls, text: str) -> float:
		width = 0
		for character in text:
			width += cls._GLYPHS.get(character, cls._MEDIAN_GLYPH_WIDTH)
		return width

