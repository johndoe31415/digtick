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
import dataclasses
import xml.etree.ElementTree

class FaceDirection(enum.Enum):
	North = "north"
	South = "south"
	West = "west"
	East = "east"

@dataclasses.dataclass(frozen = True, slots = True, order = True)
class Vec2D():
	x: int
	y: int

	@classmethod
	def parse(cls, xy_tuple: str):
		assert(xy_tuple.startswith("("))
		assert(xy_tuple.endswith(")"))
		(x, y) = xy_tuple[1 : -1].split(",")
		return cls(x = int(x), y = int(y))

	def __add__(self, other: "Vec2D"):
		return Vec2D(self.x + other.x, self.y + other.y)

	def __neg__(self):
		return Vec2D(-self.x, -self.y)

	def rotate_offset(self, fd: FaceDirection):
		match fd:
			case FaceDirection.East:
				# No rotation needed, this is the original configuration
				return self

			case FaceDirection.West:
				return -self

			case FaceDirection.North:
				return -Vec2D(self.y, self.x)

			case FaceDirection.South:
				return Vec2D(self.y, self.x)

			case _:
				raise NotImplementedError(fd)

	def __repr__(self):
		return f"<{self.x}, {self.y}>"

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

	def _parse_libraries(self):
		for node in self._root.findall("./lib"):
			self._libraries[node.get("name")] = node.get("desc")

	def _iter_components(self):
		for node in self._xml_circuit.findall("./comp"):
			lib = node.get("lib")
			name = node.get("name")
			full_name = f"{self._libraries[lib]}.{name}"
			loc = Vec2D.parse(node.get("loc"))

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
			yield (Vec2D.parse(node.get("from")), Vec2D.parse(node.get("to")))

	def _resolve_component(self, component: dict):
		print(component)
		translated_component = {
			"type": None,
			"pins": { },
		}
		match (component["name"], component.get(".type")):
			case ("#Wiring.Pin", None):
				translated_component["type"] = "Sink"
				translated_component["pins"]["IN"] = component["loc"]

			case ("#Wiring.Pin", "output"):
				translated_component["type"] = "Source"
				translated_component["pins"]["OUT"] = component["loc"]

			case ("#Gates.NOT Gate", None):
				assert(component.get(".inputs", 2) == 2)
				translated_component["type"] = "NOT"
				translated_component["pins"]["Y"] = component["loc"]
				translated_component["pins"]["A"] = component["loc"] + Vec2D(-component.get(".size", 30), 0).rotate_offset(component.get(".facing", FaceDirection.East))

			case ("#Gates.AND Gate", None):
				assert(component.get(".inputs", 2) == 2)
				translated_component["type"] = "AND"
				translated_component["pins"]["Y"] = component["loc"]
				size = component.get(".size", 50)
				(aoffset, boffset) = {
					30: (Vec2D(-size, -10), Vec2D(-size, 10)),
					50: (Vec2D(-size, -20), Vec2D(-size, 20)),
					70: (Vec2D(-size, -20), Vec2D(-size, 20)),
				}[size]
				translated_component["pins"]["A"] = component["loc"] + aoffset.rotate_offset(component.get(".facing", FaceDirection.East))
				translated_component["pins"]["B"] = component["loc"] + boffset.rotate_offset(component.get(".facing", FaceDirection.East))

			case ("#Gates.OR Gate", None):
				assert(component.get(".inputs", 2) == 2)
				translated_component["type"] = "AND"
				translated_component["pins"]["Y"] = component["loc"]

			case ("#Gates.NAND Gate", None):
				assert(component.get(".inputs", 2) == 2)
				translated_component["type"] = "NAND"
				translated_component["pins"]["Y"] = component["loc"]

			case ("#Gates.NOR Gate", None):
				assert(component.get(".inputs", 2) == 2)
				translated_component["type"] = "NOR"
				translated_component["pins"]["Y"] = component["loc"]

			case ("#Gates.XOR Gate", None):
				assert(component.get(".inputs", 2) == 2)
				translated_component["type"] = "XOR"
				translated_component["pins"]["Y"] = component["loc"]
				size = component.get(".size", 50)
				(aoffset, boffset) = {
					30: (Vec2D(-size - 10, -10), Vec2D(-size - 10, 10)),
					50: (Vec2D(-size - 10, -20), Vec2D(-size - 10, 20)),
					70: (Vec2D(-size - 10, -20), Vec2D(-size - 10, 20)),
				}[size]
				translated_component["pins"]["A"] = component["loc"] + aoffset.rotate_offset(component.get(".facing", FaceDirection.East))
				translated_component["pins"]["B"] = component["loc"] + boffset.rotate_offset(component.get(".facing", FaceDirection.East))

			case ("#Memory.D Flip-Flop", None):
				assert(component.get(".appearance") == "logisim_evolution")
				translated_component["type"] = "D-FlipFlop"
				translated_component["pins"]["D"] = component["loc"] + Vec2D(-10, 10)
				translated_component["pins"]["CLK"] = component["loc"] + Vec2D(-10, 50)
				translated_component["pins"]["Q"] = component["loc"] + Vec2D(50, 10)
				translated_component["pins"]["!Q"] = component["loc"] + Vec2D(50, 50)

		if translated_component["type"] is None:
			raise UnknownComponentException(f"Logisim component {component} is unknown to digtick.")

		return translated_component


	def parse(self):
		self._parse_libraries()
		net_nodes = set()
		for (src, dst) in self._iter_wires():
			net_nodes.add(src)
			net_nodes.add(dst)

		for pos in sorted(net_nodes):
			print(pos)

		for component in self._iter_components():
			resolved_component = self._resolve_component(component)
			for (pin_name, loc) in resolved_component["pins"].items():
				if loc not in net_nodes:
					print(f"No net for {resolved_component} {pin_name}")
			print()
		return self._circuit



if __name__ == "__main__":
	circuit = LogisimLoader("/tmp/awful.circ").parse()
	print(circuit)
