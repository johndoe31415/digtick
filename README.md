# digtool
digtool is a command-line-tool tool for creating and solving problems in
digital systems. The primary target audience are educators (who can use it to
create and validate exam questions) as well as students who want to improve
their skills. It allows you to specify, parse and reformat Boolean equations
(e.g., in LaTeX form for easy inclusion in documents). It can create tables
from a given Boolean expression and rendering Karnaugh–Veitch (KV) maps with an
arbitrary number of variables. It can check Boolean equations for equivalance.
A Quine-McCluskey implementation is used to minify expressions.

## Boolean expression syntax
digtool accepts a pragmatic Boolean syntax that matches what students often
write on paper, while still being unambiguous and machine-parseable. Variables
follow a typical identifier pattern (e.g. `A`, `B`, `clk`). Constants are `0`
and `1`.

You can express `OR` as `+` or `|`, `AND` as `*` or `&`, and XOR as `^`.
Negation can be written as `!`, `~`, or `-` prefix. The parser also accepts
NAND `@` and NOR `#` as explicit operators. Note that neither NAND nor NOR are
associative and because they are not "typical" operators in Booolean algebra,
their operator precedence is unspecified. Therefore, during parsing, NAND/NOR
expression always receive implicit parenthesis to make this explicit:

```
$ digtool parse 'A | B + C @ D'
A + B + (C NAND D)
```

Parentheses work as expected for grouping and are deliberately not
automatically removed during parsing (this allows for creating of deliberately
suboptimal queries in a exam-generation scenario):

```
$ digtool parse '(((((A | (B))))))'
(((((A + (B))))))
```

For convenience of notation, `AND` is implicit: adjacency separated by
whitespace counts as `AND`:

```
$ digtool parse 'A B C + A !B C + C !A'
A B C + A !B C + C !A
```

By default, this is also implemented this way in the output, but many commands
allow specifying a particular format, including the `--no-implicit-and` option:

```
$ digtool parse --no-implicit-and 'A B C + A !B C + C !A'
A * B * C + A * !B * C + C * !A
```

There are multiple output options, e.g. a Unicode renderer:

```
$ digtool parse --format pretty-text 'A B C + A !B C + C !A'
A B C ∨ A B̅ C ∨ C A̅
```

## Truth table format
There is a human-readable truth table format which uses Unicode characters for
pretty viewing in a terminal and the machine-readable format which is
tab-separated. The latter is the default output variant and the only variant
which can be used as input:

```
$ digtool make-table 'A B C + A !B C + C !A'
A	B	C
0	0	0	0
0	0	1	1
0	1	0	0
0	1	1	1
1	0	0	0
1	0	1	1
1	1	0	0
1	1	1	1

$ digtool make-table --format pretty 'A B C + A !B C + C !A'
┌───┬───┬───┬───┐
│ A │ B │ C │   │
├───┼───┼───┼───┤
│ 0 │ 0 │ 0 │ 0 │
│ 0 │ 0 │ 1 │ 1 │
│ 0 │ 1 │ 0 │ 0 │
│ 0 │ 1 │ 1 │ 1 │
│ 1 │ 0 │ 0 │ 0 │
│ 1 │ 0 │ 1 │ 1 │
│ 1 │ 1 │ 0 │ 0 │
│ 1 │ 1 │ 1 │ 1 │
└───┴───┴───┴───┘
```

Note that commands which accept truth table inputs can all have the filename
omitted and will then read from stdin. This allows for easy piping of commands:

```
$ digtool make-table 'A B C + A !B C + C !A' | digtool synth
CDNF: !A !B C + !A B C + A !B C + A B C
CCNF: (A + B + C) (A + !B + C) (!A + B + C) (!A + !B + C)
DNF : C
CNF : (C)
```

## "parse": parse and reformat Boolean expressions
`parse` parses an equation and outputs it in a different format, such as LaTeX.
It takes care that in overline-style negation of literals the overline does
*not* automatically carry over to the next character (this is an annoying LaTeX
default, unfortunately, and results in a non-equivalent equation):

```
$ digtool parse --format tex-tech '!A !B'
\overline{\textnormal{A}} \ \overline{\textnormal{B}}
$ digtool parse --format tex-tech '!(A B)'
\overline{(\textnormal{A} \ \textnormal{B})}
```

Note that also the mathematical variant of symbols can be used:

```
$ digtool parse --format tex-math '!(A B)'
\neg \textnormal{A} \ \neg \textnormal{B}
```

## "make-table": generate a truth table from an expression
`make-table` evaluates a Boolean expression over all input combinations and
prints a truth table. An optional second expression can be used to mark “don't
care” output positions (`*`). Wherever the “don't care” expression evaluates to
1, the output is printed as `*` instead of `0` or `1`.

