#	digtick - Digital systems toolkit: simplify, minimize and transform Boolean expressions, draw KV-maps, etc.
#	Copyright (C) 2026-2026 Johannes Bauer
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

class UID():
	_Value = 0
	@classmethod
	def gen(cls):
		cls._Value += 1
		return cls._Value

class Level(enum.IntEnum):
	Undefined = 0
	WeakLow = 1
	StrongLow = 2
	WeakHigh = 4
	StrongHigh = 8

class Net():
	def __init__(self, circuit: "Circuit"):
		self._circuit = circuit
		self._uid = UID.gen()
		self._level = Level.Undefined
		self._next_level = Level.Undefined
		self._members = set()

	@property
	def nid(self):
		return self._uid

	@property
	def name(self):
		return repr(self)

	@property
	def member_count(self):
		return len(self._members)

	@property
	def level(self) -> int:
		if self._level == Level.Undefined:
			raise ValueError(f"Tried to read level of undefined network {self}")
		return {
			Level.WeakLow: 0,
			Level.StrongLow: 0,
			Level.WeakHigh: 1,
			Level.StrongHigh: 1,
		}[self._level]

	def force(self, level: Level):
		if self._level != level:
			self._circuit.notify_net_change(self)
		self._level = Level(level)
		self._next_level = 0

	def drive(self, value: int):
		assert(value in [ 0, 1 ])
		self._next_level |= {
			0: Level.StrongLow,
			1: Level.StrongHigh,
		}[value]

	def add_member(self, component: "Component", pin_name: str):
		self._members.add((component, pin_name))

	def dump(self):
		print(f"{self} level {self._level.name} nextlevel {self._next_level} with {len(self._members)} members:")
		for (component, pin_name) in self:
			print(f"    {component}.{pin_name}")

	def tick(self):
		# TODO handle collision
		self.force(self._next_level)

	def __iter__(self):
		return iter(self._members)

	def __eq__(self, other: "Net"):
		return self.nid == other.nid

	def __lt__(self, other: "Net"):
		return self.nid < other.nid

	def __hash__(self):
		return hash(self.nid)

	def __repr__(self):
		return f"Net{self.nid}"

class Component():
	_Inputs = [ ]
	_Outputs = [ ]
	_Name = None
	_Prefix = None

	def __init__(self):
		self._uid = UID.gen()
		self._no = None
		self._nets = { }

	@property
	def cid(self):
		return self._uid

	@property
	def no(self):
		return self._no

	@no.setter
	def no(self, value: int):
		assert(self._no is None)
		assert(isinstance(value, int))
		self._no = value

	@property
	def name(self):
		return f"{self._Prefix}{self.no}"

	def __getitem__(self, pin_name: str):
		return self._nets.get(pin_name)

	def connect(self, pin_name: str, net: Net):
		assert((pin_name in self._Inputs) or (pin_name in self._Outputs))
		self._nets[pin_name] = net
		net.add_member(self, pin_name)

	def tick(self):
		pass

	def __eq__(self, other: "Component"):
		return self.cid == other.cid

	def __lt__(self, other: "Component"):
		return self.cid < other.cid

	def __hash__(self):
		return hash(self.cid)

	def __str__(self):
		return f"{self.name}: {self._Name}"

	def __repr__(self):
		return f"#{self.cid}<{str(self)}>"

class CmpSource(Component):
	_Outputs = [ "OUT" ]
	_Name = "Source"
	_NodeName = "Src"
	_Prefix = "SRC"

	def __init__(self, level: int):
		super().__init__()
		self._level = level

	@property
	def level(self):
		return self._level

	@level.setter
	def level(self, value: int):
		assert(isinstance(value, int))
		assert(value in [ 0, 1 ])
		self._level = value

	def tick(self):
		self["OUT"].drive(self._level)

class CmpSink(Component):
	_Outputs = [ "IN" ]
	_Name = "Sink"
	_NodeName = "Sink"
	_Prefix = "SNK"

class CmpInv(Component):
	_Outputs = [ "A" ]
	_Outputs = [ "Y" ]
	_Name = "NOT"
	_NodeName = "~"
	_Prefix = "IC"

	def __init__(self):
		super().__init__()

	def tick(self):
		self["OUT"].drive(self["IN"].level ^ 1)

