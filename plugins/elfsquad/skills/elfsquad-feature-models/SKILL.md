---
name: elfsquad-feature-models
description: Build, read and edit Elfsquad CPQ feature models (configuration models, products) through the MCP server. Covers features in the feature library, the model and its root node, nodes and structural relationships (option groups, Optional, Mandatory, Alternative, Or), feature properties and their values, dynamic groups, linked sub-models, model versions, DiagnoseFeatureModel, ValidateFeatureModelForPublish, the Order Entry view, and the 3D model tree. Use to create a model from a spec or spreadsheet, add or move options, delete nodes, or review a model before publishing. Rules and expressions are in elfsquad-model-rules.
---

# Feature models

A feature model describes one configurable product. It is built from four kinds of record:

| Record | What it is | Scope |
|---|---|---|
| Feature | A catalog item: name, article code, sales price, min/max/step value, texts. | Tenant-wide. One feature can be used in many models. |
| Feature model | The product. Its name is its root feature's name. | One per product. |
| Node | A feature placed in one model. The same feature can be placed more than once. | One model. |
| Relationship | A link from a parent node to a child node. Its `type` says how the children are chosen. | One model. |

An option group ("choose a colour") is a parent node plus the relationships into its children. It has no
record of its own.

Every tool takes `tenantHandle`. See `elfsquad-getting-started` for access levels and error handling.

## Standing rules

- Read before you write. Find the model with `SearchFeatureModels` (or `QueryData`, see
  `elfsquad-data-queries`), then read it with `GetFeatureModelHayf`.
- Reuse features. Search the library with `SearchFeatures` before `CreateFeatures`, so the catalog does not
  fill with duplicates.
- Editing a feature with `UpdateFeatures` changes it in every model that uses it. Say so and ask first.
- Ask before every delete: `DeleteFeatureModelNodes`, `DeleteRelationships`, `DeleteFeaturePropertyValues`,
  `DeleteDynamicGroups`, `DeleteThreeDModel`. Do deletes last, after the replacement exists.
- Prefer changing or moving a node over deleting and recreating it. Rules, expressions, quotation lines and
  3D bindings point at node ids. A new node starts with none of them, and nothing reports the break.
- Count what you meant to create, then read back and compare. Every call commits on its own.
- Writes need Write access. Without it they are refused and nothing changes.

## Reading a model

`GetFeatureModelHayf` with `modelId` returns the model as HAYF text: nodes, structure, features,
constraints and expressions in one answer.

- `sections`: comma-separated subset of `features`, `structure`, `constraints`, `expressions`. Omit for all.
  A misspelled name is ignored and that section is silently left out.
- `subtreeRootNodeId`: a node id to return only that branch. Useful on large models.
- The ALIAS MAP at the end maps each `@alias` in the text to a node id. Use those ids in write tools.
- On an environment with feature-model versioning, HAYF shows the **last published version**. Edits made
  since then do not appear in it. To check a change you just made, read rows with `SearchFeatureModelNodes`
  or `QueryData` instead.
- HAYF leaves out relationship ids, `order` and `displayType`, steps, dynamic groups, linked-model rows and
  most per-node flags. Read `FeatureModelRelationships` with `QueryData` when you need those.

`SearchFeatureModelNodes` with `featureModelId`, `limit` and `include: ["feature"]` lists a model's current
nodes with their features.

## Creating a model from nothing

1. Create the root feature. Its `name` becomes the model's name.
   `CreateFeatures` with `features: [ { "name": "X500 Loader", "type": 0 } ]`. Keep the returned `id`.
2. Create the model with its root node in one call:

```json
CreateFeatureModel  entity: { "rootFeatureId": "<rootFeatureId>", "nodes": [ { "featureId": "<rootFeatureId>" } ] }
```

3. Find the root node id: `SearchFeatureModelNodes` with the new model's id. The root node is the one whose
   feature is the root feature.
4. Add the option groups and options (next section).

A new model has no configurator steps, and steps cannot be created with these tools. Publishing is not a
tool either. Both are done in the Elfsquad editor. Tell the user when they are needed.

## Adding options

`AddFeatureNodes` places existing features under a parent node and creates the relationships in one call:

```json
AddFeatureNodes  model: { "nodeId": "<parentNodeId>", "featureIds": ["<f1>", "<f2>"], "relationshipType": 2 }
```

The new options go after the existing children, in the order of `featureIds`. All of them get the same
relationship type. This is the default way to add options.

For finer control (a different type or `displayType` per child, a preselected default) change the
relationships with `UpdateRelationships` afterwards. `AddFeatureNodes` is the only tool that adds a plain
node to an existing model, so a node always arrives with a relationship to its parent. `CreateRelationships`
is for rules between nodes that already exist (see `elfsquad-model-rules`).

### Relationship types

| `type` | Name | Meaning |
|---|---|---|
| 0 | Optional | The child may be selected. |
| 1 | Mandatory | The child is always part of the configuration. |
| 2 | Alternative | Pick exactly one of the siblings. |
| 3 | Or | Pick one or more of the siblings. |
| 4 | Required | Cross-tree rule: selecting the parent requires the child. See `elfsquad-model-rules`. |
| 5 | Excludes | Cross-tree rule: the two cannot be combined. |
| 6 | Implies | A calculated value. |
| 7 | Includes | Cross-tree rule: selecting one forces the other on. |

Types 0 to 3 are structural. Types 4 to 7 are rules and are covered in `elfsquad-model-rules`.

