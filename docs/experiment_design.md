# Experiment Design: Validating Discount Incrementality

## 1. Purpose

The scenario simulator identifies `TARGETED15` as the leading discount policy under the modeled Conservative, Base, and Optimistic scenarios. However, the simulator is scenario-based and does not establish that discounts cause incremental customer value.

The purpose of this experiment is to determine whether targeted discounting creates genuine incremental contribution margin compared with not offering a discount.

> Does offering a targeted 15% discount generate enough incremental customer value to justify the cost of the discount?

## 2. Business Hypothesis

### Primary hypothesis

Eligible customers who receive a targeted 15% discount generate higher incremental contribution margin over the measurement period than comparable eligible customers who do not receive the offer.

### Null hypothesis

The targeted 15% discount does not increase contribution margin per eligible customer compared with the control group.

### Secondary hypotheses

The experiment will also evaluate whether targeted discounting changes:

1. Purchase conversion.
2. Repeat purchase behavior.
3. Average order value.
4. Order frequency.
5. Customer contribution margin.
6. Value relative to discount cost.

## 3. Experimental Population

Eligibility rules should be defined and frozen before randomization. Example criteria include:

- At least one completed purchase.
- Eligibility to receive marketing offers.
- No overlapping promotion in the previous 30 days.
- No active support or refund-resolution flow.
- No high fraud or payment-failure risk.
- A valid customer identifier.
- Eligibility under the targeting model where applicable.

Customers should not be manually added or removed after randomization unless a predefined exclusion rule applies.

## 4. Experimental Arms

| Group | Treatment |
| --- | --- |
| Control | No discount offer |
| Blanket treatment | 30% discount |
| Targeted treatment | Targeted 15% discount |
| Targeted holdout | Target-eligible customer intentionally withheld from the offer |

### Control

The control group establishes baseline purchasing and contribution margin without a promotion.

### Blanket 30% treatment

This group tests whether broad discounting creates sufficient value. The current simulator suggests that this policy produces negative incremental contribution margin under the modeled scenarios.

### Targeted 15% treatment

Eligible customers satisfying the targeting criteria receive a 15% discount. This is the primary treatment of interest because the simulator identifies `TARGETED15` as the leading policy hypothesis.

### Targeted holdout

Some target-eligible customers are randomly withheld from receiving the offer. This estimates incrementality within the targetable audience and reduces selection bias.

## 5. Randomization

Randomization should occur at the customer level before treatment exposure. A possible allocation is:

| Group | Example allocation |
| --- | ---: |
| Control | 25% |
| Blanket 30% | 25% |
| Targeted 15% | 25% |
| Targeted holdout | 25% |

The final allocation should reflect power, business risk, and operational constraints. The randomization seed and assignment logic must be stored for reproducibility and auditability.

Recommended randomization strata include segment, tenure, purchase frequency, prior contribution margin, category affinity, geography, and acquisition channel where available.

## 6. Randomization Requirements

- Assign customers before treatment exposure.
- Do not assign based on post-treatment behavior.
- Keep each customer in the assigned group.
- Prevent conflicting promotional treatments.
- Log assignment and exposure events.
- Freeze the eligible population before analysis.
- Define exclusions before reviewing outcomes.

## 7. Primary Success Metric

### 90-Day Incremental Contribution Margin per Eligible Customer

```text
Contribution Margin per Eligible Customer
= Total Contribution Margin / Number of Eligible Customers

Incremental Contribution Margin
= Treatment Margin per Eligible Customer
  - Control Margin per Eligible Customer
```

The denominator must include all eligible assigned customers, not only redeemers. Contribution margin is preferred to revenue or order count because a discount can increase sales while reducing profitability.

## 8. Secondary Metrics

- **14-day conversion:** customers with a purchase within 14 days divided by eligible customers.
- **Order frequency:** total orders divided by eligible customers.
- **Average order value:** revenue divided by orders.
- **Discount cost:** total discount value provided to treatment customers.
- **Contribution margin:** revenue after discount and relevant costs.
- **Repeat purchase rate:** eligible customers making another purchase in the specified period.
- **90-day customer value:** observed contribution margin during the first 90 days.
- **180-day CLV:** longer-term follow-up value where available.

## 9. Measurement Window

