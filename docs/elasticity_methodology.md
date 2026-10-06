# Discount Elasticity Methodology

## Limitation

The Olist dataset contains completed orders but does not contain:

- product-page views,
- customer offer exposure,
- eligible customers who did not purchase,
- historical list prices,
- actual historical promotion assignment,
- inventory availability.

Therefore, this project cannot estimate true causal price elasticity from Olist purchase records alone.

## What this project uses instead

The discount-allocation simulator uses transparent, segment-level elasticity assumptions.

These assumptions estimate how purchase probability may change when price falls because of a discount.

They are scenario inputs, not observed Olist facts.

## Constant-elasticity formula

For each customer segment:

```text
demand_multiplier = (1 - discount_pct) ^ elasticity