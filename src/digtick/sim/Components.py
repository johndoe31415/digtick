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

import operator
import collections
from functools import reduce
from digtick.Exceptions import NoSuchPinException, InputPinUnconnectedException
from .UID import UID

class Component():
	_KNOWN_COMPONENTS = { }
	_Name = None
	_Prefix = None

	def __init__(self, label: str | None = None):
		self._label = label
		self._uid = UID.gen()
		self._no = None
		self._inputs = [ ]
		self._outputs = [ ]
		self._nets = { }
		self._circuit = None

	def __init_subclass__(cls, **kwargs):
		if cls._Name is None:
			return
		assert(cls._Prefix is not None)
		cls._KNOWN_COMPONENTS[cls._Name] = cls

	@property
	def label(self):
		return self._label

	@classmethod
	def new(cls, name: str, *args, **kwargs):
		return cls._KNOWN_COMPONENTS[name](*args, **kwargs)

	@classmethod
	def from_dict(cls, component_dict: dict):
		kwargs = { }
		if "label" in component_dict:
			kwargs["label"] = component_dict["label"]
		if "input_count" in component_dict:
			kwargs["input_count"] = component_dict["input_count"]
		if "inverted_inputs" in component_dict:
			kwargs["inverted_inputs"] = component_dict["inverted_inputs"]
		if "model" in component_dict:
			kwargs["model"] = component_dict["model"]
		return cls.new(name = component_dict["type"], **kwargs)

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

	def input_level(self, input_pin_name: str) -> int:
		net = self[input_pin_name]
		if net is None:
			raise InputPinUnconnectedException(f"Component {self} tried to read pin {input_pin_name} which is not connected to any net.")
		return net.level

	def add_pins(self, input_pin_names: list[str] | None = None, output_pin_names: list[str] | None = None):
		if input_pin_names is not None:
			self._inputs += input_pin_names
		if output_pin_names is not None:
			self._outputs += output_pin_names
		return self

	def __getitem__(self, pin_name: str):
		return self._nets.get(pin_name)

	def connect(self, pin_name: str, net: "Net"):
		if (pin_name not in self._inputs) and (pin_name not in self._outputs):
			raise NoSuchPinException(f"Trying to connect net {net} to component {self}.{pin_name} but no pin {pin_name} exists (have IN = {self._inputs} and OUT = {self._outputs})")
		self._nets[pin_name] = net
		net.add_member(self, pin_name)

	def notify_pin_change(self, pin_name: str):
		if (pin_name in self._inputs) and (self[pin_name] is not None):
			self.circuit.notify_change(self)

	def drive(self, pin_name: str, level: int, defer: bool = False):
		if self[pin_name] is not None:
			if defer:
				self[pin_name].deferred_drive(level)
			else:
				self[pin_name].drive(level)

	def tick(self):
		pass

	def __eq__(self, other: "Component"):
		return self.cid == other.cid

	def __lt__(self, other: "Component"):
		return self.cid < other.cid

	def __hash__(self):
		return hash(self.cid)

	def __str__(self):
		if self.label is None:
			return f"{self.name}: {self._Name}"
		else:
			return f"{self.name} ({self.label}): {self._Name}"

	def __repr__(self):
		return f"#{self.cid}<{str(self)}>"

class CmpSource(Component):
	_Name = "Source"
	_NodeName = "Src"
	_Prefix = "SRC"

	def __init__(self, label: str | None = None, level: int = 0):
		super().__init__(label = label)
		self.add_pins(output_pin_names = [ "OUT" ])
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
	_Name = "Sink"
	_NodeName = "Sink"
	_Prefix = "SNK"

	def __init__(self, label: str | None = None):
		super().__init__(label = label)
		self.add_pins(input_pin_names = [ "IN" ])

	@property
	def level(self):
		return self.input_level("IN")

