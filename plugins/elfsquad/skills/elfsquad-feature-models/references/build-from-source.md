# Building a model from a spec or spreadsheet

## What the source maps to

| In the source | Becomes |
|---|---|
| A sellable product | A root feature and a feature model (`CreateFeatures`, `CreateFeatureModel`) |
| A heading or question | A group node: a feature placed under its parent, usually with `hideInQuotation: true` |
| An option under a heading | A feature placed under the group node (`AddFeatureNodes`) |
| "Pick one", "pick any", "always included" | Relationship type 2 Alternative, 3 Or, 1 Mandatory |
| Options that cannot both be true of one product | One group, Alternative |
| A long list (about seven options or more) | `displayType` 2 Dropdown on the relationship into the group node |
| A column of attributes (width, material, voltage) | A feature property and one value row per feature |
| A price column | The feature's `salesPrice`, or a node price where it differs per model (see `elfsquad-model-rules`) |
| "X needs Y", "not with Z" | A rule (`elfsquad-model-rules`) |
| A calculation | An expression in a slot (`elfsquad-model-rules`) |
| A wizard page | A configurator step, made in the Elfsquad editor |

A column that is only read by a filter is a feature property, not an option. A column the customer picks from
is an option.

Names and article codes come from the source as written. Do not rename, shorten or tidy them; the people who
use the model wrote the source and need to trace each option back to it. If the source gives no article code,
leave it empty and report it. Never invent codes: they reach ERP systems looking like real part numbers.

Take numeric ranges (`minValue`, `maxValue`, `stepValue`) from the source. If none is given, ask.

## Settle before the first write

- One product, or a family? Machines that share almost everything are usually one model with a variant
  question.
- Which options already exist as features in the library? Reuse them, and note that later edits to them are
  tenant-wide.
- How many options does each question take: exactly one, any number, none or one?
- Which questions depend on earlier answers? That shapes the tree and the rules.
- Which nodes must produce a quotation line? Everything else gets `hideInQuotation: true`.
- Does any subtree occur several times per product? Only then use a linked model.
- Which languages need texts?

## Agree the shape first

Show the user the intended tree: the root, the groups, the relationship type of every group, which questions
are dropdowns, which options carry article codes and prices. Wait for agreement before writing anything.
Where the source does not settle a group's type, ask about that group specifically.

Then state the counts you will create (features, nodes, relationships, property values, rules) so you can
compare them with the result.

## Write order

1. Any linked child models first (and they need publishing in the app before the parent embeds them).
2. Search the library and create missing features with `CreateFeatures`. Texts can go in the same call: each
   feature takes a `texts` list of `{ "languageIso": "en", "type": 0, "value": "…" }`, where `type` 0 is
   Description and 1 is ExtendedDescription. There is no tool to add texts to a feature later, so include them
   here.
3. `CreateFeatureModel` with the root node.
4. Group nodes under the root, then options under each group, with `AddFeatureNodes`.
5. Adjust relationship types, order, defaults and display types with `UpdateRelationships`.
6. Feature property values.
7. Rules, then expressions (an expression points at node ids, so the nodes must exist).
8. `ValidateFeatureModelForPublish`, then a test configuration.

Deletes, if any, come after the replacement validates.

## Finish

Compare the counts with the read-back: nodes, relationships, rules and expressions written against what the
source asked for. A tree without its rules validates clean and still sells the wrong combinations, so count
rules too.

Report what is unfinished, by name: missing article codes, prices left at zero, rules not written, anything
mapped by guesswork, and the steps and publish the user still has to do in the Elfsquad editor.
