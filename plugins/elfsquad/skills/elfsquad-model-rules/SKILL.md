---
name: elfsquad-model-rules
description: Write and explain the rules of an Elfsquad CPQ feature model through the MCP server. Covers requires, suggests, excludes, removes and includes relationships (CreateRelationships), calculated values, default and maximum value formulas, hide conditions, node price formulas, and expressions with their variables (ValidateExpression, CreateExpression, UpdateExpression). Use when a user says "X needs Y", "X is not allowed with Y", "hide this unless", "calculate the length from", or when a formula gives the wrong number or a rule does not fire.
---

# Model rules and expressions

A rule decides which combinations a configuration allows, or computes a number. Rules are written on an
existing model's nodes, so build the structure first (`elfsquad-feature-models`). Every tool takes
`tenantHandle`, and every write here needs Write access, `ValidateExpression` included.

## Standing rules

- Pick the simplest rule that says what the user means. A relationship rule needs no expression, costs less
  to solve, and the configurator can name the conflict it causes. Use an expression only when a relationship
  cannot say it.
- Validate an expression before saving it, then test the rule in a fresh configuration
  (`elfsquad-configurator`). A clean validation proves the formula compiles, not that it does what was asked.
- Every call commits on its own. A formula is several writes (expression, then slot). If a later step
  fails, say what was left behind.
- Ask before deleting a rule (`DeleteRelationships`). Set a new rule before removing the old one, so the
  option is never unguarded in between.

## Which rule for which intent

| The user says | Write | How |
|---|---|---|
| Selecting X requires Y | Relationship type 4 Required, from X to Y | `CreateRelationships` |
| Selecting X suggests Y, user may remove it | Type 4 with `isDefaultSelector: true` | `CreateRelationships` |
| X and Y can never be combined | Type 5 Excludes | `CreateRelationships` |
| Selecting X removes Y from view | Type 5 with `hideExcludeInView: true` | `CreateRelationships` |
| Selecting X switches Y on | Type 7 Includes | `CreateRelationships` |
| Y starts selected | `default: true` on Y's structural relationship | `UpdateRelationships` |
| Y's number is calculated and can only be raised by the user | Calculated value: type 6 Implies with an expression | `CreateExpression`, then `CreateRelationships` |
| Y starts at a calculated number the user may change | Default-value expression on the node | `CreateExpression`, then `UpdateFeatureModelNodes` |
| Y may not exceed a calculated number | Max-value expression on the node | same |
| Y is hidden while something holds | Hide flag plus a condition expression on the node | same |
| Y's price is calculated | Price expression on the node | same, see [references/pricing-on-nodes.md](references/pricing-on-nodes.md) |

Only the Archer 1.2 solver applies Includes (type 7). On an environment running an older solver version it
has no effect, so test it in a configuration.

## Relationship rules

`CreateRelationships` with `entities`:

```json
[ { "featureModelId": "<modelId>", "fromNodeId": "<X>", "toNodeId": "<Y>", "type": 4 } ]
```

Both nodes must already exist. A node can carry any number of rule relationships.

Two traps that no validation reports:

- An Excludes aimed at a node that a Mandatory relationship forces on makes every configuration
  inconsistent at configure time. Use `hideExcludeInView: true` on the exclude, which removes the target
  instead.
- That same repair is how a required option quietly stops being required. A hidden or removed node counts as
  satisfied for the Mandatory, Alternative and Or rules that point at it.

If a model cannot be configured at all, `DiagnoseFeatureModel` (with `featureModelId`) names a smallest set of
rule ids to remove (`requiresToRemove`, `excludesToRemove`, and others). Show them to the user; do not
delete them on your own.

## Expressions

An expression is a formula with named inputs. Its `expressionString` names inputs by tag, such as `@width`,
and each input is an expression variable that binds one tag to a node.

### 1. Validate

`ValidateExpression` with `model`:

