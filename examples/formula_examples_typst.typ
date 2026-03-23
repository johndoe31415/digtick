#let bnand = box(width: 1em, height: 0.6em)[#place(center, dy: -0.1em)[#sym.and] #place(center, dy: -0.1em)[#text(size: 0.85em)[#sym.tilde]]]
#let bnor = box(width: 1em, height: 0.6em)[#place(center, dy: -0.1em)[#sym.or] #place(center, dy: -0.1em)[#text(size: 0.85em)[#sym.tilde]]]
#let bnot(body) = $overline(#v(1em)#h(0em) body)$

#let boxframe = rgb("#b4bcc4")

#let sourcebox(body) = block(
	inset: 8pt,
	radius: 3pt,
	stroke: (paint: boxframe, thickness: 0.6pt),
	fill: rgb("#f7f7f7"),
	width: 100%,
	body,
)
#let renderedbox(body) = block(
	inset: 8pt,
	radius: 3pt,
	stroke: (paint: boxframe, thickness: 0.6pt),
	fill: rgb("#ffffff"),
	width: 100%,
	body,
)

#align(center)[
	#text(24pt, weight: "bold")[`digtick` Typst formula showcase]
	#v(12pt)
	#text(16pt)[digtick v0.1.1rc0 / Typst #sys.version]
	#v(28pt)
]


= Purpose
This document shows several formulas in their raw form (i.e., how they were supplied directly to `digtick`) and the rendered Typst output that `digtick` produces from them, usually with multiple variants.

= Examples

#block(breakable: false)[
#text(weight: "medium")[Raw digtick input:]
#v(4pt)
#sourcebox(align(center, [
	`A !B !C D !E + !<AB> + (!A + !C) (!B + !(C + BD) + !<!A + !B + C + D>)`
]))

Default rendering:
#renderedbox([
	$ upright(A) bnot(upright(B)) thin bnot(upright(C)) upright(D) bnot(upright(E)) or bnot(upright("AB")) or (bnot(upright(A)) or bnot(upright(C))) (bnot(upright(B)) or bnot((upright(C) or upright("BD"))) or bnot(bnot(upright(A)) or bnot(upright(B)) or upright(C) or upright(D))) $
])
Using math operators:
#renderedbox([
	$ upright(A) not upright(B) not upright(C) upright(D) not upright(E) or not upright("AB") or (not upright(A) or not upright(C)) (not upright(B) or not (upright(C) or upright("BD")) or not (not upright(A) or not upright(B) or upright(C) or upright(D))) $
])
]
#v(2cm)


#block(breakable: false)[
#text(weight: "medium")[Raw digtick input:]
#v(4pt)
#sourcebox(align(center, [
	`(A + B + 0) (C D 1)`
]))

Default rendering:
#renderedbox([
	$ (upright(A) or upright(B) or 0) (upright(C) upright(D) 1) $
])
Using math operators and constants:
#renderedbox([
	$ (upright(A) or upright(B) or bot) (upright(C) upright(D) top) $
])
]
#v(2cm)


#block(breakable: false)[
#text(weight: "medium")[Raw digtick input:]
#v(4pt)
#sourcebox(align(center, [
	`A + B * C`
]))

Default rendering:
#renderedbox([
	$ upright(A) or upright(B) upright(C) $
])
]
#v(2cm)


#block(breakable: false)[
#text(weight: "medium")[Raw digtick input:]
#v(4pt)
#sourcebox(align(center, [
	`<A + B> ~C`
]))

Default rendering:
#renderedbox([
	$ (upright(A) or upright(B)) bnot(upright(C)) $
])
Using math operators:
#renderedbox([
	$ (upright(A) or upright(B)) not upright(C) $
])
]
#v(2cm)


#block(breakable: false)[
#text(weight: "medium")[Raw digtick input:]
#v(4pt)
#sourcebox(align(center, [
	`<<<<A + <B>>>>> C`
]))

Default rendering:
#renderedbox([
	$ (upright(A) or upright(B)) upright(C) $
])
]
#v(2cm)


#block(breakable: false)[
#text(weight: "medium")[Raw digtick input:]
#v(4pt)
#sourcebox(align(center, [
	`A ^ B % !C @ D`
]))

Default rendering:
#renderedbox([
	$ upright(A) xor upright(B) bnor bnot(upright(C)) bnand upright(D) $
])
Using math operators:
#renderedbox([
	$ upright(A) xor upright(B) bnor not upright(C) bnand upright(D) $
])
]
#v(2cm)


#block(breakable: false)[
#text(weight: "medium")[Raw digtick input:]
#v(4pt)
#sourcebox(align(center, [
	`F_7 !F_4 !F_2 + F_4 F_1 !F_0 + !<F_2 F_3>`
]))

Default rendering:
#renderedbox([
	$ upright("F_7") bnot(upright("F_4")) thin bnot(upright("F_2")) or upright("F_4") upright("F_1") bnot(upright("F_0")) or bnot(upright("F_2") upright("F_3")) $
])
Using math operators:
#renderedbox([
	$ upright("F_7") not upright("F_4") not upright("F_2") or upright("F_4") upright("F_1") not upright("F_0") or not (upright("F_2") upright("F_3")) $
])
]
#v(2cm)


