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

class OptionEnum(enum.StrEnum):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._options = { }

	@classmethod
	@abc.abstractmethod
	def _supported_options(cls):
		pass

	def parse_options(self, option_list: list[str]) -> dict:
		permissible_options = self._supported_options().get(self.value, { })
		self._options = { }
		for (name, (parser_class, default_value)) in permissible_options.items():
			self._options[name] = default_value
		for option in option_list:
			if "=" not in option:
				(key, value) = (option, True)
			else:
				(key, value) = option.split("=", maxsplit = 1)
			key = key.lower()

			if len(permissible_options) == 0:
				raise argparse.ArgumentTypeError(f"{self.__class__.__name__} {self.name} supports no options, but option \"{key}\" was given.")

			if key not in permissible_options:
				raise argparse.ArgumentTypeError(f"Arguments to {self.__class__.__name__} must be one of \"{', '.join(sorted(permissible_options))}\", but \"{key}\" is not.")

			(parser_class, default_value) = permissible_options[key]
			try:
				value = parser_class(value)
			except ValueError as e:
				raise argparse.ArgumentTypeError(f"Argument {key} to {self.__class__.__name__} must be of type {parser_class.__name__}, but \"{value}\" could not be parsed: {e.__class__.__name__} {str(e)}")
			self._options[key] = value
		return self

	def __getitem__(self, option_name: str):
		return self._options[option_name]

	def __str__(self):
		return self.value

class TableFormat(OptionEnum):
	Text = "text"
	TeX = "tex"
	Typst = "typst"
	Compact = "compact"
	LogiSim = "logisim"

	@classmethod
	def _supported_options(cls):
		return {
			cls.Text: {
				"pretty": (_parse_bool, False),
			},
			cls.TeX: {
				"layout": (_parse_layout, "vertical"),
			},
			cls.Typst: {
				"layout": (_parse_layout, "vertical"),
			},
		}