```json
{ "expression": "@width * 2 + 100", "parameters": ["@width"], "type": "number" }
```

`type` is `number` for values and prices, `bool` for conditions. `parameters` lists every tag the body uses.
An empty list back means it compiles. This check covers the default grammar (Linq) only.

### 2. Create

`CreateExpression` with `entity`, the variables inside it:

```json
{
  "expressionString": "@width * 2 + 100",
  "expressionType": 0,
  "variables": [ { "tag": "@width", "nodeId": "<widthNodeId>" } ]
}
```

The server compiles the body against the variables' tags and refuses it with a message if it does not
compile. Keep the returned `id`.

### 3. Point a slot at it

| Slot | Write |
|---|---|
| Calculated value | `CreateRelationships`: `{ "featureModelId": …, "fromNodeId": "<node>", "toNodeId": "<node>", "type": 6, "expressionId": "<id>" }`. The node receiving the value is `fromNodeId`; point `toNodeId` at the same node. |
| Default value | `UpdateFeatureModelNodes`: `/defaultValueExpressionId` |
| Maximum value | `UpdateFeatureModelNodes`: `/maxValueExpressionId` |
| Hide in configurator when true | `UpdateFeatureModelNodes`: `/hideInConfigurator` = true **and** `/hideInConfiguratorConditionId` |
| Hide in Order Entry when true | `UpdateFeatureModelNodes`: `/hideInOrderEntry` = true **and** `/hideInOrderEntryConditionId` |
| Price | `UpdateFeatureModelNodes`: `/divergentPriceExpressionId` |

`UpdateFeatureModelNodes` takes the bulk patch shape (`ids` and `operations`, paired by position) described
in `elfsquad-feature-models`. Calculated values (type 6) need a subscription feature; without it the write is
refused with "Formulas are not allowed with your subscription."

The hide flag and its condition go together. With the flag false, the condition is never read. With the flag
true and no condition, the node is always hidden. A hide condition answers "is this node hidden", so it is
true when the node should disappear.

### Choosing the slot

Decide the slot before writing. Once configurations depend on it, moving a formula changes which numbers
users can enter.

- A default-value expression gives a starting number. A number the user types wins over it from then on.
- A calculated value is a floor: the user can type a higher number but not a lower one. When a node has
  several calculated values, the highest wins, so adding a second one can only raise the result.
- A maximum-value expression clamps what the user types.

### Changing an expression

`UpdateExpression` with `entity` replaces the expression row. Send the whole expression: `id`,
`expressionString`, `expressionType` and its variables as you read them. To read the current ones:

```
QueryData  entitySet: Expressions  filter: id eq <expressionId>  top: 1
QueryData  entitySet: ExpressionVariables  filter: expressionId eq <expressionId>  top: 100
```

When the inputs change a lot, it is often cleaner to create a new expression and point the slot at it.

There is no tool to delete an expression. An expression nothing points at does nothing.

## Conditions on a relationship

Elfsquad can also put a condition on the relationship into an option ("show this option only when the long
chassis is selected"). Writing those conditions is not covered by these tools. Two ways forward:

- Use a hide condition on the option's node instead, with the condition reversed (true when it should be
  hidden). Remember that a hidden node counts as satisfied for a Mandatory rule.
- Or ask the user to add the condition in the Elfsquad editor.

## Verify

1. `ValidateFeatureModelForPublish` with `modelId`. Look at `data.summary.isSatisfiable`,
   `data.brokenExpressions` and `data.constraints.toRemove`. Repair and repeat until `data.status` is `ready`.
2. Start a fresh configuration, select the trigger, and check the effect in the returned configuration
   (`elfsquad-configurator`). Report the rule as working only after that.

Formulas fail quietly in two ways. A division by zero leaves the node at zero, and in the Archer grammar a
misspelled tag turns into a text constant so a comparison is always false. Both show up only in a test
configuration. More in [references/expression-language.md](references/expression-language.md).
