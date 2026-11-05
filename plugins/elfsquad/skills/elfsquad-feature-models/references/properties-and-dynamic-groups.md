# Feature properties and dynamic groups

## Feature properties

A feature property is a named attribute that features can hold a value for. Its `type` decides which value
field a feature uses:

| Property `type` | Value goes in |
|---|---|
| 0 Input (numeric) | `value` |
| 1 AssociatedFeatures | `associatedFeatureId` |
| 2 Text | `textValue` |

A value in the wrong field is refused.

There is no tool to create a feature property. Find existing ones with `SearchFeatureProperties` (or
`QueryData` on `FeatureProperties`). If the one you need does not exist, ask the user to create it in the
Elfsquad app, then continue.

### Setting values

`SetFeaturePropertyValues` with `entities`, one row per feature and property:

```json
[ { "featureId": "<featureId>", "featurePropertyId": "<propertyId>", "value": 2400 } ]
```

It inserts rows. It does not update existing ones, and nothing stops two rows for the same feature and
property. Before writing, read what is there:

```
QueryData  entitySet: FeatureHasFeatureProperties  filter: featurePropertyId eq <propertyId>
           select: id,featureId,value,textValue  top: 3000
```

To change a value, delete the old row with `DeleteFeaturePropertyValues` (destructive, ask first) and insert
the new one. Values can also be sent with new features: `CreateFeatures` accepts a `properties` list on each
feature in the same shape, without `featureId`.

Property values are tenant-wide, like the features that hold them.

Nothing converts units. If a width property is stored in millimetres on some features and metres on others,
every filter and expression reading it is wrong without any error. Settle the unit before loading values.

## Dynamic groups

A dynamic group hangs on a node. When a configuration runs, the group finds every feature whose property
values match its filters and shows each one as a child of that node. Nothing is written into the model per
option, so adding a matching feature to the catalog adds it to the group.

They pay off for long lists that change with the catalog, roughly 20 options or more. Below that a
hand-made list is simpler. Dynamic groups need a subscription feature; without it the write is refused with
"Dynamic groups are not allowed with your subscription."

### Creating one

1. Make sure every candidate feature has the property values the filters will read.
2. `CreateDynamicGroups` with `entities`. One group per host node. Each group carries:
   - `featureModelId` and `featureModelNodeId` (the host node);
   - `relationshipType`: how the generated options are chosen (0 Optional, 2 Alternative, 3 Or, …);
   - `filters`: a list of filter rows, each with `featurePropertyId`, an operator in
     `featureModelDynamicGroupFilterValueType`, and a comparison value;
   - optionally `orderByColumn` (`price`, `name`, `code`, or a feature property id), `orderDescending`,
     `hideInQuotation`, `isPhantom`.
3. Read the group and its filters back (`QueryData` on `FeatureModelDynamicGroups` and
   `FeatureModelDynamicGroupFilters`) to get their ids.
4. To combine filters with OR, or nest them, use `WriteDynamicGroupFilters` (below). Without it, all filters
   apply together (AND).

Filter operators (`featureModelDynamicGroupFilterValueType`): 0 GreaterThanOrEqual, 1 LessThanOrEqual,
2 Equal, 3 Contains, 4 StartsWith, 5 EndsWith, 6 NotEqual, 7 LessThan, 8 GreaterThan, 9 IsNotSet.

The comparison value of a filter is one of:

- `value` (number) or `textValue` (text): a fixed value;
- `valueFeatureModelNodeId` or `textValueFeatureModelNodeId`: the current value of another node, so the list
  narrows as the user answers an earlier question;
- `valueExpressionId`: an expression (see `elfsquad-model-rules`).

The stored property value is always the left side. A filter "width GreaterThanOrEqual node W" keeps features
whose width is at least W's value.

For an `AssociatedFeatures` property the filter matches on associated features instead, and `strict`
matters: with `strict: true`, a filter that finds no candidates empties the group; with `strict: false` it is
skipped and the other filters decide.

A filter on a property that no candidate has a value for empties the whole group. "The group shows nothing"
usually means unpopulated property values or a unit mismatch.

### The filter tree

`WriteDynamicGroupFilters` with `request`:

```json
{
  "dynamicGroupId": "<groupId>",
  "groups": [ { "id": "<newGuid>", "dynamicGroupId": "<groupId>", "condition": 1, "parentGroupId": null } ],
  "filterPlacements": [ { "filterId": "<filterA>", "filterGroupId": "<newGuid>" },
                        { "filterId": "<filterB>", "filterGroupId": "<newGuid>" } ]
}
```

`condition` is 0 And or 1 Or. Every group repeats the `dynamicGroupId`. The whole tree is written in one
step, so a refused request leaves the stored tree as it was. `groups` is the group's complete set of filter groups: stored groups you leave
out are removed. A filter you do not place keeps its current group; `filterGroupId: null` puts it back at the
top level, which is AND. A group with no filters and no nested groups is refused, and so is a group nested in
itself. Generate the new group ids yourself.

### Hand-listed children

A dynamic group adds to the children already under its host node; it does not replace them. If you convert
a hand-made list to a group, delete the old option nodes afterwards (with the user's agreement), or every
option shows twice. Before deleting, check what points at the old nodes: rules, expressions, quotation lines.

### Verifying

Test in a **new** configuration (`StartConfiguration`), never one opened earlier, because a configuration
keeps the options it already generated. Check that the expected features appear and that nothing extra does.
Then run `ValidateFeatureModelForPublish` and look at `summary.hasSelfFilteringNodes`: a group whose filter
reads a node the group itself generates shows up there.

`DeleteDynamicGroups` with `ids` removes groups. It is destructive; ask first.
