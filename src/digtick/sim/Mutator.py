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

import random
from digtick.Exceptions import UnsupportedMutationOperation

class ComponentMutator():
	def __init__(self, lsl: "LogisimLoader", component_label: str, mutation_selector: str | None = None):
		self._lsl = lsl
		self._component_label = component_label
		self._mutation_selector = mutation_selector
		if self._mutation_selector is None:
			self._mutation_selector = ""
		if self.component_dict["name"] not in [ "#Gates.AND Gate", "#Gates.OR Gate", "#Gates.NAND Gate", "#Gates.NOR Gate", "#Gates.XOR Gate", "#Gates.XNOR Gate" ]:
			raise UnsupportedMutationOperation(f"Component {component_label} is not a gate and cannot be mutated: type {self.component_dict['name']}")
		self._combination_count = None
		self._combination_product = None
		self._parse_selector(self._mutation_selector)

	@property
	def component_label(self):
		return self._component_label

	@property
	def combination_count(self):
		return self._combination_count

	@property
	def component_dict(self):
		return self._lsl.get_component(self._component_label)["component_dict"]

	@property
	def resolved_component(self):
		return self._lsl.get_component(self._component_label)["resolved_component"]

	def _parse_selector(self, mutation_selector: str):
		component_alternatives = None
		inverted_pins = None
		chosen_combinations = None
		random_combination_count = 0

		if len(mutation_selector.strip()) > 0:
			for selector_part in [ part.strip() for part in mutation_selector.split(",") ]:
				if "=" not in selector_part:
					raise UnsupportedMutationOperation(f"Invalid mutation selector {mutation_selector} presented: part \"{selector_part}\" does not contain equals sign.")
				(key, value) = selector_part.split("=", maxsplit = 1)
				match key:
					case "c":
						# Component
						if component_alternatives is None:
							component_alternatives = set()
						component_alternatives.add(value)

					case "inv":
						# Inversions of pins
						if not value.isdigit():
							raise UnsupportedMutationOperation(f"Invalid mutation selector {mutation_selector} presented: part \"{selector_part}\" requires a integer value on the righthand side.")
						value = int(value)
						if inverted_pins is None:
							inverted_pins = set()
						if value > 0:
							inverted_pins.add(value)

					case "comb":
						if not value.isdigit():
							raise UnsupportedMutationOperation(f"Invalid mutation selector {mutation_selector} presented: part \"{selector_part}\" requires a integer value on the righthand side.")
						value = int(value)
						if chosen_combinations is None:
							chosen_combinations = set()
						chosen_combinations.add(value)

					case "randcomb":
						if not value.isdigit():
							raise UnsupportedMutationOperation(f"Invalid mutation selector {mutation_selector} presented: part \"{selector_part}\" requires a integer value on the righthand side.")
						random_combination_count += int(value)

					case _:
						raise UnsupportedMutationOperation(f"Invalid mutation selector {mutation_selector} presented: part \"{selector_part}\" shows unknown key \"{key}\".")


		if component_alternatives is None:
			component_alternatives = set([ "AND", "OR", "NAND", "NOR", "XOR", "XNOR" ])
		if inverted_pins is None:
			inverted_pins = set(pinindex + 1 for pinindex in range(self.resolved_component["input_count"]))

		self._combination_count = len(component_alternatives) * (2 ** len(inverted_pins))
		if chosen_combinations is not None:
			self._chosen_combinations = chosen_combinations
		elif random_combination_count == 0:
			self._chosen_combinations = set(range(self._combination_count))
		else:
			self._chosen_combinations = set()

		if random_combination_count > 0:
			randomized_combinations = list(range(self._combination_count))
			random.shuffle(randomized_combinations)
			self._chosen_combinations |= set(randomized_combinations[:random_combination_count])

		self._combination_product = [ ]
		self._combination_product.append(("alternative", list(sorted(component_alternatives))))
		for pin_no in sorted(inverted_pins):
			self._combination_product.append((f"negate{pin_no - 1}", (False, True)))

	def get_mutation(self, index: int):
		if index >= self.combination_count:
			raise IndexError("Index {index} unavailable, only have {self.combination_count} combinations.")
		mutation_dict = { }
		for (name, entries) in self._combination_product:
			subindex = index % len(entries)
			index = index // len(entries)
			mutation_dict[name] = entries[subindex]
		return mutation_dict

	def __iter__(self):
		for index in self._chosen_combinations:
			yield self.get_mutation(index)
