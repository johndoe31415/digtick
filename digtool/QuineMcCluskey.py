#	digtool - Tool to compute and simplify problems in digital systems
#	Copyright (C) 2022-2026 Johannes Bauer
#
#	This file is part of digtool.
#
#	digtool is free software; you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation; this program is ONLY licensed under
#	version 3 of the License, later versions are explicitly excluded.
#
#	digtool is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with digtool; if not, write to the Free Software
#	Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#	Johannes Bauer <JohannesBauer@gmx.de>

import collections
import itertools
from .ExpressionParser import parse_expression

class QuineMcCluskey():
	Implicant = collections.namedtuple("Implicant", [ "minterms", "value", "mask" ])

	def __init__(self, value_table: "ValueTable", verbosity = 0):
		self._vt = value_table
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

	def _create_prime_implicants(self, grouped_minterms):
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

	def _determine_required_minterms(self, all_implicants):
		ctr = collections.Counter()
		for (group, implicants) in all_implicants.items():
			for implicant in implicants:
				ctr.update(implicant.minterms)

		required = set()
		for (minterm, count) in ctr.items():
			if count == 1:
				required.add(minterm)
		return required

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

	def _enumerate_fulfilling_implicants(self, remaining_minterms, grouped_implicants, included = None):
		if included is None:
			included = set()
		if len(remaining_minterms) == 0:
			yield included
			return

		# We're not done yet.
		analyzed = set()
		for remaining_minterm in remaining_minterms:
			for candidate_implicant in grouped_implicants[remaining_minterm]:
				if candidate_implicant in analyzed:
					# We've already covered this path.
					continue
				if candidate_implicant in included:
					# It's already considered
					continue
				analyzed.add(candidate_implicant)

				remaining_path = remaining_minterms - candidate_implicant.minterms
				included_path = set(included)
				included_path.add(candidate_implicant)
				yield from self._enumerate_fulfilling_implicants(remaining_path, grouped_implicants, included_path)

	def _find_minimal_expression(self, remaining_minterms, grouped_implicants):
		min_length = None
		optimal_solution = None
		for implicants in self._enumerate_fulfilling_implicants(remaining_minterms, grouped_implicants):
			if (min_length is None) or (len(implicants) < min_length):
				min_length = len(implicants)
				optimal_solution = implicants
		return optimal_solution

	def _format_implicant(self, implicant: Implicant, cnf: bool = False):
		terms = [ ]
		for (no, var_name) in enumerate(reversed(self._vt.input_variable_names)):
			if ((1 << no) & implicant.mask) == 0:
				inverted = ((1 << no) & implicant.value) == 0
				terms.append(f"{'-' if (inverted ^ cnf) else ''}{var_name}")
		if cnf:
			if len(terms) == 0:
				return "0"
			return "+".join(reversed(terms))
		else:
			if len(terms) == 0:
				return "1"
			return " ".join(reversed(terms))

	def _dump_implicants(self, text, implicants):
		print(f"{text}:")
		for (bit_count, implicants_by_mask) in sorted(implicants.items()):
			for (mask, implicants) in sorted(implicants_by_mask.items()):
				for implicant in implicants:
					print(f"   [{implicant.mask:04x}] {bit_count:3d} {implicant.minterms}")
		print()

	def _dump_eliminated_implicants(self, all_implicants, text):
		for (group, implicants) in sorted(all_implicants.items()):
			if group == 1:
				print(f"Eliminiated prime implicants {text}:")
			else:
				print(f"Eliminiated size {1 << (group - 1)} implicants {text}:")
			for implicant in implicants:
				print(f"    {implicant.minterms}")
			print()

	def optimize(self, emit_dnf: bool = True):
		# When we emit CNF, we add minterms for the inverse function and emit a
		# differnet equation in the end.

		expr_minterms = set()
		dc_minterms = set()
		for (input_values, output) in self._vt:
			index = self._vt.input_dict_to_index(input_values, self._vt.input_variable_names)
			if output is None:
				dc_minterms.add(index)
			elif (emit_dnf and (output == 1)) or (not emit_dnf and (output == 0)):
				expr_minterms.add(index)

		minterms = expr_minterms | dc_minterms
		grouped_minterms = self._group_by_bitcount(minterms)
		prime_implicants = self._create_prime_implicants(grouped_minterms)
		if len(prime_implicants) == 0:
			# Constant zero function
			return parse_expression("0" if emit_dnf else "1")

		if self._verbose >= 2:
			self._dump_implicants("Prime implicants", prime_implicants)
		all_implicants = self._create_merged_implicant_groups(prime_implicants)
		all_implicants = self._discard_mask_information(all_implicants)
		all_implicants = self._eliminate_suboptimal_implicants(all_implicants)

		if self._verbose >= 2:
			self._dump_eliminated_implicants(all_implicants, "after removal of redundant implicants")

		required_minterms = self._determine_required_minterms(all_implicants)
		if self._verbose >= 2:
			print(f"Essential minterms (only provided by a single implicant): {sorted(list(required_minterms))}")
			print()

		(required_implicants, all_implicants) = self._eliminate_required_implicants(all_implicants, required_minterms)
		if self._verbose >= 2:
			print(f"Required implicants: {required_implicants}")
			self._dump_eliminated_implicants(all_implicants, "after removal of required implicants")

		remaining_minterms = self._compute_remaining_minterms(expr_minterms, required_implicants)
		if self._verbose >= 2:
			print(f"Remaining minterms: {sorted(list(remaining_minterms))}")

		grouped_implicants = self._group_implicants_by_minterm(all_implicants)
		optimal_solution = self._find_minimal_expression(remaining_minterms, grouped_implicants)

		solution_implicants = set(required_implicants) | set(optimal_solution)

		if emit_dnf:
			return parse_expression("+".join(self._format_implicant(implicant) for implicant in sorted(solution_implicants)))
		else:
			return parse_expression("".join(f"({self._format_implicant(implicant, cnf = True)})" for implicant in sorted(solution_implicants)))
