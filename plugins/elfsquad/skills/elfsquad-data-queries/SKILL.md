---
name: elfsquad-data-queries
description: Read, filter, count and look up Elfsquad CPQ data through the MCP server. Covers QueryData, ListDataSets and DescribeDataSet (OData filter, select, expand, orderby, top, count on any entity set such as Features, FeatureModels, FeatureModelNodes, Quotations, QuotationLines, Configurations, CrmAccounts, Settings) and the free-text Search tools (SearchFeatures, SearchFeatureModels, SearchFeatureModelNodes, SearchFeatureProperties, SearchQuotations, SearchConfigurations, SearchCrmAccounts), plus ListLanguages and ListCurrencies. Use for reports, lookups, "which features cost more than", "how many quotations", or finding an id before an edit.
---

# Querying Elfsquad data

Two kinds of read tools exist. Pick by what the question needs.

| Need | Tool |
|---|---|
| Filter or sort on a field, count rows, pick fields, follow a relation | `QueryData` |
| Find something by a word in its name, with no field filter | a Search tool |
| One whole feature model in a single read | `GetFeatureModelHayf` (see `elfsquad-feature-models`) |
| One quotation with its lines | `GetQuotation` with `include` (see `elfsquad-quotations`) |

Every call takes the `tenantHandle` from `SelectTenant` (see `elfsquad-getting-started`).

## QueryData: the Data API

`QueryData` runs an OData query against one entity set and filters on the server. Use it instead of paging
a Search tool and filtering rows yourself.

Arguments:

| Argument | OData option | Notes |
|---|---|---|
| `entitySet` | path | Required. A name from `ListDataSets`, for example `Features`. Letters, digits and underscores only. |
| `top` | `$top` | Required. At most 3000. |
| `filter` | `$filter` | `salesPrice gt 5000`, `contains(name,'pump')`, `status eq 1`, `featureModelId eq <guid>`. |
| `select` | `$select` | Comma-separated fields. Ask only for what you need. |
| `expand` | `$expand` | Related records, ideally with their own select: `rootFeature($select=name)`. |
| `orderby` | `$orderby` | `name desc`. |
| `skip` | `$skip` | For paging. |
| `count` | `$count` | `true` adds the total number of matching rows. |

Steps for an unfamiliar question:

1. `ListDataSets` to see the entity set names.
2. `DescribeDataSet` with `entitySet` to get the field names, their types, and the navigations `expand`
   can follow. Field names are camelCase.
3. `QueryData`.

Practical rules:

- To size a result before reading it, ask for `count: true` with `top: 1`.
- A misspelled field in `filter` or `select` is an error, not an empty result. Check the name with
  `DescribeDataSet` before concluding there are no rows.
- Fewer rows than you expected, and no error, can mean the result spans pages. Page with `skip` and
  compare with the `count`.
- GUIDs go in a filter unquoted: `featureModelId eq 5f0c…`.
- Before filtering on an enum field, check its type with `DescribeDataSet`, or read one row without a
  filter to see how the value comes back.
- A feature model has no name of its own. Its name is its root feature's name, so filter through it:
  `entitySet: FeatureModels`, `expand: rootFeature($select=name)`,
  `filter: contains(rootFeature/name,'loader')`. Names are not unique; show the matches and let the user pick.

`QueryData` needs tenant administrator rights or the `canUseOdata` permission. Without them it is refused.
Fall back to the Search tools, and tell the user that field filtering needs that permission.

Some fields exist in the Elfsquad app but not in a Data API set. If `DescribeDataSet` does not list a field,
`QueryData` cannot read it.

### Entity sets you will use most

`Features`, `FeatureTexts`, `FeatureProperties`, `FeatureHasFeatureProperties`, `FeatureModels`,
`FeatureModelNodes`, `FeatureModelRelationships`, `FeatureModelDynamicGroups`,
`FeatureModelDynamicGroupFilters`, `LinkedFeatureModels`, `Expressions`, `ExpressionVariables`, `Steps`,
`Configurations`, `Quotations`, `QuotationLines`, `QuotationStatuses`, `CrmAccounts`, `CrmContacts`,
`Organizations`, `Categories`, `Languages`, `Currencies`, `Vats`, `Settings`. `ListDataSets` has the full list.

### Examples

Features over a price, cheapest first:

```
QueryData  entitySet: Features  filter: salesPrice gt 5000  select: id,name,articleCode,salesPrice
           orderby: salesPrice  top: 100
```

How many quotations a CRM account has:

```
QueryData  entitySet: Quotations  filter: debtorId eq <crmAccountId>  select: id  count: true  top: 1
```

The structure of one model, as rows:

```
QueryData  entitySet: FeatureModelRelationships  filter: featureModelId eq <modelId>
           select: id,fromNodeId,toNodeId,type,order,displayType  top: 3000
```

## The Search tools

`SearchFeatures`, `SearchFeatureModels`, `SearchFeatureProperties`, `SearchQuotations`,
`SearchConfigurations` and `SearchCrmAccounts` take the same arguments:

- `search`: free text over the record's searchable fields. There is no field filter.
- `limit`: always pass one. Without it a list returns up to 10,000 rows and is refused as too large.
- `skip`, `orderby` (a property name), `descending` (true or false).

`SearchFeatureModelNodes` takes `featureModelId`, `search`, `limit`, `skip` and `include` instead. Pass
`featureModelId` to read one model's nodes, and `include: ["feature"]` to get each node's feature (its name
and article code) in the same answer.

`SearchFeatureModels` returns only `id`, `status` (1 active, 0 draft), `publishedVersion`, the two hide flags
and `rootFeature` with `id`, `name` and `articleCode`.

A dealer (organization) user sees only the features and models their organization may sell.

## Languages and currencies

`ListLanguages` and `ListCurrencies` return what the environment uses. Use them to pick a valid
`languageIso` or `currencyIso` for `StartConfiguration`, `GetOrderEntryView` or a quotation.