The primary measurement window is 90 days from assignment or the defined experiment start point. This captures immediate purchase response and early repeat behavior. The existing descriptive analysis uses 180-day repeat behavior and realized CLV, so 180 days should remain a secondary observation window.

Enrollment and follow-up should be planned separately:

```text
Enrollment -> Random assignment -> Offer exposure -> 90-day measurement -> Final analysis
```

## 10. Incrementality Framework

The central targeted comparison is:

```text
Targeted 15% treatment - Targeted eligible holdout
```

The blanket comparison is:

```text
Blanket 30% treatment - No-offer control
```

These comparisons estimate the value of sending each offer to customers who were eligible for that decision.

## 11. Why Randomization Matters

Customers who naturally receive discounts may differ from customers who do not. They may be more price-sensitive, less frequent purchasers, more engaged, or different in product preference.

```text
Observed difference != Causal discount effect
```

Randomization makes groups comparable on average before treatment and provides a more reliable causal estimate.

## 12. Guardrail Metrics

Guardrails should not replace the primary margin metric. Monitor:

- Cancellation and return/refund rate.
- Average discount value per customer.
- Order margin.
- Customer service contacts and complaints.
- Unsubscribe rate.
- Promotion abuse or unusual redemption.
- Revenue per eligible customer.
- Seller capacity and fulfillment constraints.
- Order frequency and full-price purchasing.

Positive revenue is not sufficient if a treatment materially damages another important business metric.

## 13. Treatment Contamination

Track assigned treatment separately from actual exposure. Contamination examples include a control customer receiving a targeted coupon, a targeted customer receiving another offer, or a customer receiving overlapping promotions.

The exposure table should contain at least:

| Field | Description |
| --- | --- |
| `customer_id` | Customer identifier |
| `experiment_id` | Experiment identifier |
| `assigned_group` | Randomized treatment group |
| `offer_sent` | Whether the offer was delivered |
| `offer_redeemed` | Whether the offer was used |
| `assignment_timestamp` | Time of assignment |
| `exposure_timestamp` | Time of treatment exposure |

## 14. Intention-to-Treat Analysis

The primary analysis must follow intention-to-treat. Customers are analyzed according to their assigned group, even if they do not open, click, or redeem the offer. This preserves the benefits of randomization and estimates the value of the decision to send an offer.

## 15. Treatment-on-the-Treated Analysis

A secondary analysis may examine customers who received or redeemed the offer, but it must not replace intention-to-treat. Redeemers are self-selected and may differ systematically from non-redeemers.

## 16. Statistical Analysis

Estimate the difference in mean 90-day contribution margin per eligible customer:

```text
ATE = Mean(Y | Treatment) - Mean(Y | Control)

Y = 90-day contribution margin per eligible customer
```

Report:

- Treatment effect.
- Confidence interval.
- Statistical significance.
- Sample size.
- Mean outcome in each group.
- Business and statistical significance.

A statistically significant result may still be too small to justify operational complexity.

## 17. Sample Size and Power

Determine sample size before launch using:

- Baseline contribution margin.
- Expected variance.
- Minimum detectable effect.
- Desired power.
- Significance level.
- Expected attrition and contamination.

A typical planning framework is 5% significance and 80% power. These are planning assumptions, not results from the current project.

## 18. Minimum Detectable Effect

Define the minimum detectable effect in business terms:

> What is the smallest incremental contribution margin per eligible customer that would justify implementing the targeted discount?

The MDE should incorporate discount cost, operational complexity, expected customer value, scale, and opportunity cost. Success requires an effect that is both statistically credible and economically meaningful.

## 19. Experiment Duration

Run the experiment long enough to reach the required sample size and capture the primary 90-day outcome. Do not stop early because one treatment temporarily appears better. A longer 180-day follow-up can measure retention and CLV.

## 20. Analysis Segments

The primary analysis should use the full randomized population. Exploratory subgroup analyses may examine:

- New / one-order customer.
- Deal-responsive profitable.
- Full-price loyalist.
- Repeat generalist.
- Discount-dependent low-margin.
- At-risk / low engagement where represented.

Subgroup findings are exploratory unless hypotheses and segments were pre-registered and sample sizes are sufficient.

## 21. Decision Rules

