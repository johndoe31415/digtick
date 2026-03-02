#	digtick - Digital logic design toolkit: simplify, minimize and transform Boolean expressions, draw KV-maps, etc.
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
from .Exceptions import UndefinedInputUsedException, NoSuchPinException, WrongCircuitPowerStateException, CircuitAstableException

class UID():
	_Value = 0

	@classmethod
	def gen(cls):
		cls._Value += 1
		return cls._Value

class Level(enum.IntEnum):
	Low = 0
	High = 1
	Undefined = 2
	WeakLow = 3

class Net():
	def __init__(self, circuit: "Circuit"):
		self._circuit = circuit
		self._uid = UID.gen()
		self._level = Level.Undefined
		self._deferred_level = Level.Undefined
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
			raise UndefinedInputUsedException(f"Tried to read level of net {self}, but level of that net is undefined")
		return {
			Level.Low: 0,
			Level.High: 1,
			Level.WeakLow: 0,
		}[self._level]

	def reset(self):
		self._level = Level.WeakLow
		self._deferred_level = None

	def deferred_drive(self, value: int):
		assert(value in [ 0, 1 ])
		self._deferred_level = value

	def drive(self, value: int):
		assert(value in [ 0, 1 ])
		changed = self._level != value
		self._level = {
			0: Level.Low,
			1: Level.High,
		}[value]
		if changed:
			for (component, pin_name) in self._members:
				component.notify_pin_change(pin_name)

	def add_member(self, component: "Component", pin_name: str):
		self._members.add((component, pin_name))

	def dump(self):
		print(f"{self} level {self._level.name} nextlevel {self._deferred_level} with {len(self._members)} members:")
		for (component, pin_name) in self:
			print(f"    {component.type_name} {component.name}.{pin_name}")

	def commit(self):
		if self._deferred_level is not None:
			self.drive(self._deferred_level)
			self._deferred_level = None

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
		self._circuit = None

	@property
	def circuit(self):
		return self._circuit

	@circuit.setter
	def circuit(self, circuit: "Circuit"):
		assert(self._circuit is None)
		self._circuit = circuit

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

	@property
	def type_name(self):
		return self._Name

	def __getitem__(self, pin_name: str):
		return self._nets.get(pin_name)

	def connect(self, pin_name: str, net: Net):
		if (pin_name not in self._Inputs) and (pin_name not in self._Outputs):
			raise NoSuchPinException(f"Trying to connect net {net} to component {self}.{pin_name} but no pin {pin_name} exists (have IN = {self._Inputs} and OUT = {self._Outputs})")
		self._nets[pin_name] = net
		net.add_member(self, pin_name)

	def notify_pin_change(self, pin_name: str):
		if (pin_name in self._Inputs) and (self[pin_name] is not None):
			self.circuit.notify_change(self)

	def drive(self, pin_name: str, level: int, defer: bool = False):
		if self[pin_name] is not None:
			if defer:
				self[pin_name].deferred_drive(level)
			else:
				self[pin_name].drive(level)

	def reset(self):
		pass

	def tick(self):
		pass

	def finish_tick(self):
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
		if self._level != value:
			self.circuit.notify_change(self)
		self._level = value

	def toggle(self):
		self.level = self.level ^ 1

	def tick(self):
		self.drive("OUT", self._level)

class CmpSink(Component):
	_Outputs = [ "IN" ]
	_Name = "Sink"
	_NodeName = "Sink"
	_Prefix = "SNK"

	@property
	def level(self):
		return self["IN"].level

class CmpNOT(Component):
	_Inputs = [ "A" ]
	_Outputs = [ "Y" ]
	_Name = "NOT"
	_NodeName = "~"
	_Prefix = "IC"

	def tick(self):
		self.drive("Y", self["A"].level ^ 1)

class CmpGate(Component):
	_Inputs = [ "A", "B" ]
	_Outputs = [ "Y" ]
	_Prefix = "IC"

class CmpAND(CmpGate):
	_Name = "AND"
	_NodeName = "&&"

	def tick(self):
		self.drive("Y", self["A"].level & self["B"].level)

class CmpOR(CmpGate):
	_Name = "OR"
	_NodeName = "\\|\\|"

	def tick(self):
		super().tick()
		self.drive("Y", self["A"].level | self["B"].level)

class CmpXOR(CmpGate):
	_Name = "XOR"
	_NodeName = "^"

	def tick(self):
		self.drive("Y", self["A"].level ^ self["B"].level)

