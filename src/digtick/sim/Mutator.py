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

import itertools
from digtick.Exceptions import UnsupportedMutationOperation
from .Components import CmpGate

class ComponentMutator():
	def __init__(self, lsl: "LogisimLoader", component_label: str, mutation_selector: str):
		self._lsl = lsl
		self._component_label = component_label
		self._mutation_selector = mutation_selector
		if self.component_dict["name"] not in [ "#Gates.AND Gate", "#Gates.OR Gate", "#Gates.NAND Gate", "#Gates.NOR Gate", "#Gates.XOR Gate", "#Gates.XNOR Gate" ]:
			raise UnsupportedMutationOperation(f"Component {component_label} is not a gate and cannot be mutated: type {self.component_dict['name']}")

		# TODO parse component mutator
#		self._alternative_components = [ "AND", "OR", "NAND", "NOR", "XOR", "XNOR" ]
		self._alternative_components = [ "XOR" ]
		self._inversion_combinations = list(range(2 ** self.resolved_component["input_count"]))

	@property
	def component_label(self):
		return self._component_label

	@property
	def component_dict(self):
		return self._lsl.get_component(self._component_label)["component_dict"]

	@property
	def resolved_component(self):
		return self._lsl.get_component(self._component_label)["resolved_component"]

	@staticmethod
	def _int2bitlist(intval):
		for bitno in range(intval.bit_length()):
			if (intval >> bitno) & 1:
				yield bitno

	def __iter__(self):
		for (alternative_component, inversion_combination) in itertools.product(self._alternative_components, self._inversion_combinations):
			mutation = {
				"alternative": alternative_component,
				"invert": list(self._int2bitlist(inversion_combination)),
			}
			yield mutation