### Launch or scale targeted discount

Consider deployment only if `TARGETED15`:

1. Produces positive incremental 90-day contribution margin.
2. Has a confidence interval supporting a meaningful positive effect.
3. Maintains acceptable guardrails.
4. Is economically meaningful.
5. Is operationally feasible.

### Do not launch

Do not deploy if incremental margin is negative, the interval is inconsistent with a meaningful positive effect, guardrails deteriorate materially, or discount costs exceed incremental value.

### Continue testing

Continue if the estimated effect is positive but uncertain, the interval is wide, sample size is insufficient, or results vary materially across important segments.

## 22. Expected Interpretation of Possible Outcomes

| Outcome | Interpretation |
| --- | --- |
| Higher orders and higher margin | Evidence for incremental value |
| Higher orders and lower margin | Discount creates volume but damages economics |
| No order increase and lower margin | Economically unattractive discount |
| No meaningful difference | Discount may not create incremental value |
| Positive overall effect but negative low-margin segment effect | Consider tighter targeting |
| Positive targeted effect and negative blanket effect | Supports targeted rather than broad discounting |

## 23. Relationship to the Current Simulator

The simulator is a scenario-planning tool. It currently identifies:

```text
TARGETED15 -> Leading modeled policy hypothesis
```

The experiment tests whether that recommendation is supported by real customer behavior:

```text
Simulator -> Hypothesis -> Experiment -> Observed incremental effect -> Business decision
```

The simulator must not be presented as evidence that the treatment will succeed in production.

## 24. Data Requirements for the Real Experiment

### Customer

- `customer_id`
- Eligibility status.
- Customer segment.

### Experiment

- `experiment_id`
- Assignment group.
- Assignment timestamp.
- Randomization seed or reproducible assignment logic.

### Promotion

- Offer type and discount percentage.
- Offer sent and redeemed.
- Redemption timestamp.
- Discount amount.

### Orders and economics

- `order_id`, `customer_id`, order timestamp, and order value.
- Revenue, discount cost, product cost, and contribution margin.

### Follow-up

- Repeat orders, repeat revenue, repeat contribution margin.
- 90-day and 180-day customer value.

## 25. Experiment Data Model

A simplified example structure is:

| customer_id | assigned_group | offer_pct | orders_90d | revenue_90d | discount_cost | contribution_margin_90d |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| C001 | CONTROL | 0 | 1 | 100 | 0 | 30 |
| C002 | TARGETED15 | 15 | 2 | 210 | 31.50 | 42 |
| C003 | BLANKET30 | 30 | 2 | 220 | 66 | 20 |
| C004 | TARGETED_HOLDOUT | 0 | 1 | 105 | 0 | 32 |

This is an example structure only. It is not observed experiment data from Olist.

## 26. Reporting Template

The final experiment report should contain:

### Executive result

- Treatment effect.
- Confidence interval.
- P-value.
- Sample size.
- Business interpretation.

### Economics

- Revenue impact.
- Discount cost.
- Contribution margin impact.
- Incremental contribution margin per eligible customer.

### Customer behavior

- Conversion.
- Orders.
- Repeat rate.
- Average order value.

### Guardrails

- Returns.
- Cancellations.
- Customer service impact.
- Promotion abuse.

### Recommendation

One of:

```text
Launch
Do not launch
Continue testing
```

## 27. Final Decision Framework

```text
Scenario model
      |
      v
TARGETED15: leading hypothesis
      |
      v
Randomized test
      |
  +---+---+
  |       |
  v       v
Treatment Holdout
  |       |
  +---+---+
      |
      v
90-day contribution margin
      |
      v
Incremental effect
  +---+---+
  |       |
  v       v
Positive Negative
  |       |
  v       v
Evaluate  Do not
scale     launch
```

## 28. Final Recommendation

The current project should not claim that discounts have been proven causal.

> The scenario analysis identifies targeted 15% discounting as the leading policy hypothesis because it produces the highest modeled incremental contribution margin while avoiding the substantial margin loss associated with blanket discounting.

> The next business action is to validate this hypothesis through a randomized experiment using 90-day incremental contribution margin per eligible customer as the primary metric.

This preserves the distinction between observed data, scenario assumptions, model output, causal evidence, and business decision.
