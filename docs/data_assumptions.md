# Data Assumptions

## Project Purpose

This document defines the assumptions used to extend the real Olist Brazilian E-Commerce dataset for the Discount Dependency Analysis project.

The Olist dataset contains real historical transaction data but does not contain historical discount, promotion, product-cost, marketing-exposure, or explicit post-delivery return information.

Therefore, this project separates:

```text
OBSERVED DATA
     ↓
ESTIMATED DATA
     ↓
SIMULATED DATA
```

No estimated or simulated value will be presented as an actual historical Olist observation.

---

# 1. Assumption Categories

Every field created during the project must be classified as one of the following.

## 1.1 Observed

Observed fields exist directly in the original Olist dataset.

Examples:

```text
order_id
customer_id
customer_unique_id
order_purchase_timestamp
order_status
product_id
seller_id
price
freight_value
payment_value
review_score
```

These fields can be described as actual Olist observations.

---

## 1.2 Estimated

Estimated fields do not exist directly in Olist but are calculated using documented assumptions.

Examples:

```text
estimated_cogs
estimated_payment_fee
estimated_fulfillment_cost
estimated_return_cost
estimated_contribution_margin
```

These values are analytical estimates and must not be described as actual Olist financial records.

---

## 1.3 Simulated

Simulated fields are created to model hypothetical promotion scenarios.

Examples:

```text
baseline_list_price
discount_pct
discount_amount
synthetic_paid_price
promotion_id
promotion_exposure
is_discounted
```

These fields do not represent historical Olist promotions.

They represent a controlled analytical scenario.

---

# 2. Baseline Price Assumption

Olist provides an observed item-level:

```text
price
```

However, Olist does not provide a confirmed historical list price or original pre-discount price.

Therefore, the project will not claim that:

```text
price = original list price
```

Instead, for the simulation:

```text
baseline_list_price = observed Olist price
```

This means the observed Olist selling price is used as the baseline from which hypothetical discounts are modeled.

Example:

```text
Observed Olist price = R$100
```

For the simulation:

```text
baseline_list_price = R$100
```

If a simulated discount of 20% is applied:

```text
discount_amount = R$100 × 20%
                = R$20

synthetic_paid_price = R$100 - R$20
                     = R$80
```

The R$80 value is simulated and must not be described as the historical amount actually paid by the customer.

---

# 3. Synthetic Promotion Framework

The project will use several hypothetical promotion types to model different business situations.

| Promotion ID | Discount | Target / Scenario                | Business Purpose                     |
| ------------ | -------: | -------------------------------- | ------------------------------------ |
| `FULL_PRICE` |       0% | No promotion                     | Control/no-offer scenario            |
| `WELCOME10`  |      10% | First-time customers             | Test a small acquisition incentive   |
| `LAPSED20`   |      20% | Customers inactive for 60+ days  | Model customer reactivation          |
| `CATEGORY15` |      15% | Selected category/month scenario | Model targeted category promotion    |
| `BLANKET30`  |      30% | Broad customer population        | Model aggressive blanket discounting |

These promotion assignments are simulated.

They do not represent historical Olist campaigns.

---

# 4. FULL_PRICE Assumption

The `FULL_PRICE` scenario represents customers who receive no simulated discount.

```text
discount_pct = 0%
```

This acts as the baseline/no-offer scenario.

It is used to compare customer behavior and estimated economics against promotional scenarios.

---

# 5. WELCOME10 Assumption

The `WELCOME10` scenario represents a hypothetical first-purchase incentive.

```text
discount_pct = 10%
```

Target:

```text
First-time customers
```

Business question:

> Does a small first-purchase incentive potentially improve customer acquisition and future purchase behavior without creating excessive discount dependency?

This is a simulated acquisition scenario.

---

# 6. LAPSED20 Assumption

The `LAPSED20` scenario represents a hypothetical reactivation promotion.

```text
discount_pct = 20%
```

Target:

```text
Customers who have not purchased for 60+ days
```

Business question:

> Is a deeper discount potentially justified to reactivate an inactive customer?

The 60-day threshold is a project assumption and does not come from Olist.

---

# 7. CATEGORY15 Assumption

The `CATEGORY15` scenario represents a targeted category-level promotion.

```text
discount_pct = 15%
```

Target:

```text
Selected product category/month scenario
```

Business question:

> Are promotions potentially more effective when targeted at selected categories rather than applied broadly to all customers?

The selected categories and campaign timing will be defined during the implementation stage.

---

# 8. BLANKET30 Assumption

The `BLANKET30` scenario represents an aggressive broad discounting strategy.