class CmpNAND(CmpGate):
	_Name = "NAND"
	_NodeName = "~&&"

	def tick(self):
		self.drive("Y", (self["A"].level & self["B"].level) ^ 1)

class CmpNOR(CmpGate):
	_Name = "NOR"
	_NodeName = "~\\|\\|"

	def tick(self):
		self.drive("Y", (self["A"].level | self["B"].level) ^ 1)

class CmpDFlipFlop(Component):
	_Inputs = [ "D", "CLK" ]
	_Outputs = [ "Q", "!Q" ]
	_Name = "D-FF"
	_NodeName = "D-FF"
	_Prefix = "IC"

	def __init__(self):
		super().__init__()
		self._last_clk = None
		self._state = 0
		self._defer = True

	@property
	def state(self) -> int:
		return self._state

	@state.setter
	def state(self, value: int):
		assert(value in [ 0, 1 ])
		if self._state != value:
			# Changes via setter act immediately
			self.circuit.notify_change(self)
			self._defer = False
		self._state = value

	def tick(self):
		if (self._last_clk == 0) and (self["CLK"].level == 1):
			# Positive edge detected!
			self._state = self["D"].level
		self._last_clk = self["CLK"].level
		self.drive("Q", self._state, defer = self._defer)
		self.drive("!Q", self._state ^ 1, defer = self._defer)
		self._defer = True

class Circuit():
	def __init__(self):
		self._components = set()
		self._nets = set()
		self._enumeration = collections.Counter()
		self._nets_stable = False
		self._powered_on = False
		self._changed_inputs = set()

	def add(self, component: Component):
		if self._powered_on:
			raise WrongCircuitPowerStateException("Unable to add component to powered on circuit")
		component.circuit = self
		self._enumeration[component._Prefix] +=	1
		no = self._enumeration[component._Prefix]
		self._components.add(component)
		component.no = no
		return component

	def notify_change(self, component: Component):
		self._changed_inputs.add(component)

	def _merge_nets(self, net1: Net, net2: Net):
		for (component, pin_name) in net2:
			component.connect(pin_name, net1)
		self._nets.remove(net2)
		return net1

	def connect(self, component1: Component, pin1_name: str, component2: Component, pin2_name: str, *additional_component_pin_names):
		if self._powered_on:
			raise WrongCircuitPowerStateException("Unable to change nets on powered on circuit")
		net1 = component1[pin1_name]
		net2 = component2[pin2_name]
		if (net1 is None) and (net2 is None):
			# No net exists yet
			net = Net(self)
			self._nets.add(net)
		elif net1 is None:
			# Only net2 exists
			net = net2
		elif net2 is None:
			# Only net1 exists
			net = net1
		else:
			# Both nets exist
			net = self._merge_nets(net1, net2)
		component1.connect(pin1_name, net)
		component2.connect(pin2_name, net)

		if len(additional_component_pin_names) > 0:
			(component3, pin3_name, *additional_component_pin_names) = additional_component_pin_names
			self.connect(component1, pin1_name, component3, pin3_name, *additional_component_pin_names)

	def power_on(self):
		for net in self._nets:
			net.reset()
		for component in self._components:
			self.notify_change(component)
		self._powered_on = True
		self.tick()

	def _settle(self):
		iteration = 0
		while len(self._changed_inputs) > 0:
			if iteration >= 50:
				raise CircuitAstableException("Circuit does not settle, probably because of cyclic wiring/oscillating behavior. Unable to simulate.")
			iteration += 1
			needs_tick = self._changed_inputs
			self._changed_inputs = set()
			for component in needs_tick:
				component.tick()

	def tick(self):
		if not self._powered_on:
			raise WrongCircuitPowerStateException("Circuit has not yet been powered on.")
		self._settle()
		for net in self._nets:
			net.commit()
		self._settle()

	def dump(self, text: str | None = None):
		heading = f"{'~' * 50} {text or 'Dumping circuit'} {'~' * 50}"
		print(heading)
		for component in self._components:
			if isinstance(component, CmpSource):
				print(f"Source: {component} level {component.level}")
			else:
				print(f"Component: {component}")

		for net in sorted(self._nets):
			net.dump()
		print("~" * len(heading))

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

	source = circ.add(CmpSource(0))
	gate = circ.add(CmpNOT())
	sink = circ.add(CmpSink())

	circ.connect(source, "OUT", gate, "A")
	circ.connect(gate, "Y", sink, "IN")
	circ.power_on()

	for i in range(10):
		source.toggle()
		circ.tick()
		print(source.level, sink.level)
		assert(source.level ^ 1  == sink.level)
