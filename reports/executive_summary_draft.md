# Executive Summary Draft

## Business question

Do discounts create incremental long-term customer value, or do they primarily subsidize purchases that would otherwise happen at full price?

## Draft recommendation

Under the base-case scenario, **TARGETED15** produces the highest estimated incremental contribution margin versus no offer.

- Expected incremental margin versus no offer: **R$62.24**
- Expected discount cost: **R$461.59**
- Customers offered: **115**

This recommendation should be treated as a scenario-based decision input and validated with a randomized holdout experiment.

## First-order cohort comparison

- Full-price first-order cohort: **3.12%** 180-day repeat rate; **R$67.47** average realized 180-day CLV.
- Discounted first-order cohorts combined: **3.10%** 180-day repeat rate; **R$55.42** average realized 180-day CLV.

## Most valuable segment

**New / one-order customer** generates the largest total estimated contribution margin:

- Customers: **90,557**
- Average order margin: **R$58.64**
- Total contribution margin: **R$5,310,146.27**

## Simulator results

| scenario   |   customers_offered |   expected_orders |   expected_discount_cost |   expected_contribution_margin |   incremental_margin_vs_no_offer |
|:-----------|--------------------:|------------------:|-------------------------:|-------------------------------:|---------------------------------:|
| BLANKET30  |               93358 |           2477.53 |                 93852.2  |                        63950.9 |                        -47943.5  |
| NO_OFFER   |                   0 |           1852.95 |                     0    |                       111894   |                             0    |
| TARGETED15 |                 115 |           1863.58 |                   461.59 |                       111957   |                            62.24 |

## Segment economics

| customer_segment              |   customer_count |   average_discount_dependency_score |   average_order_margin |   total_contribution_margin |
|:------------------------------|-----------------:|------------------------------------:|-----------------------:|----------------------------:|
| New / one-order customer      |            90557 |                               37.11 |                  58.64 |                 5.31015e+06 |
| Deal-responsive profitable    |             1138 |                               39.53 |                  77.56 |            186976           |
| Full-price loyalist           |              577 |                                0.13 |                  60.67 |             74475.8         |
| Repeat generalist             |              795 |                               28.85 |                  23.84 |             40481           |
| Discount-dependent low-margin |              291 |                               74.5  |                  22.52 |             13286           |

## First-order cohort results

| first_order_discount_band   |   customer_count |   repeat_rate_180_days |   average_realized_clv_180 |
|:----------------------------|-----------------:|-----------------------:|---------------------------:|
| 0% (Full price)             |            16780 |                   3.12 |                      67.47 |
| 1–10%                       |            36103 |                   3.04 |                      54.96 |
| 11–15%                      |             3024 |                   3.8  |                      61    |

## Key limitations

- Olist does not contain observed historical promotion campaigns, true product cost, or explicit return events.
- Discount, promotion, and margin fields are documented synthetic/estimated scenario fields.
- The cohort and regression outputs are descriptive; they do not establish causal discount impact.
- The simulator depends on transparent elasticity assumptions and should be tested through a real randomized experiment.

## Recommended next action

Run a randomized test with no-offer control, 30% blanket treatment, 15% targeted treatment, and a targeted holdout. Use incremental 90-day contribution margin per eligible customer as the primary decision metric.