```text
discount_pct = 30%
```

This scenario is intentionally modeled as a hypothetical business strategy.

It does not represent an actual Olist promotion.

Business question:

> What could happen to revenue, contribution margin, and customer behavior if a business broadly offered a 30% discount?

This scenario will be particularly useful for evaluating the potential downside of excessive discounting.

---

# 9. Synthetic Holdout Assumption

Where a promotion scenario requires comparison between an offer and a no-offer group, a synthetic holdout will be created.

For eligible customers:

```text
70% → simulated offer group
30% → synthetic holdout group
```

The holdout group receives:

```text
discount_pct = 0%
```

The offer group receives the relevant simulated promotion.

Example:

| Group   | Discount |
| ------- | -------: |
| Offer   |      10% |
| Holdout |       0% |

The synthetic holdout is used for scenario comparison.

It must not be described as a real randomized experiment.

Because the original Olist dataset did not randomly assign historical discounts, differences between groups cannot be interpreted as definitive causal effects.

---

# 10. Random Seed

The simulation will use a fixed random seed:

```text
RANDOM_SEED = 42
```

The purpose is reproducibility.

With a fixed random seed, the same code and same input data should produce the same simulated assignments.

Example:

```text
Run 1 → same assignment
Run 2 → same assignment
Run 3 → same assignment
```

This allows the project to be reproduced and audited.

---

# 11. Discount Calculation

For each simulated discounted item:

```text
discount_amount =
    baseline_list_price × discount_pct
```

The simulated paid price is:

```text
synthetic_paid_price =
    baseline_list_price - discount_amount
```

Example:

```text
baseline_list_price = R$100
discount_pct = 20%

discount_amount = R$20

synthetic_paid_price = R$80
```

The original Olist `price` remains unchanged.

The synthetic price is stored as a separate derived field.

---

# 12. Discount Dependency Concept

The project defines discount dependency as a behavioral pattern in which a customer's modeled purchasing behavior becomes increasingly associated with promotional offers.

The project will investigate patterns such as:

```text
Repeated discount exposure
        ↓
Purchase behavior
        ↓
Full-price purchase behavior
        ↓
Customer value
```

Possible indicators include:

* Discount exposure count
* Discount exposure rate
* Repeat purchase rate
* Time between purchases
* Full-price purchase rate
* Discounted purchase rate
* Customer lifetime value
* Estimated contribution margin

These indicators will be used to create a customer-level discount dependency score or segment.

The exact scoring methodology will be defined during the feature-engineering stage.

---

# 13. Important Causal Limitation

The synthetic discount layer does not create genuine historical treatment assignment.

Therefore, the project must not claim:

```text
"Discount X caused customer behavior Y."
```

Instead, findings should be described as:

* Simulated relationships
* Modeled outcomes
* Scenario results
* Analytical estimates
* Hypothetical business outcomes

A real business would require randomized experimentation or appropriate causal-analysis methods to establish causal impact.

---

# 14. Product Cost Assumption

Olist does not provide actual product costs or COGS.

Therefore, product cost will be estimated using category-level margin assumptions.

The initial framework is:

| Margin Tier | Estimated Gross Margin | Estimated Cost Rate |
| ----------- | ---------------------: | ------------------: |
| High        |                    55% |                 45% |
| Medium      |                    40% |                 60% |
| Low         |                    25% |                 75% |

The estimated cost rate is calculated as:

```text
estimated_cost_rate =
    1 - estimated_gross_margin
```

---

# 15. High-Margin Assumption

For products classified as high-margin:

```text
estimated_gross_margin = 55%
estimated_cost_rate = 45%
```

Example:

```text
baseline_list_price = R$100

estimated_cogs =
    R$100 × 45%

estimated_cogs = R$45
```

This is an analytical estimate, not actual seller cost information.

---

# 16. Medium-Margin Assumption

For products classified as medium-margin:

```text
estimated_gross_margin = 40%
estimated_cost_rate = 60%
```

Example:

```text
baseline_list_price = R$100

estimated_cogs =
    R$100 × 60%

estimated_cogs = R$60
```

This is an analytical estimate.

---

# 17. Low-Margin Assumption

For products classified as low-margin:

```text
estimated_gross_margin = 25%
estimated_cost_rate = 75%
```

Example:

```text
baseline_list_price = R$100

estimated_cogs =
    R$100 × 75%

estimated_cogs = R$75
```

This assumption allows the project to investigate whether aggressive discounts are more dangerous for low-margin products.

---

# 18. Payment Fee Assumption

Olist does not provide a complete historical payment-fee field suitable for profitability analysis.

