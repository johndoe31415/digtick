#	digtick - Digital systems toolkit: simplify, minimize and transform Boolean expressions, draw KV-maps, etc.
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

import random
import collections
from .MultiCommand import BaseAction
from .PRNG import PRNG

class SequenceDiagramGenerator():
	_Signal = collections.namedtuple("Signal", [ "name", "values" ])

	def __init__(self):
		self._signals = [ ]
		self._signal_dict = { }
		self._annotations = collections.defaultdict(dict)
		self._signal_length = 0
		self._signal_name_alias = { }

	@property
	def signal_count(self):
		return len(self._signals)

	def add_signal_alias(self, internal_name, apparent_name):
		self._signal_name_alias[internal_name] = apparent_name

	def add_signal(self, name, values):
		values = [ int(value) for value in values ]
		signal = self._Signal(name = name, values = values)
		self._signals.append(signal)
		self._signal_length = max(self._signal_length, len(signal.values))
		self._signal_dict[signal.name] = signal
		return self

	def	add_random_signal(self, prng, name, length, toggle_chance = 25):
		value = prng.randint(0, 1)
		rndvect = [ ]
		for i in range(length):
			if prng.randint(0, 100) < toggle_chance:
				value = int(not value)
			rndvect.append(value)
		return self.add_signal(name, rndvect)

	def annotate(self, name, index, text = None):
		self._annotations[name][index] = text

	def append(self, name, value):
		if name not in self._signal_dict:
			self.add_signal(name, [ ])
		signal = self._signal_dict[name]
		signal.values.append(int(value))
		self._signal_length = max(self._signal_length, len(signal.values))

	def simulate(self, simulator):
		prev = { signal.name: None for signal in self._signals }
		for index in range(self._signal_length):
			now = { signal.name: signal.values[index] if (index < len(signal.values)) else None for signal in self._signals }
			simulator.tick(self, index, prev, now)
			prev = now

	def _format_entry(self, signal, index):
		value = str(signal.values[index])
		if index in self._annotations[signal.name]:
			value += "|"
			if self._annotations[signal.name][index] is not None:
				value += f"'{self._annotations[signal.name][index]}'"
		return value

	def format(self):
		lines = [ ]
		max_name_length = max(len(self._signal_name_alias.get(signal.name, signal.name)) for signal in self._signals)
		max_col_widths = [ max(len(self._format_entry(self._signals[signo], index)) for signo in range(self.signal_count)) for index in range(self._signal_length) ]
		for signal in self._signals:
			signal_name = self._signal_name_alias.get(signal.name, signal.name)
			line = f"{signal_name:{max_name_length}s} = "
			for index in range(self._signal_length):
				line += f"{self._format_entry(signal, index):{max_col_widths[index]}s}"
			lines.append(line)
		return lines

	def print(self):
		print("\n".join(self.format()))

class DFlipflop():
	def __init__(self, initial_state: int = 0, pos_edge: bool = True):
		self._state = initial_state
		self._pos_edge = pos_edge

	def tick(self, sdg, index, prev, now):
		if ((self._pos_edge) and (prev["C"] == 0) and ((now["C"] == 1))) or ((not self._pos_edge) and (prev["C"] == 1) and ((now["C"] == 0))):
			# We have a clock edge
			self._state = prev["D"]
			sdg.annotate("C", index - 1)
		sdg.append("Q", self._state)
		sdg.append("!Q", not self._state)


class JKFlipflop():
	def __init__(self, initial_state: int = 0, pos_edge: bool = True):
		self._state = initial_state
		self._pos_edge = pos_edge

	def tick(self, sdg, index, prev, now):
		if ((self._pos_edge) and (prev["C"] == 0) and ((now["C"] == 1))) or ((not self._pos_edge) and (prev["C"] == 1) and ((now["C"] == 0))):
			# We have a clock edge
			if (prev["J"] == 0) and (prev["K"] == 0):
				sdg.annotate("C", index - 1)
			elif (prev["J"] == 1) and (prev["K"] == 0):
				self._state = 1
				sdg.annotate("C", index - 1, "S")
			elif (prev["J"] == 0) and (prev["K"] == 1):
				self._state = 0
				sdg.annotate("C", index - 1, "R")
			elif (prev["J"] == 1) and (prev["K"] == 1):
				self._state = 1 - self._state
				sdg.annotate("C", index - 1, "T")

		sdg.append("Q", self._state)
		sdg.append("!Q", not self._state)

