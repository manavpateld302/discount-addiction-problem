# Customer Segmentation Rules

## RFM scores

Customers receive scores from 1 to 5.

- Recency score: 5 means most recently active.
- Frequency score: 5 means most delivered orders.
- Monetary score: 5 means highest total contribution margin.

## Segment priority

A customer receives the first segment whose rule they meet.

| Segment | Rule |
|---|---|
| New / one-order customer | Exactly one delivered order |
| At-risk / low engagement | At least two delivered orders, recency score of 1 or 2, and frequency score of 1 or 2 |
| Full-price loyalist | At least two delivered orders, frequency score at least 4, monetary score at least 3, and full-price order share at least 80% |
| Discount-dependent low-margin | At least two delivered orders, discount dependency score at least 60, full-price order share at most 50%, and average order margin below the portfolio median |
| Deal-responsive profitable | At least two delivered orders, used at least one discount, and average order margin at or above the portfolio median |
| Repeat generalist | Any remaining repeat customer |

## Important limitation

These are operational segments created from synthetic promotion fields and estimated margins. They are useful for scenario-based analysis, not proof that a real customer is psychologically dependent on discounts.