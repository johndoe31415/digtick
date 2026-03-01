#	digtick - Digital logic design toolkit: simplify, minimize and transform Boolean expressions, draw KV-maps, etc.
#	Copyright (C) 2015-2026 Johannes Bauer
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
import functools
import collections
import dataclasses
from pysvgedit import SVGDocument, SVGGroup, SVGPath, SVGText, Vector2D
from .TextWidthEstimator import TextWidthEstimator

class DigitalTimingType(enum.Enum):
	Low = "0"
	High = "1"
	LowHigh = ":"
	LowHighTransition = "!"
	HighZ = "Z"
	Marker = "|"
	Empty = " "

@dataclasses.dataclass
class DigitalTimingCmd():
	cmdtype: DigitalTimingType
	argument: "typing.Any" = None

	@classmethod
	def parse_sequence(cls, text):
		sequence = [ ]
		index = 0
		while index < len(text):
			char = text[index]
			index += 1
			match char:
				case "0":
					cmd = DigitalTimingCmd(cmdtype = DigitalTimingType.Low)
				case "1":
					cmd = DigitalTimingCmd(cmdtype = DigitalTimingType.High)
				case ":":
					cmd = DigitalTimingCmd(cmdtype = DigitalTimingType.LowHigh)
				case "!":
					cmd = DigitalTimingCmd(cmdtype = DigitalTimingType.LowHighTransition)
				case "Z":
					cmd = DigitalTimingCmd(cmdtype = DigitalTimingType.HighZ)
				case "|":
					marker_label = None
					if (index < len(text)) and (text[index] == "'"):
						# Label is present
						marker_label = ""
						index += 1
						while index < len(text):
							if text[index] == "'":
								break
							else:
								marker_label += text[index]
							index += 1
						index += 1
					cmd = DigitalTimingCmd(cmdtype = DigitalTimingType.Marker, argument = marker_label)
				case "_":
					cmd = DigitalTimingCmd(cmdtype = DigitalTimingType.Empty)
				case " ":
					continue
				case _:
					raise NotImplementedError(f"Unknown character in sequence diagram: {char}")
			sequence.append(cmd)
		return sequence

