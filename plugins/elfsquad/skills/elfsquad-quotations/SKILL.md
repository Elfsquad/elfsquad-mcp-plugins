---
name: elfsquad-quotations
description: Create and manage Elfsquad CPQ quotations and CRM accounts through the MCP server. Covers CreateQuotationFromConfigurations, CreateQuotation, AddConfigurationsToQuotation, GetQuotation with lines and prices, SearchQuotations, UpdateQuotation (status, remarks, subject), ListQuotationStatuses, SetQuotationCrm (customer, seller, ship-to), and SearchCrmAccounts, GetCrmAccount, CreateCrmAccount, UpdateCrmAccount, ListCrmContacts. Use to turn a configuration into a quote, find or report on quotations, move a quote to another status, attach a customer, or explain the prices and totals on a quote.
---

# Quotations and CRM

A quotation holds lines built from one or more configurations, plus a customer (debtor), a seller and a
ship-to address taken from CRM accounts. Every tool takes `tenantHandle`, and every write here needs Write
access.

## Standing rules

- Name the quotation and the customer to the user before changing either.
- Each call commits on its own. A create, then attach, then status change that fails halfway leaves a
  half-built quotation. Say what exists if you stop.
- Read back with `GetQuotation` after every write. A success reply is not proof that the value landed; a
  JSON Patch path the quotation does not have is skipped without an error.
- `GetQuotation` returns `{}` when the quotation does not exist or you may not see it.

## Turning configurations into a quotation

Two ways. Both put every configuration on the quotation at **quantity 1**; neither tool can set another
quantity.

**One call.** `CreateQuotationFromConfigurations` with `quotationRequest`:

```json
{ "quotation": { "subject": "Loader X500", "currencyIso": "EUR", "debtorId": "<crmAccountId>" },
  "configurationIds": ["<configurationId>"] }
```

It accepts a `quantities` map, but the lines are still built at quantity 1. If this call fails it tends to
fail with an empty `validation` message; use the two-step way to get a readable error.

**Two steps.**

1. `CreateQuotation` with `entity`, for example
   `{ "subject": "Loader X500", "currencyIso": "EUR", "languageIso": "en" }`. Keep the returned `id`.
2. `AddConfigurationsToQuotation` with `id` and `configurationIds`.

Things that change along the way:

- A quotation with no currency takes the currency of the first configuration added.
- `updateLocalization: true` on `AddConfigurationsToQuotation` overwrites the quotation's language and
  currency with the first configuration's, and a currency change reprices the whole quotation. Leave it off
  unless the user asks.
- The prices on a line are fixed when the line is built. Changing the model or the catalog later does not
  move them.

To quote several units, add the configuration and tell the user to set the quantity on the line in the
Elfsquad app. `DuplicateConfiguration` makes separate copies (separate lines), not a quantity.

## Reading quotations

`GetQuotation` with `id`. Pass `include: ["lines"]` for the lines with their prices. The answer also carries
totals such as `totalPriceExclVat`, `totalPriceInclVAT` and `totalDiscountPct`, the status (`statusId`),
`debtorId`, `sellerId`, `shipToId`, `currencyIso`, `languageIso`, `subject`, `remarks` and `expiresDate`.

`SearchQuotations` (`search`, `limit`, `skip`, `orderby`, `descending`) finds quotations by free text. For
"quotations in status X", "for customer Y", "above amount Z", use `QueryData` on `Quotations` or
`QuotationLines` (`elfsquad-data-queries`).

What users can see depends on their role. Some environments let users see only quotations they created.

## Status

`ListQuotationStatuses` lists the environment's statuses with their ids and names. Statuses differ per
environment; never assume an id or a name from another one.

`UpdateQuotation` with `id` and `patchDocument` writes the status directly:

```json
[ { "op": "replace", "path": "/statusId", "value": "<statusId>" } ]
```

To move a quotation through its workflow, use the status action in the Elfsquad app. Set `/statusId`
directly only when the user explicitly asks for it, and confirm before you do it.

`UpdateQuotation` also changes plain fields: `/subject`, `/remarks`, `/customerReference`, `/deliverydate`
and others. Paths are top-level camelCase field names.

## Customer, seller and ship-to

`SetQuotationCrm` with `id` (the quotation), `type` and `crmid` (a CRM account id) links an account to a
quotation. The server accepts these `type` values:

| `type` | Sets |
|---|---|
| `to` | The customer (debtor) |
| `from` | The seller |
| `shipTo` | The ship-to address |

The tool's own description mentions `debtor`, `deliver` and `invoice`; the server refuses those. Use the
values in the table. `crmid` must be a CRM account. A dealer user can only link accounts of their own
organization.

## CRM accounts

| Tool | Arguments |
|---|---|
| `SearchCrmAccounts` | `search`, `limit`, `skip`, `orderby`, `descending` |
| `GetCrmAccount` | `id` |
| `ListCrmContacts` | `id` (the account) |
| `CreateCrmAccount` | `entity`: the account's fields, such as `companyName`, `email`, `countryIso`, `city` |
| `UpdateCrmAccount` | `id` and `patchDocument`, a JSON Patch: `[ { "op": "replace", "path": "/email", "value": "…" } ]` |

Search before creating, so the CRM does not fill with duplicates. `UpdateCrmAccount` needs the `manageCrm`
permission. There is no tool to create a contact.

## Prices on a quotation

A line's price comes from the configuration: catalog price, an organization price, or a node price on the
model (see `elfsquad-model-rules`, references/pricing-on-nodes.md). After that come line discounts, discount
lines, VAT and the exchange rate. Discounts, margins and quotation documents are managed in the Elfsquad app.

When a user asks why a total is what it is:

1. `GetQuotation` with `include: ["lines"]`. Find the line.
2. If it came from a configuration, `GetConfigurationOverview` on that configuration shows the chosen lines
   and their prices before discounts.
3. Compare with the feature's `salesPrice` (`QueryData` on `Features`) and any node price on the model.
4. Explain where the difference enters. If it is a discount or margin, say so; those are not editable here.

VAT percentages are whole numbers (21 means 21 percent).