The two-level pattern matters. All `Alternative` (or all `Or`) relationships under one parent merge into a
single choice. If you hang "colour" and "size" options directly under the same parent as Alternatives, the
customer can pick only one of them in total. Give each question its own group node:

```
root ─Mandatory→ Colour (group) ─Alternative→ Red, Blue
     ─Mandatory→ Size (group)   ─Alternative→ S, M, L
```

Use `Mandatory` or `Optional` from the root into each group, and `Alternative` or `Or` from a group to its
options. A group node is a feature too; create one with `CreateFeatures` (for example "Colour") and place it
with `AddFeatureNodes`.

Details on ordering, defaults, display types and reparenting are in
[references/structure.md](references/structure.md).

## Changing nodes, relationships and features

`UpdateFeatureModelNodes`, `UpdateRelationships` and `UpdateFeatures` take a bulk JSON Patch:

```json
{
  "ids":        ["<idA>", "<idA>", "<idB>"],
  "operations": [
    { "op": "replace", "path": "/hideInQuotation", "value": true },
    { "op": "replace", "path": "/infoField", "value": "Fits frames from 2020" },
    { "op": "replace", "path": "/hideInQuotation", "value": true }
  ]
}
```

`ids[i]` is the record that `operations[i]` applies to. To change two fields on one record, list its id
twice. The arrays must be the same length. Paths are top-level camelCase field names; an unknown name fails
the call. Use `replace`.

Common edits:

- Move a node to another parent: `UpdateRelationships` on its structural relationship with
  `/fromNodeId` set to the new parent node id. Do not delete and recreate the relationship. A node can have
  only one structural parent per model, so creating the new one first fails, and deleting first leaves it
  detached.
- Reorder siblings: `UpdateRelationships` with `/order` on each relationship.
- Change how a group chooses: `UpdateRelationships` with `/type`.
- Rename or reprice a catalog item: `UpdateFeatures` with `/name` or `/salesPrice` (tenant-wide).
- Node flags: `UpdateFeatureModelNodes` with `/hideInQuotation`, `/hideInOverview`, `/isPhantom`,
  `/inheritParentValue`, `/defaultValue`, `/infoField`, and the expression slots in `elfsquad-model-rules`.

## Deleting nodes

`DeleteFeatureModelNodes` takes `nodeIdsList` and `confirmed`. It is destructive and cannot be undone.

1. Show the user which nodes will go, by name, and get a yes.
2. Call once without `confirmed`. Nothing is deleted; the ids come back for confirmation.
3. Call again with `confirmed: true`.

It removes the named nodes and every relationship attached to them. It does **not** remove their children:
children of a deleted node are left detached unless you name them too. Ids that no longer exist come back as
a warning. Entries that are not GUIDs are dropped silently, so compare the deleted count with what you sent.

A delete can fail with a generic `internal` error when another record still points at the node, for example
a dynamic group hosted on it. Retry one id at a time to find which node is held, and tell the user.

`DeleteRelationships` with `ids` removes relationships only. Removing a node's structural relationship leaves
the node in the model but unreachable.

## Feature properties, dynamic groups, linked models

- Feature properties are named attributes (width, voltage, colour family) that features hold values for.
  Dynamic groups and expressions read them. See [references/properties-and-dynamic-groups.md](references/properties-and-dynamic-groups.md).
- A dynamic group fills a node's children at configuration time from features whose property values match
  filters. Same reference.
- A linked model embeds another feature model under a node, configured as its own sub-configuration. See
  [references/linked-models-and-versions.md](references/linked-models-and-versions.md).

## Checking a model

Run these after a batch of changes, and before the user publishes.

| Tool | Answers |
|---|---|
| `ValidateFeatureModelForPublish` with `modelId` | The full pre-publish check on the current draft: can it be configured at all, broken expressions, references to deleted nodes, circular dependencies, self-filtering dynamic groups. `data.status` is `ready` or `needs_attention`, with the findings. |
| `DiagnoseFeatureModel` with `featureModelId` | Whether the model can be configured at all, and if not, a smallest set of rule ids whose removal fixes it. Empty lists mean consistent. |
| `GetOrderEntryView` with `modelId` | What a sales user sees in Order Entry for a fresh configuration: steps, each line and its control, descriptions, collapsed lines. Options: `languageIso`, `published: true` for the last published version, `expand: true` for collapsed lines. Writes nothing. |
| `ListFeatureModelVersions` with `featureModelId` | The model's published versions. |

`ValidateFeatureModelForPublish` writes nothing to the model, but when a model turns out to be inconsistent,
the solve records that against it. On large models it can return a `transient` error when it runs out of
time; retry once.

A clean validation does not prove that a rule fires as intended. Test it in a configuration
(`elfsquad-configurator`).

## 3D

`GetThreeDTranslationStatus` with `id` (the feature model id) reports how far the translation of an uploaded
CAD model has come. `GetThreeDModelTree` with `featureModelId` returns the part names and object ids once
translation has finished; a model still translating returns a retryable error. `DeleteThreeDModel` with `id`
removes the model's 3D model; it is destructive, so ask first.

Uploading a CAD file and binding parts to nodes are done in the Elfsquad editor.

## Building from a spec or spreadsheet

Follow [references/build-from-source.md](references/build-from-source.md). In short, agree the tree with the
user before writing, reuse features, write in the order feature, model, groups, options, properties, rules,
then validate and report counts against the source.
