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

import enum
import argparse
import abc

def _parse_bool(bool_value: str | bool) -> bool:
	if isinstance(bool_value, bool):
		return bool_value
	if bool_value.lower() in ("0", "off", "false", "no"):
		return False
	elif bool_value.lower() in ("1", "on", "true", "yes"):
		return True
	else:
		raise ValueError(f"Not a boolean value: {bool_value}")

def _parse_layout(layout_value: str) -> str:
	if layout_value.lower() in ("v", "vert", "vertical"):
		return "vertical"
	elif layout_value.lower() in ("h", "horiz", "horizontal"):
		return "horizontal"
	else:
		raise ValueError(f"Not a layout value: {layout_value} (expect \"vertical\" or \"horizontal\")")

class OptionedEnum():
	Value = None
	OPTIONS = { }

	def __init__(self, enum_value: enum.Enum, option_list: list[str] | None = None):
		self._value = enum_value
		self._options = self._parse_options([ ] if (option_list is None) else option_list)

	@property
	def supported_options(self):
		return self._SUPPORTED_OPTIONS.get(self._value, { })

	def _parse_options(self, option_list: list[str]) -> dict:
		supported_options = self.supported_options
		parsed_options = { }
		for (name, (parser_class, default_value)) in supported_options.items():
			parsed_options[name] = default_value
		for option in option_list:
			if "=" not in option:
				(key, value) = (option, True)
			else:
				(key, value) = option.split("=", maxsplit = 1)
			key = key.lower()

			if len(supported_options) == 0:
				raise argparse.ArgumentTypeError(f"{self.__class__.__name__} {self.name} supports no options, but option \"{key}\" was given.")

			if key not in supported_options:
				raise argparse.ArgumentTypeError(f"Arguments to {self.__class__.__name__} must be one of \"{', '.join(sorted(supported_options))}\", but \"{key}\" is not.")

			(parser_class, default_value) = supported_options[key]
			try:
				value = parser_class(value)
			except ValueError as e:
				raise argparse.ArgumentTypeError(f"Argument {key} to {self.__class__.__name__} must be of type {parser_class.__name__}, but \"{value}\" could not be parsed: {e.__class__.__name__} {str(e)}")
			parsed_options[key] = value
		return parsed_options

	def __getitem__(self, option_name: str):
		if option_name not in self._options:
			raise KeyError(f"{self.__class__.__name__} {self.name} supports {len(self.supported_options)} options: \"{', '.join(sorted(self.supported_options))}\", but option \"{option_name}\" was asked for.")
		return self._options[option_name]

	def __repr__(self):
		return f"{repr(self._value)} <{self._options}>"

class TableFormatOpts(OptionedEnum):
	class Value(enum.StrEnum):
		Text = "text"
		TeX = "tex"
		Typst = "typst"
		Compact = "compact"
		LogiSim = "logisim"

	_OPTIONS = {
		Value.Text: {
			"pretty": (_parse_bool, False),
		},
		Value.TeX: {
			"layout": (_parse_layout, "vertical"),
		},
		Value.Typst: {
			"layout": (_parse_layout, "vertical"),
		},
	}

class ExpressionFormatOpts(OptionedEnum):
	class Value(enum.StrEnum):
		Text = "text"
		TeX = "tex"
		Typst = "typst"
		Dot = "dot"
		Internal = "internal"

	_OPTIONS = {
		Value.Text: {
			"implicit-and": (_parse_bool, True),
			"pretty": (_parse_bool, False),
		},
		Value.TeX: {
			"implicit-and": (_parse_bool, True),
			"math-operators": (_parse_bool, False),
			"use-mathrm": (_parse_bool, True),
		},
		Value.Typst: {
			"implicit-and": (_parse_bool, True),
			"math-operators": (_parse_bool, False),
		},
	}
