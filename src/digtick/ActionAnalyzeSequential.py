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

import json
from .MultiCommand import BaseAction
from .ValueTable import ValueTable
from .Tools import open_file
from .Exceptions import OutputValueMissingException
from .GraphAnalysis import DAGAnalyzer

class ActionAnalyzeSequential(BaseAction):
	def run(self):
		with open_file(self._args.filename) as f:
			self._vt = ValueTable.parse_from_file(f, set_undefined_values_to = "forbidden")

		for varname in self._vt.input_variable_names:
			if not self._vt.has_output_named(varname + "'"):
				raise OutputValueMissingException(f"Every input needs a nextstate input (the label plus an apostrophe). Found input {varname} but no output {varname}'")
		self._output_vars = [ varname + "'" for varname in self._vt.input_variable_names ]

		# Cannot simply iterate as outputs may be out-of-order
		graph_edges = [ ]
		hdist_sum = 0
		hdist_min = None
		state_count = 2 ** len(self._vt.input_variable_names)
		for input_value in range(state_count):
			output_values = [ self._vt.at_index(input_value, varname) for varname in self._output_vars ]
			output_value = sum(bitvalue << bitno for (bitno, bitvalue) in enumerate(reversed(output_values)))
			graph_edges.append((input_value, output_value))
			hdist = (input_value ^ output_value).bit_count()
			if (hdist_min is None) or (hdist < hdist_min):
				hdist_min = hdist
			hdist_sum += hdist

		analyzer = DAGAnalyzer(graph_edges)
		if self._args.verbose >= 2:
			analyzer.dump()
		if self._args.output_format == "text":
			print(f"State transitions: {', '.join(self._vt.input_variable_names)} → {', '.join(self._output_vars)}")
			for cycle in analyzer.cycles:
				path = analyzer.walk(cycle.primary_node, step_count = cycle.length + 1)
				print(f"   Cycle ID={cycle.primary_node} length {cycle.length}: {' → '.join(str(node) for node in path)}")
			for tail in analyzer.tails:
				path = analyzer.walk(tail.leaf_node, step_count = tail.length + 1)
				print(f"   Tail length {tail.length}: {' → '.join(str(node) for node in path[:-1])} → [ {path[-1]} of cycle ID={tail.end_cycle.primary_node} length {tail.end_cycle.length} ]")
			print(f"State graph has {len(analyzer.cycles)} cycles and {len(analyzer.tails)} tails. Shortest cycle length: {analyzer.shortest_cycle_length}")
			print(f"Average Hamming distance between states: {hdist_sum / state_count:.1f} bits, minimum Hamming ditance: {hdist_min} bit")
		elif self._args.output_format == "dot":
			analyzer.print_graphviz(format_bits = len(self._vt.input_variable_names))
		elif self._args.output_format == "json":
			json_data = {
				"source": self._args.filename,
				"input_vars": self._vt.input_variable_names,
				"output_vars": self._output_vars,
				"cycles": [ cycle._asdict() for cycle in analyzer.cycles ],
				"tail_count": len(analyzer.tails),
				"shortest_cycle_length": analyzer.shortest_cycle_length,
				"hamming_distance": {
					"avg": hdist_sum / state_count,
					"min": hdist_min,
				},
			}
			print(json.dumps(json_data))
		else: # pragma unreachable
			raise NotImplementedError(self._args.output_format)
