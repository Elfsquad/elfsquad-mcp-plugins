# Prices on features and nodes

## Where a unit price comes from

For each selected node, the configurator takes one unit price, in this order of override:

1. The feature's `salesPrice` in the catalog. Change it with `UpdateFeatures` (`/salesPrice`). It is
   tenant-wide: every model using the feature changes. Ask first.
2. A price agreed for the user's organization, set in the Elfsquad app. It replaces the catalog price.
3. A node price in this model: a fixed `divergentPrice`, or a price expression in
   `divergentPriceExpressionId`. Set either with `UpdateFeatureModelNodes`. It replaces whatever came before.

Node prices only take effect when the environment's setting for per-node prices is on. Check it:

```
QueryData  entitySet: Settings  select: id,organizationId,divergentFeatureModelNodePrices  top: 50
```

With it off, node prices are stored and ignored. The setting is read from the tenant's row (the one whose
`organizationId` is empty).

A node price stops the node following later catalog price changes, ERP updates included. Clearing both node
fields brings the catalog price back.

## Price expressions

- A price expression returns a **unit** price. Quantity is applied afterwards, so do not multiply by the
  node's own quantity in the formula.
- If the formula does not compile, the price falls back to the fixed `divergentPrice` if set, otherwise to the
  catalog price. A division by zero gives 0. Neither shows an error, so "the price did not change" is not
  proof the formula works. Check it in a configuration.
- Calculated prices need a subscription feature; without it the write is refused with a sentence saying so.

## Reading prices

The configuration tools return prices: `totalPriceExclVat` and `totalPriceInclVat` on the configuration, and
a `totalPrice` per node. `GetConfigurationOverview` returns the chosen lines with prices. Prices on a
quotation are in its lines (`GetQuotation` with `include: ["lines"]`). See `elfsquad-configurator` and
`elfsquad-quotations`.

VAT percentages in Elfsquad are whole numbers (21 means 21 percent). Discounts, margins and exchange rates are
set in the Elfsquad app; these tools do not write them.