class CmpNOT(Component):
	_Name = "NOT"
	_NodeName = "~"
	_Prefix = "IC"

	def __init__(self, label: str | None = None):
		super().__init__(label = label)
		self.add_pins(input_pin_names = [ "A" ], output_pin_names = [ "Y" ])

	def tick(self):
		self.drive("Y", self.input_level("A") ^ 1)

class CmpGate(Component):
	_Prefix = "IC"

	def __init__(self, label: str | None = None, input_count: int = 2, inverted_inputs: set | None = None):
		super().__init__(label = label)
		self._inverted_inputs = set() if (inverted_inputs is None) else inverted_inputs
		if input_count == 2:
			self.add_pins(input_pin_names = [ "A", "B" ], output_pin_names = [ "Y" ])
		else:
			self._Name = f"{input_count}-{self._Name}"
			self.add_pins(input_pin_names = [ f"A{n}" for n in range(1, input_count + 1) ], output_pin_names = [ "Y" ])

	@property
	def input_levels(self):
		return [ (self.input_level(pin_name) ^ 1) if (pin_name in self._inverted_inputs) else self.input_level(pin_name) for pin_name in self._inputs ]

class CmpAND(CmpGate):
	_Name = "AND"
	_NodeName = "&&"

	def tick(self):
		self.drive("Y", reduce(operator.and_, self.input_levels))

class CmpOR(CmpGate):
	_Name = "OR"
	_NodeName = "\\|\\|"

	def tick(self):
		self.drive("Y", reduce(operator.or_, self.input_levels))

class CmpXOR(CmpGate):
	_Name = "XOR"
	_NodeName = "^"

	def __init__(self, label: str | None = None, input_count: int = 2, inverted_inputs: set | None = None, model: str = "odd"):
		super().__init__(label = label, input_count = input_count, inverted_inputs = inverted_inputs)
		assert(model in [ "odd", "=1" ])
		self._model = model

	def tick(self):
		if self._model == "odd":
			# Return one if an odd number of inputs is one
			self.drive("Y", reduce(operator.xor, self.input_levels))
		else:
			# Return one only if *exactly* one input is one
			self.drive("Y", int(collections.Counter(self.input_levels)[1] == 1))

class CmpNAND(CmpGate):
	_Name = "NAND"
	_NodeName = "~&&"

	def tick(self):
		self.drive("Y", reduce(operator.and_, self.input_levels) ^ 1)

class CmpNOR(CmpGate):
	_Name = "NOR"
	_NodeName = "~\\|\\|"

	def tick(self):
		self.drive("Y", reduce(operator.or_, self.input_levels) ^ 1)

class CmpDFlipFlop(Component):
	_Name = "D-FF"
	_NodeName = "D-FF"
	_Prefix = "IC"

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.add_pins(input_pin_names = [ "D", "CLK" ], output_pin_names = [ "Q", "!Q" ])
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
		if (self._last_clk == 0) and (self.input_level("CLK") == 1):
			# Positive edge detected!
			self._state = self.input_level("D")
		self._last_clk = self.input_level("CLK")
		self.drive("Q", self._state, defer = self._defer)
		self.drive("!Q", self._state ^ 1, defer = self._defer)
		self._defer = True

class CmpJKFlipFlop(Component):
	_Name = "JK-FF"
	_NodeName = "JK-FF"
	_Prefix = "IC"

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.add_pins(input_pin_names = [ "J", "K", "CLK" ], output_pin_names = [ "Q", "!Q" ])
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
		if (self._last_clk == 0) and (self.input_level("CLK") == 1):
			# Positive edge detected!
			jk = (self.input_level("J"), self.input_level("K"))
			if jk == (1, 0):
				# Set
				self._state = 1
			elif jk == (0, 1):
				# Set
				self._state = 0
			elif jk == (1, 1):
				# Toggle
				self._state = self._state ^ 1
		self._last_clk = self.input_level("CLK")
		self.drive("Q", self._state, defer = self._defer)
		self.drive("!Q", self._state ^ 1, defer = self._defer)
		self._defer = True