class CmpGate(Component):
	_Inputs = [ "A", "B" ]
	_Outputs = [ "Y" ]
	_Prefix = "IC"

class CmpAND(CmpGate):
	_Name = "AND"
	_NodeName = "&&"
	def tick(self):
		self["Y"].drive(self["A"].level & self["B"].level)

class CmpOR(CmpGate):
	_Name = "OR"
	_NodeName = "\\|\\|"
	def tick(self):
		self["Y"].drive(self["A"].level | self["B"].level)

class CmpXOR(CmpGate):
	_Name = "XOR"
	_NodeName = "^"
	def tick(self):
		self["Y"].drive(self["A"].level ^ self["B"].level)

class CmpNAND(CmpGate):
	_Name = "NAND"
	_NodeName = "~&&"
	def tick(self):
		self["Y"].drive((self["A"].level & self["B"].level) ^ 1)

class CmpNOR(CmpGate):
	_Name = "NOR"
	_NodeName = "~\\|\\|"
	def tick(self):
		self["Y"].drive((self["A"].level | self["B"].level) ^ 1)


class Circuit():
	def __init__(self):
		self._components = set()
		self._nets = set()
		self._enumeration = collections.Counter()
		self._nets_stable = False

	def notify_net_change(self, net: Net):
		self._nets_stable = False

	def add(self, component: Component):
		self._enumeration[component._Prefix] +=	1
		no = self._enumeration[component._Prefix]
		self._components.add(component)
		component.no = no
		return component

	def _merge_nets(self, net1: Net, net2: Net):
		TODO

	def connect(self, component1: Component, pin1_name: str, component2: Component, pin2_name: str):
		net1 = component1[pin1_name]
		net2 = component2[pin2_name]
		if (net1 is None) and (net2 is None):
			# No net exists yet
			net = Net(self)
			self._nets.add(net)
		elif net1 is None:
			# Only net2 exists
			net = net2
		elif net1 is None:
			# Only net1 exists
			net = net1
		else:
			# Both nets exist
			net = self.merge_nets(net1, net2)
		component1.connect(pin1_name, net)
		component2.connect(pin2_name, net)

	def reset(self):
		for net in self._nets:
			net.force(Level.WeakLow)
		circ.settle()

	def tick(self):
		for component in self._components:
			component.tick()
		for net in self._nets:
			net.tick()

	def settle(self):
		while True:
			self._nets_stable = True
			self.tick()
			if self._nets_stable:
				break

	def dump(self):
		for net in sorted(self._nets):
			net.dump()

	def print(self):
		print("digraph circuit {")
		print("	graph [ layout=neato, overlap=false, splines=true ];")
		print("	node [shape=record, fontsize=12, margin=\"0.05,0.05\"];")
		print("	edge [arrowhead=none];")
		for net in sorted(self._nets):
			if net.member_count > 2:
				print(f"	{net.name} [shape=plain, label=\"{net.name}\"];")

		for component in sorted(self._components):
			inputs = "|".join(f"<{name}>{name}" for name in component._Inputs)
			outputs = "|".join(f"<{name}>{name}" for name in component._Outputs)
			print(f"	{component.name} [label=\"{{ {{{inputs}}} | {component._NodeName} | {{{outputs}}} }}\"];")

		for net in sorted(self._nets):
			if net.member_count > 2:
				print(f"	{net.name} [shape=plain, label=\"{net.name}\"];")
				for (comp, pin) in net:
					print(f"	{comp.name}:{pin} -> {net.name};")
			elif net.member_count == 2:
				((comp1, pin1), (comp2, pin2)) = list(net)
				print(f"	{comp1.name}:{pin1} -> {comp2.name}:{pin2};")

		print("}")
if __name__ == "__main__":
	circ = Circuit()

	xor = circ.add(CmpXOR())
	pin1 = circ.add(CmpSource(0))
	pin2 = circ.add(CmpSource(1))
	out = circ.add(CmpSink())

	circ.connect(xor, "A", pin1, "OUT")
	circ.connect(xor, "B", pin2, "OUT")
	circ.connect(xor, "Y", out, "IN")

	circ.reset()
	circ.dump()

	pin1.level = 0
	circ.settle()
	circ.dump()

	#pin2.level = 1
	#circ.tick()
	#circ.tick()
	#print(out["IN"].level)