class DigitalTimingDiagram():
	class Layer(enum.Enum):
		UpperLowerBoundary = "Upper/lower boundaries"
		ClockTicks = "Clock ticks"
		SignalNames = "Signal names"
		Markers = "Markers"
		Signals = "Signals"

	_Marker = collections.namedtuple("Marker", [ "x", "label" ])

	def __init__(self, xdiv: int = 10, height: int = 30, vertical_distance: int = 10, marker_extend: int = 20, clock_ticks: bool = True, low_high_lines: bool = False, use_overline: bool = True):
		self._xdiv = xdiv
		self._height = height
		self._vertical_distance = vertical_distance
		self._marker_extend = marker_extend
		self._render_clock_ticks = clock_ticks
		self._low_high_lines = low_high_lines
		self._use_overline = use_overline
		self._risefall = height / 8
		self._svg = SVGDocument.new()
		self._setup_layers()
		self._path = None
		self._plot_count = 0
		self._clock_ticks = 0
		self._markers = [ ]

	@property
	def svg(self):
		return self._svg

	@property
	def base_height(self):
		return ((self._height + self._vertical_distance) * self._plot_count) - self._vertical_distance

	def _setup_layers(self):
		# Create layers in correct order so that signals are topmost
		for layer in [ self.Layer.UpperLowerBoundary, self.Layer.ClockTicks, self.Layer.SignalNames, self.Layer.Signals ]:
			self._layer(layer)

	@functools.cache
	def _layer(self, layer_id: "Layer"):
		assert(isinstance(layer_id, self.Layer))
		layer_label = layer_id.value
		layer = self._svg.add(SVGGroup.new(is_layer = True))
		layer.label = layer_label
		return layer

	def _transition_middle(self, y, transition_scale = 1):
		transition_width = transition_scale * self._risefall * (abs(y) / self._height)
		lead = (self._xdiv - transition_width) / 2
		self._path.horizontal(lead, relative = True)
		self._path.lineto(Vector2D(transition_width, y), relative = True)
		self._path.horizontal(lead, relative = True)

	def _render_signal_sequence(self, signal_name: str, x, y, cmds):
		signals_layer = self._layer(self.Layer.Signals)
		layer = signals_layer.add(SVGGroup.new(is_layer = True))
		layer.label = signal_name

		prev = None
		self._plot_count += 1
		abs_y_mid = y + (self._height / 2)
		self._path = layer.add(SVGPath.new(Vector2D(x, abs_y_mid)))

		text_width = 50
		raw_signal_name = signal_name.lstrip("!")
		svg_text = self._layer(self.Layer.SignalNames).add(SVGText.new(pos = Vector2D(x - text_width, abs_y_mid - 6), rect_extents = Vector2D(text_width, 30), text = raw_signal_name))
		svg_text.style["text-align"] = "right"
		svg_text.style["font-family"] = "'Latin Modern Roman'"
		if signal_name.startswith("!"):
			# text-decoration: overline does not work reliably (Firefox and
			# Chromium both do not render it), emulate by a path.  Note that
			# this is a really ugly hack that only works for this specific
			# font/font size and only for common glyphs.
			text_width = TextWidthEstimator.estimate_text_width(raw_signal_name)
			path = self._layer(self.Layer.SignalNames).add(SVGPath.new(pos = Vector2D(x + 0.5, abs_y_mid - 5.5)))
			path.horizontal(-text_width, relative = True)
			path.style["stroke-width"] = 0.75

		for cur in cmds:
			if prev is None:
				prev = cur
				if prev.cmdtype in [ DigitalTimingType.Low, DigitalTimingType.LowHigh, DigitalTimingType.LowHighTransition ]:
					self._path.moveto(Vector2D(0, self._height / 2), relative = True)
				elif prev.cmdtype in [ DigitalTimingType.High ]:
					self._path.moveto(Vector2D(0, -self._height / 2), relative = True)

			match (prev.cmdtype, cur.cmdtype):
				case (DigitalTimingType.Low, DigitalTimingType.Low) | (DigitalTimingType.High, DigitalTimingType.High) | (DigitalTimingType.HighZ, DigitalTimingType.HighZ):
					self._path.horizontal(self._xdiv, relative = True)

				case (DigitalTimingType.Low, DigitalTimingType.High):
					self._transition_middle(-self._height)

				case (DigitalTimingType.High, DigitalTimingType.Low):
					self._transition_middle(self._height)

				case (DigitalTimingType.Low, DigitalTimingType.HighZ) | (DigitalTimingType.HighZ, DigitalTimingType.High):
					self._transition_middle(-self._height / 2)

				case (DigitalTimingType.High, DigitalTimingType.HighZ) | (DigitalTimingType.HighZ, DigitalTimingType.Low):
					self._transition_middle(self._height / 2)

				case (DigitalTimingType.LowHigh, DigitalTimingType.LowHigh) | (DigitalTimingType.LowHighTransition, DigitalTimingType.LowHigh):
					with self._path.returnto():
						# High to high
						self._path.moveto(Vector2D(0, -self._height), relative = True)
						self._path.horizontal(self._xdiv, relative = True)
					# Low to low
					self._path.horizontal(self._xdiv, relative = True)

				case (DigitalTimingType.High, DigitalTimingType.LowHigh):
					with self._path.returnto():
						# High to high
						self._path.horizontal(self._xdiv, relative = True)
					# High to low
					self._transition_middle(self._height)

				case (DigitalTimingType.Low, DigitalTimingType.LowHigh):
					with self._path.returnto():
						# Low to high
						self._transition_middle(-self._height)
					# Low to low
					self._path.horizontal(self._xdiv, relative = True)

				case (DigitalTimingType.LowHigh, DigitalTimingType.High):
					with self._path.returnto():
						# High to high
						self._path.moveto(Vector2D(0, -self._height), relative = True)
						self._path.horizontal(self._xdiv, relative = True)
					# Low to low
					self._transition_middle(-self._height)

				case (DigitalTimingType.LowHigh, DigitalTimingType.Low):
					with self._path.returnto():
						# High to low
						self._path.moveto(Vector2D(0, -self._height), relative = True)
						self._transition_middle(self._height)
					# Low to low
					self._path.horizontal(self._xdiv, relative = True)

				case (DigitalTimingType.HighZ, DigitalTimingType.LowHigh):
					with self._path.returnto():
						# HighZ to High
						self._transition_middle(-self._height / 2)
					# HighZ to Low
					self._transition_middle(self._height / 2)

				case (DigitalTimingType.LowHigh, DigitalTimingType.HighZ):
					with self._path.returnto():
						# Low to HighZ
						self._transition_middle(-self._height / 2)
					# High to HighZ
					self._path.moveto(Vector2D(0, -self._height), relative = True)
					self._transition_middle(self._height / 2)

				case (DigitalTimingType.LowHigh, DigitalTimingType.LowHighTransition) | (DigitalTimingType.LowHighTransition, DigitalTimingType.LowHighTransition):
					with self._path.returnto():
						self._transition_middle(-self._height, transition_scale = 2)
					self._path.moveto(Vector2D(0, -self._height), relative = True)
					self._transition_middle(self._height, transition_scale = 2)

				case (_, DigitalTimingType.Empty):
					self._path.moveto(Vector2D(self._path.pos.x + self._xdiv, abs_y_mid))
					prev = None
					continue

				case (_, DigitalTimingType.Marker):
					mid_x = self._path.pos.x
					self._markers.append(self._Marker(x = mid_x + self._xdiv / 2, label = cur.argument))
					continue

				case _ as transition:
					raise NotImplementedError(f"Unsupported digital sequence diagram transition: {transition}")
			prev = cur
		self._clock_ticks = max(self._clock_ticks, round(self._path.pos.x / self._xdiv))

	def _render_markers(self):
		for marker in self._markers:
			have_label = (marker.label is not None) and (marker.label != "")
			marker_length = self.base_height if (not have_label) else (self.base_height + self._marker_extend)

			path = self._layer(self.Layer.Markers).add(SVGPath.new(Vector2D(marker.x, 0)))
			path.vertical(marker_length, relative = True)
			path.style["stroke-width"] = 0.5

			if have_label:
				text_width = 100
				text_height = 50

				svg_text = self._layer(self.Layer.Markers).add(SVGText.new(pos = Vector2D(marker.x - (text_width / 2), marker_length), rect_extents = Vector2D(text_width, text_height), text = marker.label))
				svg_text.style["text-align"] = "center"

	def _do_render_clock_ticks(self):
		if not self._render_clock_ticks:
			return

		for tick in range(self._clock_ticks):
			x = (tick * self._xdiv) + self._xdiv / 2
			path = self._layer(self.Layer.ClockTicks).add(SVGPath.new(Vector2D(x, 0)))
			path.vertical(self.base_height, relative = True)
			path.style["stroke-width"] = 0.25
			path.style["stroke"] = "#95a5a6"
			path.style["stroke-miterlimit"] = 4
			path.style["stroke-dasharray"] = "0.75,0.25"
			path.style["stroke-dashoffset"] = 0

	def _do_render_low_high_lines(self):
		x_width = self._clock_ticks * self._xdiv
		for plot in range(self._plot_count):
			y_high = (self._height + self._vertical_distance) * plot
			y_low = y_high + self._height
			for y in [ y_low, y_high ]:
				path = self._layer(self.Layer.UpperLowerBoundary).add(SVGPath.new(Vector2D(0, y)))
				path.horizontal(x_width, relative = True)

				path.style["stroke-width"] = 0.5
				path.style["stroke"] = "#95a5a6"
				path.style["stroke-miterlimit"] = 4
				path.style["stroke-dasharray"] = "0.75,0.25"
				path.style["stroke-dashoffset"] = 0

	def parse_and_write(self, text):
		text = text.strip("\r\n")
		varno = 0
		for line in text.split("\n"):
			line = line.strip("\r\n \t")
			if line == "":
				continue
			if line.startswith("#"):
				continue
			(varname, sequence) = line.split("=", maxsplit = 1)
			varname = varname.strip("\t ")
			sequence = sequence.strip("\t ")
			cmds = DigitalTimingCmd.parse_sequence(sequence)
			self._render_signal_sequence(varname, 0, (self._height + self._vertical_distance) * varno, cmds)
			varno += 1
		self._render_markers()
		self._do_render_clock_ticks()
		self._do_render_low_high_lines()
