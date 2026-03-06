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

import collections

class DAGAnalyzer():
	Tail = collections.namedtuple("Tail", [ "leaf_node", "length", "end_cycle" ])
	Cycle = collections.namedtuple("Cycle", [ "primary_node", "length" ])
	TailPath = collections.namedtuple("TailPath", [ "tail_steps", "end_cycle"])

	def __init__(self, edges: list[tuple[int, int]]):
		self._edges = { src: dst for (src, dst) in edges }
		self._leaf_edges = set(self._edges) - set(self._edges.values())
		self._not_visited = set(self._edges)
		self._found_cycles = { }
		self._found_tails = { }
		self._found_tailpaths = { }
		self._unique_cycles = { }
		for leaf_edge in self._leaf_edges:
			self._start_traversal(leaf_edge)
		# Possibly nodes are still not visited because we have leafless cycles
		while len(self._not_visited) > 0:
			node = self._not_visited.pop()
			self._not_visited.add(node)
			self._start_traversal(node)

	@property
	def tails(self):
		return self._found_tails.values()

	@property
	def cycles(self):
		return self._unique_cycles.values()

	@property
	def shortest_cycle_length(self):
		return min(cycle.length for cycle in self.cycles)

	def walk(self, node: int, step_count: int):
		path = [ ]
		for _ in range(step_count):
			path.append(node)
			node = self._edges[node]
		return path

	@property
	def all_nodes(self):
		all_nodes = dict(self._found_cycles)
		all_nodes.update(self._found_tails)
		all_nodes.update(self._found_tailpaths)
		assert(len(all_nodes) == len(set(self._edges)))
		return all_nodes

	def dump(self):
		all_nodes = self.all_nodes
		for node in sorted(self._edges):
			print(f"{node:>3d} {all_nodes[node]}")

	def _start_traversal(self, leaf_node: int):
		path = [ ]
		node = leaf_node
		while node in self._not_visited:
			path.append(node)
			self._not_visited.remove(node)
			node = self._edges[node]

		if node in self._found_tailpaths:
			tailpath = self._found_tailpaths[node]
			tail = self.Tail(leaf_node = leaf_node, length = len(path) + tailpath.tail_steps, end_cycle = tailpath.end_cycle)
			for (stepno, node) in enumerate(path[1:], 1):
				tailpath = self.TailPath(tail_steps = tail.length - stepno, end_cycle = tailpath.end_cycle)
				self._found_tailpaths[node] = tailpath
			self._found_tails[leaf_node] = tail
		else:
			if node in self._found_cycles:
				# We found a completely new tail and stepped directly onto a
				# known cycle
				cycle = self._found_cycles[node]
				tail_length = len(path)
				tail_path = path
			else:
				# New cycle discovered
				tail_length = path.index(node)
				cycle_length = len(path) - tail_length
				tail_path = path[:tail_length]
				cycle_path = path[tail_length:]
				cycle_primary_node = min(cycle_path)
				cycle = self.Cycle(primary_node = cycle_primary_node, length = cycle_length)
				self._unique_cycles[cycle.primary_node] = cycle
				for node in cycle_path:
					self._found_cycles[node] = cycle

			if tail_length > 0:
				tail = self.Tail(leaf_node = leaf_node, length = tail_length, end_cycle = cycle)
				for (stepno, node) in enumerate(tail_path[1:], 1):
					tailpath = self.TailPath(tail_steps = tail.length - stepno, end_cycle = cycle)
					self._found_tailpaths[node] = tailpath
				self._found_tails[leaf_node] = tail

	def print_graphviz(self, format_bits):
		print("digraph g {")
		print("	layout=neato;")
		print("	overlap=false;")
		print("	splines=true;")
		print("	node [ shape=circle, style=filled ];")
		for (node_id, node) in self.all_nodes.items():
			bin_no = f"{node_id:0{format_bits}b}"
			fillcolor = {
				self.Cycle: "#fff3b0",
				self.Tail: "#b9d7ff",
				self.TailPath: "#d9c2ff",
			}[type(node)]
			print(f"	n{node_id} [ label=\"{node_id}\\n{bin_no}\", fillcolor=\"{fillcolor}\" ];")
		for (src_id, dst_id) in self._edges.items():
			print(f"	n{src_id} -> n{dst_id};")
		print("}")
