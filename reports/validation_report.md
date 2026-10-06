# Clean Table Validation Report

This report was generated automatically by `src/validate_clean_tables.py`.

## Validation results

| check_name                                            | result   | value                                | notes                                                                                                    |
|:------------------------------------------------------|:---------|:-------------------------------------|:---------------------------------------------------------------------------------------------------------|
| customers_clean has rows                              | PASS     | 99,441                               | A clean table should not be empty.                                                                       |
| orders_clean has rows                                 | PASS     | 99,441                               | A clean table should not be empty.                                                                       |
| order_items_clean has rows                            | PASS     | 112,650                              | A clean table should not be empty.                                                                       |
| products_clean has rows                               | PASS     | 32,951                               | A clean table should not be empty.                                                                       |
| payments_clean has rows                               | PASS     | 99,440                               | A clean table should not be empty.                                                                       |
| reviews_clean has rows                                | PASS     | 98,673                               | A clean table should not be empty.                                                                       |
| orders_clean: order_id is unique                      | PASS     | 0 duplicate order IDs                | There must be one row per order in orders_clean.                                                         |
| order_items_clean: order_id + order_item_id is unique | PASS     | 0 duplicate item keys                | Each item sequence should occur only once within an order.                                               |
| customers_clean: customer_id is unique                | PASS     | 0 duplicate customer IDs             | customer_id is an order-level customer record key.                                                       |
| products_clean: product_id is unique                  | PASS     | 0 duplicate product IDs              | There must be one row per product.                                                                       |
| orders_clean: customer_unique_id populated            | PASS     | 0 missing values                     | customer_unique_id is required for repeat purchase and CLV analysis.                                     |
| order_items_clean: no negative observed item prices   | PASS     | 0 negative values                    | Negative product prices would invalidate revenue calculations.                                           |
| order_items_clean: no negative freight values         | PASS     | 0 negative values                    | Negative freight values would invalidate cost calculations.                                              |
| delivered orders identified                           | PASS     | 96,478 delivered orders              | Delivered orders will be the primary population for revenue and CLV.                                     |
| canceled/unavailable orders identified                | PASS     | 1,234 canceled or unavailable orders | These orders must not be counted as successful revenue.                                                  |
| order items with unknown product category             | WARNING  | 1,627 line items                     | Unknown categories are expected for some products and will remain labeled 'unknown'.                     |
| orders with a review score                            | PASS     | 98,673 reviewed orders               | A review is optional; missing reviews should not be treated as bad reviews.                              |
| total observed item revenue                           | INFO     | R$13,591,643.70                      | Raw Olist item-price total before synthetic promotions.                                                  |
| total observed freight value                          | INFO     | R$2,251,909.54                       | Raw Olist freight total.                                                                                 |
| total aggregated payment value                        | INFO     | R$16,008,872.12                      | Payment value can differ from item price plus freight due to vouchers, installments, and data structure. |

## Interpretation

- `PASS`: the expected rule was met.
- `WARNING`: investigate or document the condition; it is not necessarily an error.
- `FAIL`: stop and fix the issue before moving forward.
- `INFO`: descriptive business total, not a pass/fail rule.