```
$ digtool make-table 'A + B !C' 'A !B'
A	B	C
0	0	0	0
0	0	1	0
0	1	0	1
0	1	1	0
1	0	0	*
1	0	1	*
1	1	0	1
1	1	1	1
```


## "print-table": read and print a table file
`print-table` reads a TSV truth table and prints it back in either plain TSV
form or a formatted view. If your table doesn't define every input combination,
you can decide how missing patterns should be treated. In the default strict
mode, missing patterns are considered an error; in the relaxed modes, missing
patterns are filled as `0`, `1`, or `*`.

```
$ digtool make-table 'A + B !C' 'A !B' | \
  head -n 4 | \
  digtool print-table -f pretty --unused-value-is '*'
┌───┬───┬───┬───┐
│ A │ B │ C │   │
├───┼───┼───┼───┤
│ 0 │ 0 │ 0 │ 0 │
│ 0 │ 0 │ 1 │ 0 │
│ 0 │ 1 │ 0 │ 1 │
│ 0 │ 1 │ 1 │ * │
│ 1 │ 0 │ 0 │ * │
│ 1 │ 0 │ 1 │ * │
│ 1 │ 1 │ 0 │ * │
│ 1 │ 1 │ 1 │ * │
└───┴───┴───┴───┘
```


## "kv": render a Karnaugh–Veitch map from a table
`kv` takes a truth table and lays it out as a KV map. There are multiple ways
to create a KV map which are all. As an educator, I usually have the policy
that my students need not adhere to the format taught in my lectures, but may
choose a different format as long as it produces correct output. This puts the
burden of verification on me, which is cumbersome. For this purpose, this
rendering command accepts a number of different parameters that influence the
way the KV diagram is printed.

```
$ digtool make-table 'A B !C + B D + !C A' 'B !A D + A B C D' >exam1.txt
$ digtool kv exam1.txt
┌─────┬─────┬─────┬─────┬─────┐
│     │ A̅ B̅ │ A B̅ │ A B │ A̅ B │
├─────┼─────┼─────┼─────┼─────┤
│ C̅ D̅ │  0  │  1  │  1  │  0  │
├─────┼─────┼─────┼─────┼─────┤
│ C D̅ │  0  │  0  │  0  │  0  │
├─────┼─────┼─────┼─────┼─────┤
│ C D │  0  │  0  │  *  │  *  │
├─────┼─────┼─────┼─────┼─────┤
│ C̅ D │  0  │  1  │  1  │  *  │
└─────┴─────┴─────┴─────┴─────┘

$ digtool kv exam1.txt -o DCBA --x-offset 1 --y-invert
┌─────┬─────┬─────┬─────┬─────┐
│     │ C̅ D │ C D │ C D̅ │ C̅ D̅ │
├─────┼─────┼─────┼─────┼─────┤
│ A̅ B̅ │  0  │  0  │  0  │  0  │
├─────┼─────┼─────┼─────┼─────┤
│ A B̅ │  1  │  0  │  0  │  1  │
├─────┼─────┼─────┼─────┼─────┤
│ A B │  1  │  *  │  0  │  1  │
├─────┼─────┼─────┼─────┼─────┤
│ A̅ B │  *  │  *  │  0  │  0  │
└─────┴─────┴─────┴─────┴─────┘
```

This makes it much easier to verify solutions for their correctness, regardless
of which format the student chose.


## "synthesize": minimize/synthesize expressions from a truth table
`synthesize` reads a truth table and prints canonical forms (CDNF/CCNF) as well
as minimized forms (DNF/CNF) produced via Quine-McCluskey.

```
$ digtool synth exam1.txt
CDNF: A !B !C !D + A !B !C D + A B !C !D + A B !C D
CCNF: (A + B + C + D) (A + B + C + !D) (A + B + !C + D) (A + B + !C + !D) (A + !B + C + D) (A + !B + !C + D) (!A + B + !C + D) (!A + B + !C + !D) (!A + !B + !C + D)
DNF : A !C + B D
CNF : (!C) (A)
```

## "equal": check whether two expressions are equivalent
`equal` compares two Boolean expressions by evaluating them over all possible
input assignments of the involved variables. If they are equivalent, it reports
success. If they differ, it prints a counterexample assignment.

```
$ digtool eq 'A @ B @ C' 'A @ (B @ C)'
Not equal: {'A': 0, 'B': 0, 'C': 1} gives 0 on LHS but 1 on RHS

$ digtool eq 'A B C + C !D B + B C' 'B C'
Expressions equal.
```

Note that `digtool` also supports checking a whole file for equivalence in the `parse` command. For example, say you have generated an exam and are preparing the reference solution, in which you are performing tiny simplification steps each line:

```
$ cat exam2.txt
A B C + B C (A + D) + B A !D + F (E + !F)
A B C + B C A + B C D + B A !D + F (E + !F)
A B C + B C A + B C D + B A !D + F E + F !F
A B C + B C A + B C D + B A !D
B C A + B C D + B A !D
B (C A + C D + A !D)
B (C D + A !D)
```

Did you spot my error? A simple omission that changes the whole formula:

```
$ digtool parse --read-as-filename --validate-equivalence exam2.txt
A B C + B C (A + D) + B A !D + F (E + !F)
A B C + B C A + B C D + B A !D + F (E + !F)
A B C + B C A + B C D + B A !D + F E + F !F
A B C + B C A + B C D + B A !D
Warning: expression "A * B * C + B * C * A + B * C * D + B * A * !D + F * E + F * !F" on line 3 is not equivalent to expression "A * B * C + B * C * A + B * C * D + B * A * !D" on line 4.
B C A + B C D + B A !D
B (C A + C D + A !D)
B (C D + A !D)
There were validation errors, some of the equations are not equivalent to each other.
```

Once you corrected the mistake, you can then, for example, render as TeX -- I'm
sure you'll agree that this output is a write-only format not intended for
human consumption:

```
\textnormal{A} \ \textnormal{B} \ \textnormal{C} \vee \textnormal{B} \ \textnormal{C} \ (\textnormal{A} \vee \textnormal{D}) \vee \textnormal{B} \ \textnormal{A} \ \overline{\textnormal{D}} \vee \textnormal{F} \ (\textnormal{E} \vee \overline{\textnormal{F}})
\textnormal{A} \ \textnormal{B} \ \textnormal{C} \vee \textnormal{B} \ \textnormal{C} \ \textnormal{A} \vee \textnormal{B} \ \textnormal{C} \ \textnormal{D} \vee \textnormal{B} \ \textnormal{A} \ \overline{\textnormal{D}} \vee \textnormal{F} \ (\textnormal{E} \vee \overline{\textnormal{F}})
\textnormal{A} \ \textnormal{B} \ \textnormal{C} \vee \textnormal{B} \ \textnormal{C} \ \textnormal{A} \vee \textnormal{B} \ \textnormal{C} \ \textnormal{D} \vee \textnormal{B} \ \textnormal{A} \ \overline{\textnormal{D}} \vee \textnormal{F} \ \textnormal{E} \vee \textnormal{F} \ \overline{\textnormal{F}}
\textnormal{A} \ \textnormal{B} \ \textnormal{C} \vee \textnormal{B} \ \textnormal{C} \ \textnormal{A} \vee \textnormal{B} \ \textnormal{C} \ \textnormal{D} \vee \textnormal{B} \ \textnormal{A} \ \overline{\textnormal{D}} \vee \textnormal{F} \ \textnormal{E}
\textnormal{B} \ \textnormal{C} \ \textnormal{A} \vee \textnormal{B} \ \textnormal{C} \ \textnormal{D} \vee \textnormal{B} \ \textnormal{A} \ \overline{\textnormal{D}} \vee \textnormal{F} \ \textnormal{E}
\textnormal{B} \ (\textnormal{C} \ \textnormal{A} \vee \textnormal{C} \ \textnormal{D} \vee \textnormal{A} \ \overline{\textnormal{D}}) \vee \textnormal{F} \ \textnormal{E}
\textnormal{B} \ (\textnormal{C} \ \textnormal{D} \vee \textnormal{A} \ \overline{\textnormal{D}}) \vee \textnormal{F} \ \textnormal{E}
```

## "random-expr": generate a random Boolean expression
`random-expr` generates a random expression over a specified number of
variables that has a certain "complexity" according to some metric (currently,
number of characters in native format). It automatically simplifies the
randomized equations and checks that the minimized variant is not below another
complexity metric (so that tautologies are not created):

```
$ digtool random-expr 4 60
Expression: !((!B !C D A + A C)) (!C) !B !C (!D + !C) + (!C + D) B C D A + !B !A
Simplified: !B !C !D + !A !B + A B C D
```


## "random-table": generate a random truth table
`random-table` creates a truth table for a specified number of variables,
randomly choosing output values according to configured probabilities. By
default the output distribution is 40% zeros, 40% ones, and the remainder
don't-cares. You can adjust the zero/one percentages; whatever remains after
those is implicitly treated as `*`.

```
$ digtool random-table -0 30 -1 50 3
A	B	C
0	0	0	0
0	0	1	1
0	1	0	*
0	1	1	*
1	0	0	1
1	0	1	1
1	1	0	1
1	1	1	0
```


## License
GNU GPL-3.
