# Linked models and versions

## Linked models

A linked model embeds one feature model inside another. In a configuration, each instance of it is a
sub-configuration of its own, solved separately from the parent. Use one when a subtree has to exist several
times per product (three identical axles, say), or when the same assembly is shared by many products and
maintained once.

If the subtree exists once per product and is only used there, build it as ordinary nodes instead. It is
simpler and solves as one tree.

### Adding one

`AddLinkedFeatureModels` with `models`, a list:

```json
[ { "nodeId": "<parentNodeId>", "featureModelId": "<childModelId>", "relationshipType": 1 } ]
```

For each entry it creates a host node (a node with no feature), the link to the child model, and a
relationship from the parent node to the host node, appended after the existing children. All entries must
share the same `nodeId`; the first entry's parent is used for all of them.

Before linking:

- The child model must exist, and on an environment with feature-model versioning it should be published,
  because the parent embeds the child's published version.
- A change to the child later needs the child republished, and the parent too if it should pick up the change.
- Leave the hosting relationship's `displayType` at 0 Standard. Compact display types (table, chips and so
  on) cannot host an embedded configuration.

How many instances a link allows (cardinality) and the rules that pass values between parent and child are
not editable with these tools. The link is created with the defaults; set the rest in the Elfsquad editor.

In `ValidateFeatureModelForPublish` and `DiagnoseFeatureModel`, `linkedModels` in the list of rules to remove
names linked-model constraints that make the model inconsistent.

### What the configuration shows

In `StartConfiguration` and `OpenConfiguration` answers, `linkedConfigurations` lists the
sub-configurations with their own `linkedConfigurationId`, `parentNodeId` and `multiplier`. Open a
sub-configuration with `OpenConfiguration` on its id to change options inside it (see `elfsquad-configurator`).

## Versions and publishing

On an environment with feature-model versioning, the model you edit is a working draft. Customers and sales
users configure the last published version until someone publishes again.

- `ListFeatureModelVersions` with `featureModelId` lists the published versions.
- `GetFeatureModelHayf` shows the last published version, not the draft.
- `ValidateFeatureModelForPublish` checks the draft, which is what a publish would take.
- `GetOrderEntryView` shows the draft by default and the published version with `published: true`.
- `ListConfigurationModels` lists published models only, and new configurations start from the published
  version.

Publishing is not available as a tool. When the draft is ready (validation `ready`, and tested), tell the user
to publish it in the Elfsquad editor. On an environment without versioning there is no draft: every change is
live as soon as it is written.
