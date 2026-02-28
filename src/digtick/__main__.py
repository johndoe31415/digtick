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

import sys
import digtick
from .ActionParse import ActionParse
from .ActionMakeTable import ActionMakeTable
from .ActionPrintTable import ActionPrintTable
from .ActionKVDiagram import ActionKVDiagram
from .ActionSynthesize import ActionSynthesize
from .ActionSatisfied import ActionSatisfied
from .ActionEqual import ActionEqual
from .ActionRandomExpression import ActionRandomExpression
from .ActionRandomTable import ActionRandomTable
from .ActionTransform import ActionTransform
from .ActionDTDCreate import ActionDTDCreate
from .ActionDTDRender import ActionDTDRender
from .MultiCommand import MultiCommand

def main():
	mc = MultiCommand(description = "Digital systems toolkit: simplify, minimize and transform Boolean expressions, draw KV-maps, etc.", trailing_text = f"digtick v{digtick.VERSION}")

	def genparser(parser):
		parser.add_argument("-F", "--read-as-filename", action = "store_true", help = "Instead of having an expression on the command line, specify a file name that contains multiple expressios and format each one linewise.")
		parser.add_argument("-n", "--no-implicit-and", action = "store_true", help = "By default, AND operations are implicity expressed (using a space character). This causes an actual operator to be emitted here.")
		parser.add_argument("-f", "--expr-format", choices = [ "text", "pretty-text", "tex-tech", "tex-math", "dot", "internal" ], default = "text", help = "Print the expression in the desired format. Can be one of %(choices)s, defaults to %(default)s.")
		parser.add_argument("-e", "--validate-equivalence", action = "store_true", help = "When reading a file, ensures that every parsed equation is semantically identical to that before it. Useful for validation of manual computation.")
		parser.add_argument("-v", "--verbose", action = "count", default = 0, help = "Increase verbosity. Can be given multiple times.")
		parser.add_argument("expression", help = "Input expression to parse or filename (if the 'file' option was given)")
	mc.register("parse", "Parse and reformat Boolean expression(s)", genparser, action = ActionParse)

	def genparser(parser):
		parser.add_argument("-o", "--output-variable-name", metavar = "name", default = "Y", help = "Name of the output variable. Defaults to %(default)s.")
		parser.add_argument("-f", "--tbl-format", choices = [ "text", "pretty", "tex", "compact", "logisim" ], default = "text", help = "Print the table in the desired format. Can be one of %(choices)s, defaults to %(default)s.")
		parser.add_argument("-v", "--verbose", action = "count", default = 0, help = "Increase verbosity. Can be given multiple times.")
		parser.add_argument("expression", help = "Input expression to create truth table from")
		parser.add_argument("dc_expression", nargs = "?", help = "Optional expression that gives all don't care values")
	mc.register("make-table", "Create a truth table for a Boolean expression", genparser, action = ActionMakeTable, aliases = [ "mkt" ])

	def genparser(parser):
		parser.add_argument("-f", "--tbl-format", choices = [ "text", "pretty", "tex", "compact", "logisim" ], default = "text", help = "Print the table in the desired format. Can be one of %(choices)s, defaults to %(default)s.")
		parser.add_argument("-u", "--unused-value-is", choices = [ "forbidden", "0", "1", "*" ], default = "forbidden", help = "Treat values that do not appear in truth table as the specified value (0, 1, or \"don't care\" value). By default, strict parsing is performed which means unused values are forbidden and all values need to be set explicitly.")
		parser.add_argument("-v", "--verbose", action = "count", default = 0, help = "Increase verbosity. Can be given multiple times.")
		parser.add_argument("filename", nargs = "?", help = "Filename containing the truth table, tab-separated")
	mc.register("print-table", "Read a table file and print it out", genparser, action = ActionPrintTable)

	def genparser(parser):
		parser.add_argument("-o", "--output-variable-name", metavar = "name", default = "Y", help = "Name of the output variable to use. Defaults to %(default)s.")
		parser.add_argument("-r", "--row-heavy", action = "store_true", help = "For odd number of literals, choose row-heavy representation (vertical) instead of the default column-heavy representation (horizontal)")
		parser.add_argument("-x", "--x-offset", metavar = "offset", type = int, default = 0, help = "Order of literals in the X direction start with this offset. Defaults to %(default)d.")
		parser.add_argument("-y", "--y-offset", metavar = "offset", type = int, default = 0, help = "Order of literals in the Y direction start with this offset. Defaults to %(default)d.")
		parser.add_argument("-X", "--x-invert", action = "store_true", help = "Invert ordering of literals in the X direction")
		parser.add_argument("-Y", "--y-invert", action = "store_true", help = "Invert ordering of literals in the Y direction")
		parser.add_argument("-d", "--literal-order", metavar = "vars", help = "Print literals in the given order. Can be a comma-separated list (\"A,C,D,B\") or simply a string like \"ACDB\" in case of single-letter literals.")
		parser.add_argument("-u", "--unused-value-is", choices = [ "forbidden", "0", "1", "*" ], default = "forbidden", help = "Treat values that do not appear in truth table as the specified value (0, 1, or \"don't care\" value). By default, strict parsing is performed which means unused values are forbidden and all values need to be set explicitly.")
		parser.add_argument("-O", "--output-filename", metavar = "name", help = "Instead of printing in the console, do a SVG rendering and write that to the given filename.")
		parser.add_argument("-v", "--verbose", action = "count", default = 0, help = "Increase verbosity. Can be given multiple times.")
		parser.add_argument("filename", nargs = "?", help = "Filename containing the truth table, tab-separated. Reads from stdin when argument omitted.")
	mc.register("kv", "Print a truth table as KV-diagram", genparser, action = ActionKVDiagram)

	def genparser(parser):
		parser.add_argument("-o", "--output-variable-name", metavar = "name", default = "Y", help = "Name of the output variable to use. Defaults to %(default)s.")
		parser.add_argument("-N", "--no-implicit-and", action = "store_true", help = "By default, AND operations are implicity expressed (using a space character). This causes an actual operator to be emitted here.")
		parser.add_argument("-f", "--expr-format", choices = [ "text", "pretty-text", "tex-tech", "tex-math", "dot", "internal" ], default = "text", help = "Print the expression in the desired format. Can be one of %(choices)s, defaults to %(default)s.")
		parser.add_argument("-u", "--unused-value-is", choices = [ "forbidden", "0", "1", "*" ], default = "forbidden", help = "Treat values that do not appear in truth table as the specified value (0, 1, or \"don't care\" value). By default, strict parsing is performed which means unused values are forbidden and all values need to be set explicitly.")
		parser.add_argument("-c", "--compute", choices = [ "dnf", "cnf", "both" ], default = "both", help = "Compute DNF, CNF or both. Can be one of %(default)s. Defaults to %(default)s.")
		parser.add_argument("-v", "--verbose", action = "count", default = 0, help = "Increase verbosity. Can be given multiple times.")
		parser.add_argument("filename", nargs = "?", help = "Filename containing the truth table, tab-separated. Reads from stdin when argument omitted.")
	mc.register("synthesize", "Synthesize a Boolean expression from a given truth table", genparser, action = ActionSynthesize, aliases = [ "qmc" ])

	def genparser(parser):
		parser.add_argument("-f", "--tbl-format", choices = [ "text", "pretty", "tex", "compact", "logisim" ], default = "text", help = "Print the table in the desired format. Can be one of %(choices)s, defaults to %(default)s.")
		parser.add_argument("-o", "--output-variable-name", metavar = "name", default = "Y", help = "Name of the output variable to use. Defaults to %(default)s.")
		parser.add_argument("-u", "--unused-value-is", choices = [ "forbidden", "0", "1", "*" ], default = "forbidden", help = "Treat values that do not appear in truth table as the specified value (0, 1, or \"don't care\" value). By default, strict parsing is performed which means unused values are forbidden and all values need to be set explicitly.")
		parser.add_argument("-v", "--verbose", action = "count", default = 0, help = "Increase verbosity. Can be given multiple times.")
		parser.add_argument("filename", help = "Filename containing the truth table, tab-separated. Reads from stdin when argument is \"-\".")
		parser.add_argument("expression", help = "Input expression to parse or filename (if the 'file' option was given)")
	mc.register("satisfied", "Verify if a givel Boolean expression satisfies the truth table", genparser, action = ActionSatisfied)

	def genparser(parser):
		parser.add_argument("-v", "--verbose", action = "count", default = 0, help = "Increase verbosity. Can be given multiple times.")
		parser.add_argument("expression1", help = "Input expression 1")
		parser.add_argument("expression2", help = "Input expression 2")
	mc.register("equal", "Comprare two Boolean expression for equality", genparser, action = ActionEqual)

	def genparser(parser):
		parser.add_argument("-n", "--allow-nand-nor-xor", action = "store_true", help = "Allow that expressions contain NAND, NOR and XOR.")
		parser.add_argument("-a", "--allow-trivial", action = "store_true", help = "Allow expressions which simplify to something compartively simple, like tautologies. By default, when such an expression is generated, another try is started.")
		parser.add_argument("-v", "--verbose", action = "count", default = 0, help = "Increase verbosity. Can be given multiple times.")
		parser.add_argument("var_count", type = int, help = "Number of variables in expression")
		parser.add_argument("complexity", type = int, help = "Number of complexity iteration steps to take")
	mc.register("random-expr", "Generate a randomized expression", genparser, action = ActionRandomExpression)

	def genparser(parser):
		parser.add_argument("-f", "--tbl-format", choices = [ "text", "pretty", "tex", "compact", "logisim" ], default = "text", help = "Print the table in the desired format. Can be one of %(choices)s, defaults to %(default)s.")
		parser.add_argument("-o", "--output-variable-name", metavar = "name", action = "append", default = [ ], help = "Name the output variable. Can be specified multiple times to generate a table that has multiple outputs. If omitted, a single output named \"Y\" is generated.")
		parser.add_argument("-0", "--zero-percentage", metavar = "percentage", type = float, default = 40, help = "Percentage of values that have result 0. Defaults to %(default).0f%%.")
		parser.add_argument("-1", "--one-percentage", metavar = "percentage", type = float, default = 40, help = "Percentage of values that have result 0. Defaults to %(default).0f%%.")
		parser.add_argument("-v", "--verbose", action = "count", default = 0, help = "Increase verbosity. Can be given multiple times.")
		parser.add_argument("var_count", type = int, help = "Number of variables in table")
	mc.register("random-table", "Generate a randomized table", genparser, action = ActionRandomTable)

	def genparser(parser):
		parser.add_argument("-t", "--transform", choices = [ "simplify", "nand", "nor" ], default = [ ], action = "append", required = True, help = "Transformation to apply. Can be one of %(choices)s and may be specified multiple times to successively apply transformations. Mandatory argument.")
		parser.add_argument("-n", "--no-implicit-and", action = "store_true", help = "By default, AND operations are implicity expressed (using a space character). This causes an actual operator to be emitted here.")
		parser.add_argument("-f", "--expr-format", choices = [ "text", "pretty-text", "tex-tech", "tex-math", "dot", "internal" ], default = "text", help = "Print the expression in the desired format. Can be one of %(choices)s, defaults to %(default)s.")
		parser.add_argument("-v", "--verbose", action = "count", default = 0, help = "Increases verbosity. Can be specified multiple times to increase.")
		parser.add_argument("expression", help = "Input expression to transform")
	mc.register("transform", "Transform a boolean expression", genparser, action = ActionTransform)

	def genparser(parser):
		parser.add_argument("-s", "--random-seed", help = "Specify a custom seed for reproducible traces. Defaults to a random value.")
		parser.add_argument("-d", "--device", choices = [ "sr-nand-ff", "d-ff", "jk-ff", "jk-ms-ff" ], default = "sr-nand-ff", help = "Generate a timing diagram for this type of device. Can be one of %(choices)s, defaults to %(default)s")
		parser.add_argument("-i", "--initial-state-high", action = "store_true", help = "For devices with an internal state, initialize them with HIGH.")
		parser.add_argument("-n", "--negative-edge-triggered", action = "store_true", help = "For devices which are edge triggered, trigger on the negative edge.")
		parser.add_argument("-l", "--length", metavar = "count", type = int, default = 32, help = "Number of bits to generate. By default %(default)d.")
		parser.add_argument("-v", "--verbose", action = "count", default = 0, help = "Increases verbosity. Can be specified multiple times to increase.")
		parser.add_argument("param", metavar = "signame=value", nargs = "*", help = "Predefine some signals, e.g., 'C=10100010'. By default, those are randomly generated.")
	mc.register("dtd-create", "Generate a digital timing diagram", genparser, action = ActionDTDCreate)

	def genparser(parser):
		parser.add_argument("-f", "--force", action = "store_true", help = "Overwrite output file if it already exists")
		parser.add_argument("-o", "--output-filename", metavar = "filename", default = "timing_diagram.svg", help = "Output filename to write. Defaults to %(default)s.")
		parser.add_argument("-v", "--verbose", action = "count", default = 0, help = "Increases verbosity. Can be specified multiple times to increase.")
		parser.add_argument("filename", nargs = "?", help = "Filename containing the timing diagram data. Reads from stdin when omitted.")
	mc.register("dtd-render", "Render a digital timing diagram to SVG", genparser, action = ActionDTDRender)

	sys.exit(mc.run(sys.argv[1:]) or 0)

if __name__ == "__main__":
	main()
