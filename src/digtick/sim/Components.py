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

from .UID import UID

class Component():
	_KNOWN_COMPONENTS = { }
	_Inputs = [ ]
	_Outputs = [ ]
	_Name = None
	_Prefix = None

	def __init__(self):
		self._uid = UID.gen()
		self._no = None
		self._nets = { }
		self._circuit = None

	def __init_subclass__(cls, **kwargs):
		if cls._Name is None:
			return
		assert(cls._Prefix is not None)
		cls._KNOWN_COMPONENTS[cls._Name] = cls

	@classmethod
	def new(cls, name: str, *args, **kwargs):
		return cls._KNOWN_COMPONENTS[name](*args, **kwargs)

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

	def connect(self, pin_name: str, net: "Net"):
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

	def __init__(self, level: int = 0):
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
