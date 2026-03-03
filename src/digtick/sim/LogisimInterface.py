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
import collections
import dataclasses
import xml.etree.ElementTree
from digtick.sim import Circuit, Component
from digtick.Exceptions import NoSuchCircuitException

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
	def __init__(self, doc: xml.etree.ElementTree.Element, circuit_name: str = "main"):
		self._doc = doc
		self._circuit_name = circuit_name
		self._root = self._doc.getroot()
		self._xml_circuit = self._root.find(f"./circuit[@name='{self._circuit_name}']")
		if self._xml_circuit is None:
			raise NoSuchCircuitException(f"Unable to find a circuit named \"{self._circuit_name}\" in the provided file.")
		self._libraries = { }
		self._circuit = None

	@classmethod
	def load_from_file(cls, filename: str, circuit_name: str = "main"):
		doc = xml.etree.ElementTree.parse(filename)
		return cls(doc = doc, circuit_name = circuit_name)

	@classmethod
	def load_from_xmldata(cls, xmldata: bytes, circuit_name: str = "main"):
		doc = xml.etree.ElementTree.ElementTree(xml.etree.ElementTree.fromstring(xmldata))
		return cls(doc = doc, circuit_name = circuit_name)

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

	def _find_gate_pin_locations(self, component: dict, translated_component: dict, xoffset: int = 0):
		size = component.get(".size", 50)
		(aoffset, boffset) = {
			30: (Vec2D(-size + xoffset, -10), Vec2D(-size + xoffset, 10)),
			50: (Vec2D(-size + xoffset, -20), Vec2D(-size + xoffset, 20)),
			70: (Vec2D(-size + xoffset, -20), Vec2D(-size + xoffset, 20)),
		}[size]
		translated_component["pins"]["A"] = component["loc"] + aoffset.rotate_offset(component.get(".facing", FaceDirection.East))
		translated_component["pins"]["B"] = component["loc"] + boffset.rotate_offset(component.get(".facing", FaceDirection.East))

	def _resolve_component(self, component: dict):
		translated_component = {
			"type": None,
			"pins": { },
		}
		if ".label" in component:
			translated_component["label"] = component[".label"]
		match (component["name"], component.get(".type")):
			case ("#Wiring.Pin", "output"):
				translated_component["type"] = "Sink"
				translated_component["pins"]["IN"] = component["loc"]

			case ("#Wiring.Pin", None):
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
				self._find_gate_pin_locations(component, translated_component)

			case ("#Gates.OR Gate", None):
				assert(component.get(".inputs", 2) == 2)
				translated_component["type"] = "OR"
				translated_component["pins"]["Y"] = component["loc"]
				self._find_gate_pin_locations(component, translated_component)

			case ("#Gates.NAND Gate", None):
				assert(component.get(".inputs", 2) == 2)
				translated_component["type"] = "NAND"
				translated_component["pins"]["Y"] = component["loc"]
				self._find_gate_pin_locations(component, translated_component, xoffset = -10)

			case ("#Gates.NOR Gate", None):
				assert(component.get(".inputs", 2) == 2)
				translated_component["type"] = "NOR"
				translated_component["pins"]["Y"] = component["loc"]
				self._find_gate_pin_locations(component, translated_component, xoffset = -10)

			case ("#Gates.XOR Gate", None):
				assert(component.get(".inputs", 2) == 2)
				translated_component["type"] = "XOR"
				translated_component["pins"]["Y"] = component["loc"]
				self._find_gate_pin_locations(component, translated_component, xoffset = -10)

			case ("#Memory.D Flip-Flop", None):
				assert(component.get(".appearance") == "logisim_evolution")
				translated_component["type"] = "D-FF"
				translated_component["pins"]["D"] = component["loc"] + Vec2D(-10, 10)
				translated_component["pins"]["CLK"] = component["loc"] + Vec2D(-10, 50)
				translated_component["pins"]["Q"] = component["loc"] + Vec2D(50, 10)
				translated_component["pins"]["!Q"] = component["loc"] + Vec2D(50, 50)

			case ("#Memory.J-K Flip-Flop", None):
				assert(component.get(".appearance") == "logisim_evolution")
				translated_component["type"] = "JK-FF"
				translated_component["pins"]["J"] = component["loc"] + Vec2D(-10, 10)
				translated_component["pins"]["K"] = component["loc"] + Vec2D(-10, 30)
				translated_component["pins"]["CLK"] = component["loc"] + Vec2D(-10, 50)
				translated_component["pins"]["Q"] = component["loc"] + Vec2D(50, 10)
				translated_component["pins"]["!Q"] = component["loc"] + Vec2D(50, 50)

		if translated_component["type"] is None:
			raise UnknownComponentException(f"Logisim component {component} is unknown to digtick.")

		return translated_component

	def _parse_nets(self):
		self._net_id_by_pos = { }
		pos_by_net_id = collections.defaultdict(set)
		max_net_id = 0
		for (src, dst) in self._iter_wires():
			if (src in self._net_id_by_pos) and (dst not in self._net_id_by_pos):
				# Continue existing net
				net_id = self._net_id_by_pos[src]
			elif (dst in self._net_id_by_pos) and (src not in self._net_id_by_pos):
				# Continue existing net
				net_id = self._net_id_by_pos[dst]
			elif (dst not in self._net_id_by_pos) and (src not in self._net_id_by_pos):
				# Create new net
				net_id = max_net_id
				max_net_id += 1
			else:
				# Join two self._net_id_by_pos
				net_id = self._net_id_by_pos[src]
				old_net_id = self._net_id_by_pos[dst]
				for old_pos in pos_by_net_id[old_net_id]:
					self._net_id_by_pos[old_pos] = net_id
					pos_by_net_id[net_id].add(old_pos)
				del pos_by_net_id[old_net_id]

			self._net_id_by_pos[src] = net_id
			self._net_id_by_pos[dst] = net_id
			pos_by_net_id[net_id].add(src)
			pos_by_net_id[net_id].add(dst)

	def _dump_nets(self):
		for (pos, net_id) in sorted(self._net_id_by_pos.items(), key = lambda pnetid: (pnetid[1], pnetid[0])):
			print(pos, net_id)

	def _parse_components(self):
		self._circuit = Circuit()
		self._components = [ ]
		for component_dict in self._iter_components():
			resolved_component = self._resolve_component(component_dict)

			component = Component.new(resolved_component["type"], label = resolved_component.get("label"))
			self._circuit.add(component)
			resolved_component["instance"] = component
			self._components.append(resolved_component)

	def _wire_components(self):
		connected_nets = collections.defaultdict(list)
		for resolved_component in self._components:
			for (pin_name, loc) in resolved_component["pins"].items():
				if loc in self._net_id_by_pos:
					net_id = self._net_id_by_pos[loc]
					connected_nets[net_id].append(resolved_component["instance"])
					connected_nets[net_id].append(pin_name)

		for (net_id, connected_component_pins) in connected_nets.items():
			self._circuit.connect(*connected_component_pins)


	def parse(self):
		self._parse_libraries()
		self._parse_nets()
#		self._dump_nets()
		self._parse_components()
		self._wire_components()
		return self._circuit



if __name__ == "__main__":
	circuit = LogisimLoader("examples/awful.circ").parse()
	#circuit.dump()
	circuit.power_on()
	computed_result = circuit.build_table()
	computed_result.print()

#	circuit["C"].level = 1
#	circuit.tick()
#	print("V=",circuit["V"].level)
