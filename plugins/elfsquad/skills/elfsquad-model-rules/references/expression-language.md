# The expression language

## Grammars

`expressionType` picks the grammar: 0 Linq (the default), 1 Python, 2 Archer. Write Linq unless the user's
model already uses another. `ValidateExpression` checks Linq only. Pre-publish validation skips Python
expressions, so a broken one shows up only in a configuration.

Only the Archer 1.1 and 1.2 solvers compile Archer expressions. On an environment running an older
solver version an Archer formula in a value slot or condition does nothing, while validation stays clean.

## Types

A body compiles to the type its slot needs: true/false for a condition or hide condition, a number for value
and price slots. A bare number is not a condition. Write a comparison: `@a + @b <> 0`.

Linq rewrites bare integers to decimals before compiling, so `1 / 2` is `0.5`. It also strips `//` and
`/* */` comments. Archer does neither: write `1.0 / 2.0` and keep comments out.

Archer operators: `+ - * /`, `< <= > >=`, `== != <>`, `&&` `||`, and `=` as equality. The lower-case word
forms `and` and `or` treat numbers as true/false; capital `AND` and `OR` do not.

## Tags

A variable's `tag` is the name the body uses, `@` included. The body must contain it exactly. A formula reads
its inputs only through tags, never through feature or node names. A body naming the feature instead of the
tag binds nothing. A Linq body then fails to compile; an Archer body treats the unknown name as text and the
comparison is always false.

Tags and node names drift apart. Renaming a node does not rename the tag, so read tags from the variable
rows, never derive them from a name.

`Feature.tags`, the free-text labels on a feature, are unrelated and cannot be read by an expression.

## What a variable reads

Each variable binds one node. Its flags decide what it reads from that node.

| Flags on the variable | Reads |
|---|---|
| none | The node's value (its quantity, or the number the user typed). 0 when not selected. |
| `featurePropertyId` | That feature property's value on the node's feature. |
| `useUnitPrice` | The node's catalog unit price, excluding VAT. |
| `useSelected` | Whether the node is selected, as true/false. Archer 1.2 solver only. |
| `children` | An aggregate over the node's direct children instead of the node itself. |
| `childCalculationMethod` | With `children`: 0 Sum, 1 Average, 2 Min, 3 Max. |
| `exists` | Multiplies the bound value by the node's own value, so an unselected node gives 0. |
| `multilevel` | With `children`, all descendant levels. Archer 1.2 solver only. |
| `isSelfReference` | "This node". Needed when a dynamic group copies the rule onto each generated option. |

Points that catch people:

- A feature-property or unit-price binding on a single node is read whether or not the node is selected. To
  count it only when selected, add `exists`, or aggregate through the parent with `children`, which counts
  selected children only.
- A `useSelected` variable is true/false. Arithmetic on it does not compile; compare it instead.
- `exists` with no property, unit price or `useSelected` fails to build.

## Replacing a long OR with data

A condition like `@A <> 0 or @B <> 0 or @C <> 0`, naming every option in a group, needs a new variable for
every new option. Put the enumeration in the data instead: give each option a number on one numeric feature
property, bind one variable to the group node with `children: true`, that `featurePropertyId` and
`childCalculationMethod: 0` (Sum), and compare the sum with the number of the option you mean, for example
`@picked = 40` under a pick-one group. A new option with the property filled in is covered automatically.

## Silent failures

- A division by zero, or any result that is not a finite number, is dropped and the node stays at 0. Guard
  divisors: `iif(@d <> 0, @a / @d, 0)`.
- A formula can read 0 for a node the solver has not reached yet. If a value looks too low only in some
  orders of selection, that is the first thing to suspect.
- An unknown identifier in an Archer body is treated as text.

None of these produce an error. Check the result in a configuration.
