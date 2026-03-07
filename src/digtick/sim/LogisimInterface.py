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

import sys
import enum
import collections
import dataclasses
import xml.etree.ElementTree
from digtick.sim import Circuit, Component
from digtick.Exceptions import NoSuchCircuitException, UnknownComponentException

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

			case _:	# pragma unreachable
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
		def _common_pin_offsets(x_value: int, input_count: int):
			for i in reversed(range(1, (input_count // 2) + 1)):
				yield Vec2D(x_value, -10 * i)
			if (input_count % 2) != 0:
				yield Vec2D(x_value, 0)
			for i in range(1, (input_count // 2) + 1):
				yield Vec2D(x_value, 10 * i)

		# This is incredibly cursed, especially wide components. For a gate
		# facing East (having the output right), the Y-offsets are:
		#
		# Inputs	Narrow				Medium					Wide
		# 2			-10/+10				-20/+20					-20/+20
		# 3			-10/0/+10			-20/0/+20				-30/0/+30
		# 4			-20/-10/+10/+20		-20/-10/+10/+20			-30/-10/+10/+30
		# 5			-20/-10/0/+10/+20	-20/-10/0/+10/+20		-20/-10/0/+10/+20
		# 6								-30/-20/-10/+10/...		-30/-20/-10/10/20/30
		# 7														-30/-20/-10/0/10/20/30
		# 8														-40/-30/-20/-10/+10/...

		size = component.get(".size", 50)
		input_count = component.get(".inputs", 2)
		match (size, input_count):
			case (30, _):
				pin_offsets = list(_common_pin_offsets(x_value = -size + xoffset, input_count = input_count))

			case (50, 2):
				pin_offsets = [ Vec2D(-size + xoffset, y_offset) for y_offset in [ -20, 20 ] ]

			case (50, 3):
				pin_offsets = [ Vec2D(-size + xoffset, y_offset) for y_offset in [ -20, 0, 20 ] ]

			case (50, _):
				pin_offsets = list(_common_pin_offsets(x_value = -size + xoffset, input_count = input_count))

			case (70, 2):
				pin_offsets = [ Vec2D(-size + xoffset, y_offset) for y_offset in [ -20, 20 ] ]

			case (70, 3):
				pin_offsets = [ Vec2D(-size + xoffset, y_offset) for y_offset in [ -30, 0, 30 ] ]

			case (70, 4):
				pin_offsets = [ Vec2D(-size + xoffset, y_offset) for y_offset in [ -30, -10, 10, 30 ] ]

			case (70, _):
				pin_offsets = list(_common_pin_offsets(x_value = -size + xoffset, input_count = input_count))

			case (_, _):
				raise UnknownComponentException(f"Logisim component {component} has unhandled size/input count: {size}, {input_count}")

		# Rotation in Logisim is not *actually* rotation. Instead, what Logisim
		# uses is a method known under the scientific term "batshit insane pin
		# assignment algorithm" where through rotation also the pin numbering
		# changes:
		#
		# Face direction		Pin order
		# East (right)			Top -> bottom
		# South (down)			Left -> right (!)
		# West (left)			Top -> bottom (!)
		# North (up)			Left -> right
		#
		# Counting happens from zero (i.e., "negate0" means Pin 1). For each
		# negated input, the X-distance of the pin decreases by 10 units.
		face_direction = component.get(".facing", FaceDirection.East)
		if face_direction in [ FaceDirection.North ]:
			pin_offsets.reverse()

		if len(pin_offsets) == 2:
			pin_names = [ "A", "B" ]
		else:
			pin_names = [ f"A{i}" for i in range(1, len(pin_offsets) + 1) ]

		print(f"Pin locations for {component.get('.label', 'unnamed')} {input_count}-input {component['name']} at {component['loc']} face direction {face_direction.name}", file = sys.stderr)
		print(f"    Pin offsets initial: {pin_offsets}", file = sys.stderr)
		translated_component["inverted_inputs"] = set()
		for (index, pin) in enumerate(pin_offsets):
			if component.get(f".negate{index}", "false") == "true":
				translated_component["inverted_inputs"].add(pin_names[index])
				pin_offsets[index] = pin + Vec2D(-10, 0)
		print(f"         With inversion: {pin_offsets}", file = sys.stderr)


		for (pin_name, offset) in zip(pin_names, pin_offsets):
			translated_component["pins"][pin_name] = component["loc"] + offset.rotate_offset(face_direction)
			print(f"                  Final: {pin_name} {offset.rotate_offset(face_direction)} -> {translated_component['pins'][pin_name]}", file = sys.stderr)

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
				translated_component["type"] = "NOT"
				translated_component["pins"]["Y"] = component["loc"]
				translated_component["pins"]["A"] = component["loc"] + Vec2D(-component.get(".size", 30), 0).rotate_offset(component.get(".facing", FaceDirection.East))

			case ("#Gates.AND Gate", None):
				translated_component["type"] = "AND"
				translated_component["input_count"] = component.get(".inputs", 2)
				translated_component["pins"]["Y"] = component["loc"]
				self._find_gate_pin_locations(component, translated_component)

			case ("#Gates.OR Gate", None):
				translated_component["type"] = "OR"
				translated_component["input_count"] = component.get(".inputs", 2)
				translated_component["pins"]["Y"] = component["loc"]
				self._find_gate_pin_locations(component, translated_component)

			case ("#Gates.NAND Gate", None):
				translated_component["type"] = "NAND"
				translated_component["input_count"] = component.get(".inputs", 2)
				translated_component["pins"]["Y"] = component["loc"]
				self._find_gate_pin_locations(component, translated_component, xoffset = -10)

			case ("#Gates.NOR Gate", None):
				translated_component["type"] = "NOR"
				translated_component["input_count"] = component.get(".inputs", 2)
				translated_component["pins"]["Y"] = component["loc"]
				self._find_gate_pin_locations(component, translated_component, xoffset = -10)

			case ("#Gates.XOR Gate", None):
				translated_component["type"] = "XOR"
				translated_component["input_count"] = component.get(".inputs", 2)
				translated_component["pins"]["Y"] = component["loc"]
				translated_component["model"] = component.get(".xor", "=1")
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

			case ("#Base.Text", None):
				return None

		if translated_component["type"] is None:
			raise UnknownComponentException(f"Logisim component {component} is unknown to digtick.")

		return translated_component

	def _add_net(self, src: Vec2D, dst: Vec2D):
		if (src in self._net_id_by_pos) and (dst not in self._net_id_by_pos):
			# Continue existing net
			net_id = self._net_id_by_pos[src]
		elif (dst in self._net_id_by_pos) and (src not in self._net_id_by_pos):
			# Continue existing net
			net_id = self._net_id_by_pos[dst]
		elif (dst not in self._net_id_by_pos) and (src not in self._net_id_by_pos):
			# Create new net
			net_id = self._max_net_id
			self._max_net_id += 1
		else:
			# Join two self._net_id_by_pos
			net_id = self._net_id_by_pos[src]
			old_net_id = self._net_id_by_pos[dst]
			for old_pos in self._pos_by_net_id[old_net_id]:
				self._net_id_by_pos[old_pos] = net_id
				self._pos_by_net_id[net_id].add(old_pos)
			del self._pos_by_net_id[old_net_id]

		self._net_id_by_pos[src] = net_id
		self._net_id_by_pos[dst] = net_id
		self._pos_by_net_id[net_id].add(src)
		self._pos_by_net_id[net_id].add(dst)

	def _parse_nets(self):
		self._net_id_by_pos = { }
		self._pos_by_net_id = collections.defaultdict(set)
		self._max_net_id = 0
		for (src, dst) in self._iter_wires():
			self._add_net(src, dst)

	def dump_nets(self):
		for (pos, net_id) in sorted(self._net_id_by_pos.items(), key = lambda pnetid: (pnetid[1], pnetid[0])):
			print(pos, net_id, file = sys.stderr)

	def _parse_components(self):
		self._circuit = Circuit()
		self._components = [ ]
		for component_dict in self._iter_components():
			resolved_component = self._resolve_component(component_dict)
			if resolved_component is None:
				continue

			component = Component.from_dict(resolved_component)
			self._circuit.add(component)
			resolved_component["instance"] = component
			self._components.append(resolved_component)

			# Each pin spans its own net so that direcly overlapping pins get
			# connected together
			for (pin_name, pin_location) in resolved_component["pins"].items():
				self._add_net(pin_location, pin_location)

	def _wire_components(self):
		connected_nets = collections.defaultdict(list)
		for resolved_component in self._components:
			for (pin_name, loc) in resolved_component["pins"].items():
				if loc in self._net_id_by_pos:
					net_id = self._net_id_by_pos[loc]
					connected_nets[net_id].append(resolved_component["instance"])
					connected_nets[net_id].append(pin_name)

		for (net_id, connected_component_pins) in connected_nets.items():
			if len(connected_component_pins) < 4:
				# Lonely wire
				continue
			self._circuit.connect(*connected_component_pins)

	def parse(self):
		self._parse_libraries()
		self._parse_nets()
		self._parse_components()
		self._wire_components()
		return self._circuit