Therefore, payment fees will be modeled as an estimated percentage of the simulated paid price.

Initial assumption:

```text
estimated_payment_fee_rate = 3%
```

Calculation:

```text
estimated_payment_fee =
    synthetic_paid_price × 3%
```

Example:

```text
synthetic_paid_price = R$80

estimated_payment_fee =
    R$80 × 3%

estimated_payment_fee = R$2.40
```

This is an estimated assumption and not an actual Olist payment-processing fee.

---

# 19. Fulfillment Cost Assumption

Olist does not provide a complete fulfillment-cost field.

Therefore, fulfillment cost will initially be estimated using a simplified freight-based assumption.

Initial assumption:

```text
estimated_fulfillment_cost =
    freight_value
```

This is a simplified analytical proxy.

It should not be described as Olist's actual fulfillment cost.

A later sensitivity analysis may apply alternative fulfillment-cost assumptions.

---

# 20. Return Cost Assumption

Olist does not provide a complete explicit post-delivery return/refund dataset.

Therefore, actual return costs cannot be calculated directly.

For the initial model:

```text
estimated_return_cost = 0
```

This does not mean the business has no returns.

It means that the first version of the model does not estimate return costs because the required historical return data is unavailable.

Later scenarios may test:

```text
Scenario A → 0% return cost
Scenario B → 3% return cost
Scenario C → 5% return cost
```

These will be clearly identified as sensitivity scenarios.

---

# 21. Cancellation Assumption

Canceled orders must not be treated as customer returns.

The project distinguishes:

```text
Canceled order
≠
Post-delivery return
```

Canceled and unavailable orders will be excluded from successful delivered-order revenue analysis.

They may be analyzed separately for operational and cancellation insights.

---

# 22. Contribution Margin Assumption

The primary financial metric for promotion evaluation will be estimated contribution margin.

The initial formula is:

```text
estimated_contribution_margin =
    synthetic_paid_price
    + freight_value
    - estimated_cogs
    - estimated_payment_fee
    - estimated_fulfillment_cost
    - estimated_return_cost
```

Because:

```text
estimated_fulfillment_cost = freight_value
```

in the initial model, the freight component effectively nets out in the first version.

The formula is intentionally kept explicit so that assumptions can be changed later.

---

# 23. Contribution Margin Percentage

The estimated contribution margin percentage will be:

```text
estimated_margin_pct =
    estimated_contribution_margin
    / synthetic_paid_price
```

If:

```text
synthetic_paid_price = R$80
estimated_contribution_margin = R$20
```

then:

```text
estimated_margin_pct = 25%
```

---

# 24. Discount Economics

The project will not evaluate promotions using revenue alone.

For every simulated promotion, the analysis should consider:

```text
Revenue
+
Repeat purchase behavior
+
Customer lifetime value
-
Discount cost
-
Estimated costs
=
Contribution economics
```

The central business question is:

> Does the additional customer value generated by a promotion justify the margin sacrificed through discounting?

---

# 25. Customer Eligibility Assumptions

Promotion eligibility will be determined using customer purchase history available in the Olist dataset.

Examples:

### First-time customer

A customer whose first observed purchase occurs in the analysis period.

Potential promotion:

```text
WELCOME10
```

### Lapsed customer

A customer with at least 60 days since their previous observed purchase.

Potential promotion:

```text
LAPSED20
```

### Existing customer

A customer with previous purchase history who does not meet the lapsed threshold.

Potential treatment:

```text
FULL_PRICE
```

or another scenario depending on the simulation.

These classifications are project assumptions.

---

# 26. Discount Exposure Assumption

A customer is considered exposed to a simulated promotion when an eligible transaction is assigned a simulated promotion.

Example:

```text
promotion_id = WELCOME10
```

means:

```text
discount_exposure = 1
```

A no-offer transaction is:

```text
discount_exposure = 0
```

Customer-level exposure may later be aggregated as:

```text
discount_exposure_count
```

and:

```text
discount_exposure_rate
```

---

# 27. Discount Exposure Rate

The initial customer-level exposure rate will be calculated as:

```text
discount_exposure_rate =
    discounted_orders
    / eligible_orders
```

Example:

```text
eligible_orders = 10
discounted_orders = 4

discount_exposure_rate = 40%
```

This metric is used to understand how frequently a customer is modeled as receiving promotions.

---

# 28. Full-Price Purchase Rate

The project may calculate:

```text
full_price_purchase_rate =
    full_price_orders
    / eligible_orders
```

This helps identify whether customers continue purchasing without simulated promotions.

