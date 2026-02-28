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

import collections
import itertools
import dataclasses
from .ExpressionParser import BinaryOperator, Operator, Variable, Constant
from .ValueTable import CompactStorage
from .TableFormatter import Table

class QuineMcCluskey():
	@dataclasses.dataclass(frozen = True, slots = True, order = True)
	class Implicant():
		minterms: frozenset[int]
		value: int
		mask: int

		def binformat(self, bit_count: int):
			bitstr = [ ]
			for bit in reversed(range(bit_count)):
				if (self.mask >> bit) & 1:
					bitstr.append("-")
				elif (self.value >> bit) & 1:
					bitstr.append("1")
				else:
					bitstr.append("0")
			return "".join(bitstr)

		def as_mterm(self, variables: list[Variable], minterm: bool):
			literals = [ ]
			for (index, variable) in enumerate(variables):
				bit = len(variables) - 1 - index
				if ((self.mask >> bit) & 1) == 0:
					# We DO care
					inverted = (((self.value >> bit) & 1) != 0) ^ minterm
					literals.append(~variable if inverted else variable)
			return BinaryOperator.join(Operator.And if minterm else Operator.Or, literals)

		def __repr__(self):
			return f"size-{len(self.minterms)} implicant {{{','.join(str(minterm) for minterm in sorted(self.minterms))}}}"

	def __init__(self, value_table: "ValueTable", variable_name: str, verbosity = 0):
		self._vt = value_table
		self._varname = variable_name
		self._verbose = verbosity

	def _minterm2int(self, minterm):
		result = 0
		for (no, var_name) in enumerate(reversed(self._vt.input_variable_names)):
			if minterm[var_name]:
				result |= 1 << no
		return result

	def _group_by_bitcount(self, values):
		result = collections.defaultdict(list)
		for value in values:
			result[value.bit_count()].append(value)
		return result

	def _create_size_one_implicants(self, grouped_minterms):
		return { bit_count: { 0: [ self.Implicant(minterms = frozenset([ minterm ]), value = minterm, mask = 0) for minterm in minterms ] } for (bit_count, minterms) in grouped_minterms.items() }

	def _merge_implicants(self, grouped_implicants):
		result = collections.defaultdict(lambda: collections.defaultdict(list))

		highest_bit_count = max(grouped_implicants.keys())
		for (bit_count, implicants_1_by_mask) in grouped_implicants.items():
			if bit_count == highest_bit_count:
				continue
			if (bit_count + 1) not in grouped_implicants:
				continue

			implicants_2_by_mask = grouped_implicants[bit_count + 1]

			found_merged = set()
			for (mask_bits, implicants_1) in implicants_1_by_mask.items():
				implicants_2 = implicants_2_by_mask.get(mask_bits, [ ])

				for (implicant1, implicant2) in itertools.product(implicants_1, implicants_2):
					mask = implicant1.value ^ implicant2.value
					if mask.bit_count() == 1:
						merged_minterms = implicant1.minterms | implicant2.minterms
						merged_minterm_tuple = tuple(sorted(merged_minterms))
						if merged_minterm_tuple not in found_merged:
							found_merged.add(merged_minterm_tuple)
							merged_implicant = self.Implicant(minterms = merged_minterms, value = implicant1.value & ~mask, mask = implicant1.mask | mask)
							#print("Merging", implicant1, implicant2, merged_implicant)
							result[bit_count][implicant1.mask | mask].append(merged_implicant)
		return result


	def _create_merged_implicant_groups(self, prime_implicants):
		all_implicants = {
			1: prime_implicants,
		}
		for index in range(len(self._vt.input_variable_names)):
			prev_implicants = all_implicants[index + 1]
			merged_implicants = self._merge_implicants(prev_implicants)
			if len(merged_implicants) == 0:
				break
			if self._verbose >= 2:
				self._dump_implicants(f"Size {1 << (index + 1)} implicants", merged_implicants)
			all_implicants[index + 2] = merged_implicants
		return all_implicants

	def _discard_mask_information(self, all_implicants):
		result = { }
		for (group, implicants_by_group) in all_implicants.items():
			result[group] = [ ]
			for implicants_by_bitcount in implicants_by_group.values():
				for implicants in implicants_by_bitcount.values():
					result[group] += implicants
		return result

	def _eliminate_suboptimal_implicants(self, all_implicants):
		result = { }
		top_group = max(all_implicants.keys())
		for lower_group_id in range(1, top_group):
			upper_group_id = lower_group_id + 1

			eliminated_lower_group = [ ]
			for lower_implicant in all_implicants[lower_group_id]:
				for upper_implicant in all_implicants[upper_group_id]:
					if (lower_implicant.minterms & upper_implicant.minterms) == lower_implicant.minterms:
						# Lower implicant is full subgroup of upper, eliminate.
						break
				else:
					# Nowhere in the upper group, it's required.
					eliminated_lower_group.append(lower_implicant)

			if len(eliminated_lower_group) > 0:
				result[lower_group_id] = eliminated_lower_group
		result[top_group] = all_implicants[top_group]
		return result

	def _determine_required_minterms(self, all_implicants: dict[int, list[Implicant]], mandatory_minterms: set[int]):
		ctr = collections.Counter()
		for (group, implicants) in all_implicants.items():
			for implicant in implicants:
				ctr.update(implicant.minterms & mandatory_minterms)
		return { minterm for (minterm, count) in ctr.items() if count == 1 }

	def _eliminate_required_implicants(self, all_implicants, required_minterms):
		result = { }
		required_implicants = [ ]
		for (group, implicants) in all_implicants.items():
			eliminated_implicants = [ ]
			for implicant in implicants:
				if len(required_minterms & implicant.minterms) > 0:
					required_implicants.append(implicant)
				else:
					eliminated_implicants.append(implicant)
			if len(eliminated_implicants) > 0:
				result[group] = eliminated_implicants
		return (required_implicants, result)

	def _compute_remaining_minterms(self, expr_minterms, required_implicants):
		remaining_minterms = set(expr_minterms)
		for implicant in required_implicants:
			remaining_minterms = remaining_minterms - implicant.minterms
		return remaining_minterms

	def _group_implicants_by_minterm(self, all_implicants):
		result = collections.defaultdict(list)
		for implicants in all_implicants.values():
			for implicant in implicants:
				for minterm in implicant.minterms:
					result[minterm].append(implicant)
		return result

	def _print_prime_implicant_chart(self, remaining_minterms: set[int], implicants_fulfilling_minterm: dict[int, list[Implicant]]):
		# Reverse dictionary
		minterm_covered_by_implicant = collections.defaultdict(list)
		for (minterm, fulfilling_implicants) in implicants_fulfilling_minterm.items():
			for fulfilling_implicant in fulfilling_implicants:
				minterm_covered_by_implicant[fulfilling_implicant].append(minterm)

		table = Table()
		heading = { str(minterm): str(minterm) for minterm in remaining_minterms }
		heading.update({ "_": "Prime implicant chart" })
		table.add_row(heading)
		table.add_separator_row()

		for (implicant, covered_minterms) in sorted(minterm_covered_by_implicant.items()):
			row = { "_": str(implicant) }
			for minterm in covered_minterms:
				row[str(minterm)] = "*"
			table.add_row(row)
		table.print(*([ "_" ] + list(str(minterm) for minterm in sorted(remaining_minterms))))

	def _absorb(self, terms: set[int]) -> set[int]:
		# Remove all values that are completely covered by other values in
		# terms of their bits. This is current O(n²) but I'm quite certain we
		# could use a divide-and-conquery approach. Let's check first if this
		# works
		unique = set()
		while len(terms) > 0:
			term = terms.pop()
			for other in terms:
				if (term & other) == term:
					break
			else:
				unique.add(term)
		return unique

	def _filter_min_bit_count(self, terms: set[int]) -> set[int]:
		result = None
		min_bit_count = None
		for value in terms:
			if (result is None) or (value.bit_count() < min_bit_count):
				min_bit_count = value.bit_count()
				result = set([ value ])
			elif value.bit_count() == min_bit_count:
				result.add(value)
		return result

	def _find_minimal_expression_petricks_method(self, remaining_minterms: set[int], implicants_fulfilling_minterm: dict[int, list[Implicant]]):
		# Assign each candidate implicant a bit
		candidate_implicants = { }
		for minterm in remaining_minterms:
			for implicant in implicants_fulfilling_minterm[minterm]:
				if implicant not in candidate_implicants:
					candidate_implicants[implicant] = 1 << len(candidate_implicants)
		inverse = { bitvalue: implicant for (implicant, bitvalue) in candidate_implicants.items() }

		possible_solutions = None
		for minterm in remaining_minterms:
			next_minterm_implicants = set(candidate_implicants[implicant] for implicant in implicants_fulfilling_minterm[minterm])
			if possible_solutions is None:
				# First term
				possible_solutions = next_minterm_implicants
			else:
				# Next term, multiply/absorb
				possible_solutions = set(a | b for (a, b) in itertools.product(possible_solutions, next_minterm_implicants))
				possible_solutions = self._filter_min_bit_count(possible_solutions)		# TODO: greedy matching. Is this correct?
				possible_solutions = self._absorb(possible_solutions)


		remaining_solutions = self._filter_min_bit_count(possible_solutions)
		# We now have a list of solutions that all are correct. Choose one that
		# has the fewest amount of literals (not all implicants have the same!).

		final_solution = remaining_solutions.pop()		# TODO: implement me
		impl = [ ]
		for bit in range(final_solution.bit_length()):
			impl.append(inverse[1 << bit])
		return impl


