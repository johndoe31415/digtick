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

import os
from digtick.sim.LogisimInterface import LogisimLoader
from digtick.sim.Mutator import ComponentMutator
from .MultiCommand import BaseAction

class ActionMutateCircuit(BaseAction):
	def run(self):
		os.makedirs(self._args.output_directory, exist_ok = True)

		lsl = LogisimLoader.load_from_file(self._args.circ_filename, circuit_name = self._args.circuit_name)
		lsl.parse()

		mutators = [ ]
		for mutator in self._args.mutator:
			if ":" in mutator:
				(label, mutation_selector) = mutator.split(":", maxsplit = 1)
			else:
				(label, mutation_selector) = (mutator, None)
			mutator = ComponentMutator(lsl = lsl, component_label = label, mutation_selector = mutation_selector)
			mutators.append(mutator)

		# Shortcut notation
		if self._args.randomize_component is not None:
			for label in self._args.randomize_component.split(","):
				mutator = ComponentMutator(lsl = lsl, component_label = label, mutation_selector = "randcomb=1")
				mutators.append(mutator)

		if len(mutators) == 0:
			raise ValueError("At least one mutator needs to be specified.")

		if self._args.prefix is None:
			(prefix, ext) = os.path.splitext(os.path.basename(self._args.circ_filename))
		else:
			prefix = self._args.prefix
		for (variant_number, applied_mutators) in enumerate(lsl.apply_mutators(mutators), 1):
			filename = f"{self._args.output_directory}/{prefix}-{variant_number:03d}.circ"
			lsl.write_to_file(filename)