A lower full-price purchase rate combined with high discount exposure may indicate a potential discount-dependency pattern.

However, this remains a modeled behavioral indicator rather than proof of psychological or causal dependency.

---

# 29. Repeat Purchase Assumption

Repeat purchase behavior will be calculated using:

```text
customer_unique_id
```

rather than:

```text
customer_id
```

A repeat customer is a customer with more than one observed order in the relevant analysis period.

Example:

```text
customer_unique_id = ABC

Order 1
Order 2
Order 3
```

This represents:

```text
purchase_count = 3
```

---

# 30. Customer Lifetime Value Assumption

Customer lifetime value will be modeled using the contribution generated by the customer's observed and simulated purchases.

The initial conceptual formula is:

```text
customer_lifetime_value =
    SUM(estimated_contribution_margin)
```

This should be interpreted as modeled contribution value rather than accounting-based lifetime profit.

---

# 31. Scenario Analysis

The project will compare multiple promotion strategies.

At minimum, the analysis should include:

```text
Scenario 1 → FULL_PRICE
Scenario 2 → WELCOME10
Scenario 3 → LAPSED20
Scenario 4 → CATEGORY15
Scenario 5 → BLANKET30
```

Each scenario should be evaluated using metrics such as:

* Revenue
* Orders
* Repeat purchase rate
* Average order value
* Discount cost
* Estimated contribution margin
* Estimated margin percentage
* Customer lifetime value
* Discount exposure
* Full-price purchase rate

---

# 32. Sensitivity Analysis

Because several financial assumptions are estimated, the project should test whether business conclusions remain stable under alternative assumptions.

Potential sensitivity dimensions include:

```text
COGS rate
Payment fee rate
Fulfillment cost
Return cost
Discount percentage
Promotion eligibility
```

Example:

```text
COGS scenario:
45%
60%
75%
```

The objective is to determine whether the recommendation depends heavily on one assumption.

---

# 33. Assumption Governance

Every estimated or simulated field must have:

1. A documented definition.
2. A documented formula or rule.
3. A clear classification.
4. A reason for its inclusion.
5. A business interpretation.
6. A limitation statement where appropriate.

No hidden assumptions should be introduced in Python code.

---

# 34. Data Preservation Rule

The original Olist data must never be overwritten.

The project will maintain the following separation:

```text
data/raw/
    ↓
Original Olist CSV files
    ↓
Never modified
```

and:

```text
data/processed/
    ↓
Cleaned and enriched datasets
```

Synthetic and estimated fields will only be added to processed/enriched datasets.

---

# 35. Reproducibility Rule

All simulation rules must be reproducible.

The implementation must use:

```text
RANDOM_SEED = 42
```

and all important parameters should be defined centrally rather than scattered throughout the code.

The final project should make it possible for another analyst to understand:

```text
Which records were eligible?
Why were they eligible?
Which promotion was assigned?
What discount was applied?
Which costs were estimated?
How was contribution margin calculated?
```

---

# 36. Interpretation Rules

The project must use careful language when presenting results.

## Acceptable

```text
"Under the simulated 20% discount scenario..."
```

```text
"The modeled promotion group showed..."
```

```text
"Using the estimated cost assumptions..."
```

```text
"The scenario analysis suggests..."
```

## Not acceptable

```text
"Olist gave this customer a 20% discount."
```

```text
"The actual product cost was R$50."
```

```text
"The discount caused customers to purchase again."
```

```text
"Olist customers are addicted to discounts."
```

The analysis should describe modeled behavior rather than make unsupported historical or causal claims.

---

# 37. Final Assumption Framework

The project follows this structure:

```text
REAL OLIST DATA
       ↓
Observed transaction behavior
       ↓
Clean and validate
       ↓
Apply documented assumptions
       ↓
Create estimated economics
       ↓
Create simulated promotions
       ↓
Measure customer behavior
       ↓
Measure contribution economics
       ↓
Compare scenarios
       ↓
Create customer segments
       ↓
Recommend targeted promotion strategy
```

---

# Final Principle

The purpose of this assumptions document is to ensure that every analytical extension beyond the original Olist dataset is transparent and reproducible.

The project must always distinguish:

```text
WHAT OLIST ACTUALLY OBSERVED
              ↓
WHAT WE ESTIMATE
              ↓
WHAT WE SIMULATE
              ↓
WHAT THE SCENARIO ANALYSIS SUGGESTS
```

The final business recommendations must be based on the combination of observed transaction behavior, documented estimates, and explicitly simulated promotion scenarios.

The project must never present simulated discounts, estimated costs, or modeled relationships as historical facts from Olist.