#	def _format_implicant(self, implicant: Implicant, cnf: bool = False):
#		terms = [ ]
#		for (no, var_name) in enumerate(reversed(self._vt.input_variable_names)):
#			if ((1 << no) & implicant.mask) == 0:
#				inverted = ((1 << no) & implicant.value) == 0
#				terms.append(f"{'-' if (inverted ^ cnf) else ''}{var_name}")
#		if cnf:
#			if len(terms) == 0:
#				return "0"
#			return "+".join(reversed(terms))
#		else:
#			if len(terms) == 0:
#				return "1"
#			return " ".join(reversed(terms))

	def _dump_implicants(self, text: set, implicants_by_hamming_weight: dict[int, dict[int, Implicant]]):
		print(f"{text}:")
		for (hamming_weight, implicants) in sorted(implicants_by_hamming_weight.items()):
			for (order, implicants) in sorted(implicants.items()):
				for implicant in implicants:
					print(f"   HammWeight={hamming_weight:<3d} {implicant.binformat(self._vt.input_variable_count)} {implicant}")
		print()

	def _dump_merged_implicants(self, text: set, implicants_by_order: dict[int, Implicant]):
		print(f"{text}:")
		for (order, implicants) in sorted(implicants_by_order.items()):
			for implicant in implicants:
				print(f"   {implicant.binformat(self._vt.input_variable_count)} {implicant}")
		print()

	def optimize(self, emit_dnf: bool = True):
		# When we emit CNF, we add minterms for the inverse function and emit a
		# differnet equation in the end.

		expr_minterms = set()
		dc_minterms = set()
		for (index, output) in enumerate(self._vt.iter_output_variable(self._varname)):
			if output == CompactStorage.Entry.DontCare:
				dc_minterms.add(index)
			elif (emit_dnf and (output == CompactStorage.Entry.High)) or (not emit_dnf and (output == CompactStorage.Entry.Low)):
				expr_minterms.add(index)

		minterms = expr_minterms | dc_minterms
		grouped_minterms = self._group_by_bitcount(minterms)
		size_one_implicants = self._create_size_one_implicants(grouped_minterms)
		if len(size_one_implicants) == 0:
			# Constant zero function
			return Constant(0) if emit_dnf else Constant(1)

		if self._verbose >= 2:
			self._dump_implicants("Initial size-1 implicants", size_one_implicants)
		all_implicants = self._create_merged_implicant_groups(size_one_implicants)
		all_implicants = self._discard_mask_information(all_implicants)
		all_implicants = self._eliminate_suboptimal_implicants(all_implicants)

		if self._verbose >= 2:
			self._dump_merged_implicants("Remaining implicants after merging/redundant removal", all_implicants)

		required_minterms = self._determine_required_minterms(all_implicants, mandatory_minterms = expr_minterms)
		if self._verbose >= 2:
			print(f"Essential minterms (only provided by a single implicant that needs to be contained): {sorted(list(required_minterms))}")
			print()

		(required_implicants, all_implicants) = self._eliminate_required_implicants(all_implicants, required_minterms)
		if self._verbose >= 2:
			print(f"Essential implicants: {required_implicants}")
			print()
			self._dump_merged_implicants("Remaining implicants after removal of essential implicants", all_implicants)

		remaining_minterms = self._compute_remaining_minterms(expr_minterms, required_implicants)
		if self._verbose >= 2:
			print(f"{len(remaining_minterms)} remaining minterms which need to be selected by prime implicant chart: {sorted(list(remaining_minterms))}")

		grouped_implicants = self._group_implicants_by_minterm(all_implicants)
		if self._verbose >= 2:
			self._print_prime_implicant_chart(remaining_minterms, grouped_implicants)
		optimal_solution = self._find_minimal_expression_petricks_method(remaining_minterms, grouped_implicants)

		solution_implicants = set(required_implicants) | set(optimal_solution)

		variables = [ Variable(varname) for varname in self._vt.input_variable_names ]
		if emit_dnf:
			return BinaryOperator.join(Operator.Or, (implicant.as_mterm(variables, minterm = True) for implicant in sorted(solution_implicants)))
		else:
			return BinaryOperator.join(Operator.And, (implicant.as_mterm(variables, minterm = False) for implicant in sorted(solution_implicants)))