class JKMasterSlaveFlipflop():
	def __init__(self, initial_state: int = 0):
		self._master = initial_state
		self._slave = initial_state

	def tick(self, sdg, index, prev, now):
		if (prev["C"] == 0) and (now["C"] == 1):
			# Positive clock edge triggers master
			if (prev["J"] == 1) and (prev["K"] == 0):
				self._master = 1
				sdg.annotate("C", index - 1, "S")
			elif (prev["J"] == 0) and (prev["K"] == 1):
				self._master = 0
				sdg.annotate("C", index - 1, "R")
			elif (prev["J"] == 1) and (prev["K"] == 1):
				self._master = 1 - self._master
				sdg.annotate("C", index - 1, "T")
		elif (prev["C"] == 1) and (now["C"] == 0):
			# Negative clock edge triggers slave
			slave_j = self._master
			if (slave_j == 1):
				# J = 1, K = 0
				self._slave = 1
			else:
				# J = 0, K = 1
				self._slave = 0

		sdg.append("M", self._master)
		sdg.append("Q", self._slave)
		sdg.append("!Q", not self._slave)


class SRFlipflopNAND():
	def __init__(self, initial_state: int = 0):
		self._state = initial_state

	def tick(self, sdg, index, prev, now):
		if (now["S"] == 0) and (now["R"] == 0):
			sdg.append("Q", 1)
			sdg.append("!Q", 1)
			if self._state is not None:
				sdg.annotate("S", index - 1)
			self._state = None
		elif (now["S"] == 0) and (now["R"] == 1):
			if self._state != 1:
				sdg.annotate("S", index - 1, "S")
			self._state = 1
			sdg.append("Q", self._state)
			sdg.append("!Q", not self._state)
		elif (now["S"] == 1) and (now["R"] == 0):
			if self._state != 0:
				sdg.annotate("S", index - 1, "R")
			self._state = 0
			sdg.append("Q", self._state)
			sdg.append("!Q", not self._state)
		else:
			if self._state is None:
				self._state = 0
				sdg.annotate("S", index - 1, "🗲")
			sdg.append("Q", self._state)
			sdg.append("!Q", not self._state)


class ActionDTDCreate(BaseAction):
	_INPUT_SIGNALS = {
		"sr-nand-ff":	("S", "R"),
		"d-ff":			("C", "D"),
		"jk-ff":		("C", "J", "K"),
		"jk-ms-ff":		("C", "J", "K"),
	}

	def _initialize(self):
		self._predetermined = { }
		for param in self._args.param:
			param = param.replace(" ", "")
			(name, value) = param.split("=")
			value = "".join([ x for x in value if x in "01" ])
			self._predetermined[name] = value

	def run(self):
		self._initialize()

		if self._args.random_seed is not None:
			seed = self._args.random_seed
		else:
			seed = str(random.randint(0, 9999999999))
		prng = PRNG(seed.encode("ascii"))

		sdg = SequenceDiagramGenerator()

		match self._args.device:
			case "sr-nand-ff":
				device = SRFlipflopNAND(initial_state = int(self._args.initial_state_high))
				sdg.add_signal_alias("S", "!S")
				sdg.add_signal_alias("R", "!R")

			case "d-ff":
				device = DFlipflop(initial_state = int(self._args.initial_state_high), pos_edge = not self._args.negative_edge_triggered)
				if self._args.negative_edge_triggered:
					sdg.add_signal_alias("C", "!C")

			case "jk-ff":
				device = JKFlipflop(initial_state = int(self._args.initial_state_high), pos_edge = not self._args.negative_edge_triggered)
				if self._args.negative_edge_triggered:
					sdg.add_signal_alias("C", "!C")

			case "jk-ms-ff":
				device = JKMasterSlaveFlipflop(initial_state = int(self._args.initial_state_high))

		for signame in self._INPUT_SIGNALS[self._args.device]:
			if signame in self._predetermined:
				sdg.add_signal(signame, self._predetermined[signame])
			else:
				sdg.add_random_signal(prng, signame, self._args.length)

		print(f"# Random seed: {seed}")
		sdg.simulate(device)
		sdg.print()
