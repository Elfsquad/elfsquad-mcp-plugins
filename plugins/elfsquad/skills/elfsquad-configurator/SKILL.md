---
name: elfsquad-configurator
description: Configure Elfsquad CPQ products through the MCP server, the way a customer or sales user does in the configurator. Covers ListConfigurationModels, StartConfiguration, OpenConfiguration, UpdateConfiguration (select, deselect, set a number), SetConfigurationText, conflicts and unanswered mandatory options, prices, GetConfigurationOverview, DuplicateConfiguration, SearchConfigurations and GetOrderEntryView. Use to build a configuration for a quote, to answer "what options does this product have", to test that a rule fires, or to find out why an option cannot be selected.
---

# Configuring a product

A configuration is one set of choices on one feature model. It has an id, belongs to the user who made it,
and can be added to a quotation (`elfsquad-quotations`). Every tool takes `tenantHandle`.

Starting and changing a configuration works with Read access: `StartConfiguration`, `UpdateConfiguration`
and `SetConfigurationText` store nothing in the model. `DuplicateConfiguration` needs Write access.

## Start

1. `ListConfigurationModels` (optional `lang`) lists the models you may configure, by category, with their
   ids. It lists published models only, and a dealer user sees only what their organization may sell.
2. `StartConfiguration` with `input`:

```json
{ "featureModelId": "<modelId>", "languageIso": "en", "currencyIso": "EUR" }
```

`languageIso` and `currencyIso` are optional (`ListLanguages`, `ListCurrencies`). Keep the returned `id`; it
is the configuration id for every later call.

`featureModelId` also accepts the model's name or an existing configuration's code. A code does not resume
that configuration. It copies it into a new one, and your changes go to the copy. To continue an existing
configuration, use `OpenConfiguration` with its id.

## What a configuration answer contains

`StartConfiguration`, `OpenConfiguration`, `UpdateConfiguration` and `SetConfigurationText` all return the
whole configuration:

- `id`, `configurationModelId`, `language`, `currency`;
- prices: `basePriceExclVat`, `additionalPriceExclVat`, `totalPriceExclVat`, `totalPriceInclVat` as
  formatted text, and `totalPriceExclVatNumber`, `totalPriceInclVatNumber` as numbers;
- `steps`: each step's `features`, a tree of nodes. Each node has `id` (the node id you send back),
  `parentId`, `name`, `articleCode`, `isSelected`, `value`, `textValue`, `isMandatory`, `minValue`,
  `maxValue`, `stepValue`, `unitOfMeasurement`, `totalPrice`, `isDisabled`, `disabledReason` and its child
  `features`;
- `unansweredMandatories`: required choices not made yet, by node id and name;
- `conflicts`: what the last change could not do (see below);
- `linkedConfigurations`: sub-configurations of linked models.

Options the rules have removed from play are absent from `steps`, not flagged. Absence does not mean the
model lacks the option.

`isDisabled` is set only by rules between a model and its linked models. An option blocked by an ordinary
rule in the same model shows `isDisabled: false`. Read `conflicts` to see why a choice was refused.

## Change choices

`UpdateConfiguration` with `configurationId`, `requirement` and optionally `ignoreConflicts`:

| Intent | `requirement` |
|---|---|
| Select an option | `{ "featureModelNodeId": "<nodeId>", "isSelection": true, "value": 1 }` |
| Deselect it | `{ "featureModelNodeId": "<nodeId>", "isSelection": true, "value": 0 }` |
| Set a number (length, quantity) | `{ "featureModelNodeId": "<nodeId>", "isSelection": false, "value": 2400 }` |

`SetConfigurationText` with `id` (the configuration id) and `updatedRequirement`
`{ "featureModelNodeId": "<nodeId>", "textValue": "…" }` fills a text field.

Rules:

- One change per call, and wait for each answer before sending the next for the same configuration. Never
  send changes to one configuration in parallel. Different configurations can run in parallel.
- The answer to a change is the new state. You do not need to open the configuration again to see it.
- Make changes in the order the user would. The same end state reached in a different order can resolve
  differently.
- Use node ids from the latest answer. Do not send a step id where a node id belongs.

## Conflicts

When a change breaks a rule, the change is not applied and `conflicts` explains it: `feature` (the node),
`featurePath` (its path from the root), `requestedValue`, `actualValue`, and `alternativeOptions` the solver
would accept. Show this to the user and let them choose. To apply the change anyway and let the
configurator drop whatever blocks it, send the same change with `ignoreConflicts: true`, after telling the
user what will be dropped.

An empty `conflicts` list does not always mean nothing was refused:

- An environment setting can force automatic conflict resolution. Then a conflicting choice is applied and
  the blocking options are deselected without any conflict being reported. Check with
  `QueryData` on `Settings`, selecting `disableConflictDialog` and `disableConflictDialogOrderEntry`.
- A conflict inside a linked sub-configuration is resolved automatically and never reported. Open the
  sub-configuration (`OpenConfiguration` with its id from `linkedConfigurations`) and make the change there to
  see it.

So when an option deselects itself, compare the before and after states and name what changed.

## Reading and reopening

`OpenConfiguration` with `configurationId` (optional `lang`) returns the stored configuration. The stored
state is written shortly after each change, so an open straight after a change can briefly show the
previous state. If it does, open once more before concluding anything was lost.

`GetConfigurationOverview` with `configurationId` returns the configuration as it is checked out: the
chosen lines and their prices. Use it to summarize a configuration for the user.

`SearchConfigurations` (`search`, `limit`, `skip`, `orderby`, `descending`) lists configurations. For field
filters (a model, a date, a creator) use `QueryData` on `Configurations` (`elfsquad-data-queries`).

`DuplicateConfiguration` with `configurationId` and `value` (how many copies, at most 30) returns the ids of
the copies. Ask before making copies.

There is no tool to delete a configuration.

## Errors you may see

| Error | Meaning |
|---|---|
| `validation` with `CONFIGURATION_MODEL_CHANGED` | The model changed so much that this configuration is no longer valid. Start a new one. |
| `transient` (timeout) | The solve took too long. Retry once. If it repeats on the same configuration, report it. |
| `permission` on start or open | The user's organization may not sell this model. |

## Testing a rule

1. `StartConfiguration` fresh. Do not reuse an existing configuration; it carries earlier choices and, for
   dynamic groups, options it generated before.
2. Select the trigger with `UpdateConfiguration`.
3. Check the effect in that answer: the target selected, removed, its value changed, or the expected conflict.
4. Report what you saw, with the node names.

## Seeing a model the way users do

`GetOrderEntryView` with `modelId` renders, as text, what Order Entry shows for a fresh configuration:
steps, lines, the control each line gets, descriptions, collapsed lines and counts. It stores nothing. Use
`languageIso`, `published: true` for the last published version, and `expand: true` to include collapsed
lines. It answers as the calling user, so a dealer sees their organization's view. Linked sub-models are not
opened.

## From configuration to quotation

`CreateQuotationFromConfigurations` or `CreateQuotation` plus `AddConfigurationsToQuotation`. Both are
covered in `elfsquad-quotations`.
