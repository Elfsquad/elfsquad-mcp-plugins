# Structure: nodes, relationships, order and display

## How a node reaches the configurator

A node shows in a configuration only through a structural relationship (type 0 to 3) from its parent. A node
with no incoming structural relationship stays in the model, reads back fine, keeps the model valid, and is
shown nowhere. After a build, check that every node except the root is the `toNodeId` of exactly one
structural relationship:

```
QueryData  entitySet: FeatureModelRelationships  filter: featureModelId eq <modelId>
           select: id,fromNodeId,toNodeId,type,order  top: 3000
```

The root node is the node whose feature is the model's `rootFeatureId` and which has no parent. A model needs
exactly one.

## One structural parent per model

A node can be the target of only one structural relationship in a model. A second one is refused with a
`validation` error whose message is just `Entity already exists.`, naming no field. Cross-tree rules (types 4
to 7) are not counted, so a node can be the target of any number of them.

That is why a move is an update. `UpdateRelationships` with `/fromNodeId` set to the new parent moves the
node in one step, keeping its id and everything that points at it.

To put the same option in two places, place the feature twice (two nodes). `AddFeatureNodes` under each
parent does that.

## Aggregation

`Alternative` and `Or` relationships that share a parent combine into one choice over all of them.
`Optional`, `Mandatory` and the cross-tree types apply per relationship, so a parent may mix those freely.

Two consequences:

- Two independent pick-one questions under one parent become one pick-one question. Give each question its
  own group node.
- `Alternative` from the root into the top-level groups makes the customer pick only one section. Use
  `Mandatory` (section always configured) or `Optional` (section may be skipped) there.

An omitted `type` stores as `0` (Optional). That is a valid row with the wrong meaning when you meant
something else, so always send `type`.

## Order

Sibling order lives on the relationship's `order` field, not on the node. `AddFeatureNodes` appends after
the highest existing order. When you set order yourself, use distinct values (the editor keeps 0, 1, 2, …
per parent). Ties have no defined order.

## Defaults and suggestions

- `default: true` on a structural relationship preselects the child.
- `isDefaultSelector: true` on a `Required` (4) relationship turns "requires" into "suggests": the target is
  selected, and the user may deselect it.
- `hideExcludeInView: true` on an `Excludes` (5) relationship hides the excluded option instead of showing a
  conflict.

## Display type

`displayType` on a relationship controls how the configurator draws the child group. The value that lays out
a group of options is read from the relationship that attaches the **group node** to its parent, not from the
option rows below it.

Values (from the tool schema): 0 Standard, 1 ImageBox, 2 Dropdown, 4 Searchbar, 5 Table, 6 NonDialogSearchbar,
7 Slider, 8 Input, 9 Dialog, 10 Chips, and more. Use Dropdown for long lists, roughly seven options or more.
Searchbar and Table need a subscription feature; without it the write is refused with a sentence saying so.

A node that hosts a linked model must sit under a `Standard` relationship.

## Numeric options

A feature's `minValue`, `maxValue` and `stepValue` bound what the user may type. Take them from the source.
If the source gives no range, ask; a guessed range lets customers enter sizes nobody can build. A feature with
`minValue` equal to `maxValue` (and not both 0) is pinned to that number.

A selected node with no value of its own takes its parent's value. A parent set to 3 makes every such child 3
and multiplies their line prices. Set `inheritParentValue` to false on the node to pin it to 1 instead.

## Hide flags on a node

| Field | Effect |
|---|---|
| `hideInQuotation` | No quotation line for this node. Use on group and container nodes that are not sold. |
| `hideInConfigurator` | Hidden in the configurator (Showroom). With a condition expression, hidden only when the condition holds. |
| `hideInOrderEntry` | Hidden in Order Entry. Same condition rule. |
| `hideInOverview` | Left out of the overview. |
| `isPhantom` | The line is written but flagged as phantom. |

A node that sells nothing but has a feature with no article code and `hideInQuotation` false produces a
quotation line with no article code. Check for that after a build.
