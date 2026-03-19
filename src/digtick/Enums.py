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

class TableFormat(enum.StrEnum):
	Text = "text"
	Pretty = "pretty"
	TeXHorizontal = "tex-horizontal"
	TeXVertical = "tex-vertical"
	TypstHorizontal = "typst-horizontal"
	TypstVertical = "typst-vertical"
	Compact = "compact"
	LogiSim = "logisim"

	__SUPPORTED_OPTIONS = {
		Text: {
			"foo": str,
			"val": int,
		},
	}

	def options(self, option_list: list[str]) -> dict:
		permissible_options = self.__SUPPORTED_OPTIONS.get(self.value, { })
		options = { }
		for option in option_list:
			if "=" not in option:
				raise argparse.ArgumentTypeError(f"Arguments to {self.__class__.__name__} must be of form \"key=value\", but \"{option}\" is not.")
			(key, value) = option.split("=", maxsplit = 1)
			key = key.lower()

			if len(permissible_options) == 0:
				raise argparse.ArgumentTypeError(f"{self.__class__.__name__} has no options, but option \"{key}\" was given.")

			if key not in permissible_options:
				raise argparse.ArgumentTypeError(f"Arguments to {self.__class__.__name__} must be one of \"{', '.join(sorted(permissible_options))}\", but \"{key}\" is not.")

			try:
				value = permissible_options[key](value)
			except ValueError as e:
				raise argparse.ArgumentTypeError(f"Argument {key} to {self.__class__.__name__} must be of type {permissible_options[key].__name__}, but \"{value}\" produced error: {e.__class__.__name__} {str(e)}")

			options[key] = value
		return options

	def __str__(self):
		return self.value

#x = TableFormat.Text
#print(x.options([ "foo=bar", "val=9x" ]))
