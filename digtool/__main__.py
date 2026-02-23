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

import sys
from .ActionParse import ActionParse
from .ActionMakeTable import ActionMakeTable
from .ActionPrintTable import ActionPrintTable
from .ActionSynthesize import ActionSynthesize
from .ActionEqual import ActionEqual
from .ActionQMC import ActionQMC
from .ActionCanonicalize import ActionCanonicalize
from .ActionRandom import ActionRandom
from .ActionDigitalTimingDiagram import ActionDigitalTimingDiagram
from .ActionTransform import ActionTransform
from .MultiCommand import MultiCommand

def main():
	mc = MultiCommand(description = "Tool to compute and simplify problems in digital systems", run_method = True)

	def genparser(parser):
		parser.add_argument("-n", "--no-implicit-and", action = "store_true", help = "By default, AND operations are implicity expressed (using a space character). This causes an actual operator to be emitted here.")
		parser.add_argument("-f", "--format", choices = [ "text", "tex-tech", "tex-math", "internal" ], default = "text", help = "Print the expression in the desired format. Can be one of %(choices)s, defaults to %(default)s.")
		parser.add_argument("-v", "--verbose", action = "count", default = 0, help = "Increase verbosity. Can be given multiple times.")
		parser.add_argument("expression", help = "Input expression to parse")
	mc.register("parse", "Parse and reformat a Boolean expression", genparser, action = ActionParse)

	def genparser(parser):
		parser.add_argument("-f", "--format", choices = [ "text", "pretty" ], default = "text", help = "Print the table in the desired format. Can be one of %(choices)s, defaults to %(default)s.")
		parser.add_argument("-v", "--verbose", action = "count", default = 0, help = "Increase verbosity. Can be given multiple times.")
		parser.add_argument("expression", help = "Input expression to create truth table from")
		parser.add_argument("dc_expression", nargs = "?", help = "Optional expression that gives all don't care values")
	mc.register("make-table", "Create a truth table for a Boolean expression", genparser, action = ActionMakeTable)

	def genparser(parser):
		parser.add_argument("-f", "--format", choices = [ "text", "pretty" ], default = "text", help = "Print the table in the desired format. Can be one of %(choices)s, defaults to %(default)s.")
		parser.add_argument("-u", "--unused-value-is", choices = [ "forbidden", "0", "1", "*" ], default = "forbidden", help = "Treat values that do not appear in truth table as the specified value (0, 1, or \"don't care\" value). By default, strict parsing is performed which means unused values are forbidden and all values need to be set explicitly.")
		parser.add_argument("-v", "--verbose", action = "count", default = 0, help = "Increase verbosity. Can be given multiple times.")
		parser.add_argument("filename", help = "Filename containing the input data and output data, tab-separated")
	mc.register("print-table", "Read a table file and print it out", genparser, action = ActionPrintTable)

	def genparser(parser):
		parser.add_argument("-n", "--no-optimization", action = "store_true", help = "Do not automatically optimize the resulting expression.")
		parser.add_argument("-v", "--verbose", action = "count", default = 0, help = "Increase verbosity. Can be given multiple times.")
		parser.add_argument("filename", help = "Filename that contains the table data")
	mc.register("synthesize", "Synthesize a Boolean expression from a given truth table", genparser, action = ActionSynthesize)

	def genparser(parser):
		parser.add_argument("-v", "--verbose", action = "count", default = 0, help = "Increase verbosity. Can be given multiple times.")
		parser.add_argument("expression1", help = "Input expression 1")
		parser.add_argument("expression2", help = "Input expression 2")
	mc.register("equal", "Comprare two Boolean expression for equality", genparser, action = ActionEqual)

	def genparser(parser):
		parser.add_argument("-v", "--verbose", action = "count", default = 0, help = "Increase verbosity. Can be given multiple times.")
		parser.add_argument("expression", help = "Expression to minimize")
		parser.add_argument("dc_expression", nargs = "?", help = "Optional expression that gives all don't care values")
	mc.register("qmc", "Minimize a Boolean expression using the Quine-McCluskey method", genparser, action = ActionQMC)

	def genparser(parser):
		parser.add_argument("-c", "--ccnf", action = "store_true", help = "By default, the canonical disjunctive normal form (CDNF) is generated. With this switch, the canonical conjunctive normal form (CCNF) is generated instead.")
		parser.add_argument("-v", "--verbose", action = "count", default = 0, help = "Increase verbosity. Can be given multiple times.")
		parser.add_argument("expression", help = "Input expression to canonicalize")
	mc.register("canonicalize", "Canonicalize an expression into CDNF or CCNF", genparser, action = ActionCanonicalize)

	def genparser(parser):
		parser.add_argument("-v", "--verbose", action = "count", default = 0, help = "Increase verbosity. Can be given multiple times.")
		parser.add_argument("var_count", type = int, help = "Number of variables in expression")
		parser.add_argument("minterm_count", type = int, help = "Number of minterms in expression")
	mc.register("random", "Generate a randomized CDNF", genparser, action = ActionRandom)

	def genparser(parser):
		parser.add_argument("-s", "--random-seed", help = "Specify a custom seed for reproducible traces. Defaults to a random value.")
		parser.add_argument("-d", "--device", choices = [ "sr-nand-ff", "d-ff", "jk-ff", "jk-ms-ff" ], default = "sr-nand-ff", help = "Generate a timing diagram for this type of device. Can be one of %(choices)s, defaults to %(default)s")
		parser.add_argument("-i", "--initial-state-high", action = "store_true", help = "For devices with an internal state, initialize them with HIGH.")
		parser.add_argument("-n", "--negative-edge-triggered", action = "store_true", help = "For devices which are edge triggered, trigger on the negative edge.")
		parser.add_argument("-l", "--length", metavar = "count", type = int, default = 32, help = "Number of bits to generate. By default %(default)d.")
		parser.add_argument("-v", "--verbose", action = "count", default = 0, help = "Increases verbosity. Can be specified multiple times to increase.")
		parser.add_argument("param", metavar = "signame=value", nargs = "*", help = "Predefine some signals, e.g., 'C=10100010'. By default, those are randomly generated.")
	mc.register("dtd", "Generate a digital timing diagram", genparser, action = ActionDigitalTimingDiagram)

	def genparser(parser):
		parser.add_argument("-l", "--logic", choices = [ "nand", "nor", "xor" ], default = "nand", help = "Logic type to transform to. Can be one of %(choices)s, defaults to %(default)s.")
		parser.add_argument("-v", "--verbose", action = "count", default = 0, help = "Increases verbosity. Can be specified multiple times to increase.")
		parser.add_argument("expression", help = "Input expression to transform")
	mc.register("transform", "Transform a boolean expression", genparser, action = ActionTransform)

	sys.exit(mc.run(sys.argv[1:]) or 0)

if __name__ == "__main__":
	main()
