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

import enum
import xml.etree.ElementTree

class FaceDirection(enum.Enum):
	North = "north"
	South = "south"
	West = "west"
	East = "east"

class LogisimLoader():
	def __init__(self, filename: str, circuit_name: str = "main"):
		self._filename = filename
		self._circuit_name = circuit_name
		self._doc = xml.etree.ElementTree.parse(filename)
		self._root = self._doc.getroot()
		self._xml_circuit = self._root.find(f"./circuit[@name='{self._circuit_name}']")
		self._libraries = { }
		self._circuit = None

	@property
	def circuit(self):
		return self.circuit

	@staticmethod
	def _parse_pos(xy_tuple: str):
		assert(xy_tuple.startswith("("))
		assert(xy_tuple.endswith(")"))
		(x, y) = xy_tuple[1 : -1].split(",")
		return (int(x), int(y))

	def _parse_libraries(self):
		for node in self._root.findall("./lib"):
			self._libraries[node.get("name")] = node.get("desc")

	def _iter_components(self):
		for node in self._xml_circuit.findall("./comp"):
			lib = node.get("lib")
			name = node.get("name")
			full_name = f"{self._libraries[lib]}.{name}"
			loc = self._parse_pos(node.get("loc"))

			component = {
				"name": full_name,
				"loc": loc,
			}
			for attribute in node.findall("./a"):
				(key, value) = (attribute.get("name"), attribute.get("val"))
				if key in [ "inputs", "size" ]:
					value = int(value)
				elif key in [ "facing" ]:
					value = FaceDirection(value)
				component[f".{key}"] = value
			yield component

	def _iter_wires(self):
		for node in self._xml_circuit.findall("./wire"):
			yield (self._parse_pos(node.get("from")), self._parse_pos(node.get("to")))

	def parse(self):
		self._parse_libraries()
		for component in self._iter_components():
			print(component)
		for (src, dst) in self._iter_wires():
			print(src, dst)
		return self._circuit



if __name__ == "__main__":
	circuit = LogisimLoader("/tmp/awful.circ").parse()
	print(circuit)
