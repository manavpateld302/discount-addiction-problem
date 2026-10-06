# Olist Raw Data Dictionary

## Project Context

This project uses the Olist Brazilian E-Commerce dataset as its real transaction-data foundation.

The Olist dataset contains real historical e-commerce transaction records. However, it does not contain several fields required to directly study discount dependency.

Important limitation:

Olist does not contain actual historical:

* Discounts
* Promotion campaigns
* Original/list prices
* Product costs
* Marketing-channel attribution
* Explicit post-delivery customer returns
* Customer exposure to promotional campaigns

Therefore, these fields will be introduced later as clearly documented **estimated or simulated fields**.

No simulated or estimated field will be presented as if it were an original Olist observation.

---

# Customer Identifier Rule

For all customer-level analysis, use:

```text
customer_unique_id
```

This identifier should be used for:

* Repeat purchase analysis
* Customer lifetime value (CLV)
* Cohort analysis
* RFM segmentation
* Discount dependency analysis
* Customer purchase frequency
* Time between purchases

Do not use `customer_id` as the permanent customer identifier.

`customer_id` represents an order-level customer record, while `customer_unique_id` is the stable customer/person identifier.

---

# 1. Customers

**Raw file:**

```text
olist_customers_dataset.csv
```

**Grain:**

One customer record linked to one order.

**Primary identifier:**

```text
customer_id
```

**Customer-level identifier:**

```text
customer_unique_id
```

## Columns

| Column                     | Meaning                           | Planned Use                                |
| -------------------------- | --------------------------------- | ------------------------------------------ |
| `customer_id`              | Order-specific customer record ID | Join to orders                             |
| `customer_unique_id`       | Stable customer/person identifier | Repeat purchase, cohort, CLV, segmentation |
| `customer_zip_code_prefix` | Customer ZIP-code prefix          | Geography features                         |
| `customer_city`            | Customer city                     | Geography features                         |
| `customer_state`           | Customer state                    | Geography features                         |

## Important Note

A single `customer_unique_id` can be associated with multiple `customer_id` values.

Therefore, customer-level metrics must use:

```text
customer_unique_id
```

rather than:

```text
customer_id
```

---

# 2. Orders

**Raw file:**

```text
olist_orders_dataset.csv
```

**Grain:**

One row per order.

**Primary identifier:**

```text
order_id
```

**Customer join key:**

```text
customer_id
```

## Columns

| Column                          | Meaning                                   | Planned Use                           |
| ------------------------------- | ----------------------------------------- | ------------------------------------- |
| `order_id`                      | Unique order identifier                   | Main order key                        |
| `customer_id`                   | Customer record identifier                | Join to customers                     |
| `order_status`                  | Order lifecycle status                    | Delivered/canceled filtering          |
| `order_purchase_timestamp`      | Date and time when the order was placed   | Cohorts, repeat behavior, time trends |
| `order_approved_at`             | Date and time when payment was approved   | Payment/operations analysis           |
| `order_delivered_carrier_date`  | Date when order was handed to carrier     | Delivery analysis                     |
| `order_delivered_customer_date` | Date when order was delivered to customer | Delivery duration                     |
| `order_estimated_delivery_date` | Estimated delivery date                   | Late-delivery analysis                |

## Order Status Rule

For the primary revenue, repeat-purchase, and CLV analysis, the initial population will be:

```text
order_status = 'delivered'
```

Canceled and unavailable orders will be analyzed separately.

They must not be treated as successful completed revenue.

---

# 3. Order Items

**Raw file:**

```text
olist_order_items_dataset.csv
```

**Grain:**

One product item within an order.

**Primary identifier:**

```text
order_id + order_item_id
```

**Join keys:**

```text
order_id
product_id
seller_id
```

## Columns

| Column                | Meaning                                  | Planned Use           |
| --------------------- | ---------------------------------------- | --------------------- |
| `order_id`            | Order identifier                         | Join to orders        |
| `order_item_id`       | Sequence number of item within an order  | Creates line-item key |
| `product_id`          | Product identifier                       | Join to products      |
| `seller_id`           | Seller identifier                        | Join to sellers       |
| `shipping_limit_date` | Seller shipping deadline                 | Operations feature    |
| `price`               | Observed item selling price              | Revenue baseline      |
| `freight_value`       | Shipping charge associated with the item | Margin calculation    |

## Important Price Rule

The `price` column represents the observed item selling price in the Olist dataset.

It is **not confirmed to be**:

* Original list price
* Pre-discount price
* Promotional price
* Discounted price

Therefore, this project will not claim that the Olist `price` column represents a historical list price.

Later, the project may create synthetic fields such as:

```text
baseline_list_price
discount_pct
discount_amount
synthetic_paid_price
promotion_id
```

These fields will be clearly labeled as simulated or scenario-based fields.

---

# 4. Order Payments

**Raw file:**

```text
olist_order_payments_dataset.csv
```

**Grain:**

One payment method/transaction record within an order.

**Primary identifier:**

```text
order_id + payment_sequential
```

## Columns

| Column                 | Meaning                          | Planned Use               |
| ---------------------- | -------------------------------- | ------------------------- |
| `order_id`             | Order identifier                 | Join to orders            |
| `payment_sequential`   | Payment sequence within an order | Payment record identifier |
| `payment_type`         | Payment method                   | Payment behavior          |
| `payment_installments` | Number of installments           | Payment behavior          |
| `payment_value`        | Payment amount                   | Payment reconciliation    |

## Important Payment Rule

An order can contain more than one payment row.

Therefore, payment data must be aggregated when creating an order-level table.

For example:

```text
Order A
├── Payment 1 = R$50
└── Payment 2 = R$30
```

The order-level payment value becomes:

```text
R$80
```

Therefore:

```text
order_payment_value = SUM(payment_value)
```

---

# 5. Order Reviews

**Raw file:**

```text
olist_order_reviews_dataset.csv
```

**Grain:**

One review associated with an order.

**Primary identifier:**

```text
review_id
```

**Order join key:**

```text
order_id
```

## Columns

| Column                    | Meaning                          | Planned Use                    |
| ------------------------- | -------------------------------- | ------------------------------ |
| `review_id`               | Review identifier                | Review record key              |
| `order_id`                | Order identifier                 | Join to orders                 |
| `review_score`            | Customer rating from 1 to 5      | Customer satisfaction analysis |
| `review_comment_title`    | Review title                     | Optional future text analysis  |
| `review_comment_message`  | Review text                      | Optional future text analysis  |
| `review_creation_date`    | Date review was created          | Timing analysis                |
| `review_answer_timestamp` | Date/time seller answered review | Optional service analysis      |

## Important Review Rule

A missing review does not mean a bad review.

For example:

```text
review_score = NULL
```

means that a usable review score is not available.

It must not automatically be converted to:

```text
review_score = 0
```

or:

```text
review_score = 1
```

---

# 6. Products

**Raw file:**

```text
olist_products_dataset.csv
```

**Grain:**

One row per product.

**Primary identifier:**

```text
product_id
```

## Columns

| Column                       | Meaning                        | Planned Use                        |
| ---------------------------- | ------------------------------ | ---------------------------------- |
| `product_id`                 | Product identifier             | Join to order items                |
| `product_category_name`      | Product category in Portuguese | Category analysis                  |
| `product_name_lenght`        | Product-name length            | Optional product feature           |
| `product_description_lenght` | Product-description length     | Optional product feature           |
| `product_photos_qty`         | Number of product photos       | Optional product feature           |
| `product_weight_g`           | Product weight in grams        | Estimated fulfillment-cost feature |
| `product_length_cm`          | Product length in centimeters  | Optional logistics feature         |
| `product_height_cm`          | Product height in centimeters  | Optional logistics feature         |
| `product_width_cm`           | Product width in centimeters   | Optional logistics feature         |

---

# 7. Product Category Translation

**Raw file:**

```text
product_category_name_translation.csv
```

**Grain:**

One product-category translation record.

**Primary identifier:**

```text
product_category_name
```

## Columns

| Column                          | Meaning                  | Planned Use                    |
| ------------------------------- | ------------------------ | ------------------------------ |
| `product_category_name`         | Portuguese category name | Join to products               |
| `product_category_name_english` | English category name    | Dashboard and reporting labels |

## Important Rule

The English category name will primarily be used for:

* Dashboards
* Charts
* Business reporting
* Easier category interpretation

The original Portuguese category name will be retained where useful for data traceability.

---

# 8. Sellers

**Raw file:**

```text
olist_sellers_dataset.csv
```

**Grain:**

One row per seller.

**Primary identifier:**

```text
seller_id
```

## Columns

| Column                   | Meaning                | Planned Use                 |
| ------------------------ | ---------------------- | --------------------------- |
| `seller_id`              | Seller identifier      | Join to order items         |
| `seller_zip_code_prefix` | Seller ZIP-code prefix | Optional logistics analysis |
| `seller_city`            | Seller city            | Optional geography analysis |
| `seller_state`           | Seller state           | Optional geography analysis |

---

# 9. Geolocation

**Raw file:**

```text
olist_geolocation_dataset.csv
```

**Grain:**

Geographic observation associated with a ZIP-code prefix.

**Primary identifier:**

No guaranteed unique primary key.

## Columns

| Column                        | Meaning         | Planned Use             |
| ----------------------------- | --------------- | ----------------------- |
| `geolocation_zip_code_prefix` | ZIP-code prefix | Optional geography join |
| `geolocation_lat`             | Latitude        | Optional mapping        |
| `geolocation_lng`             | Longitude       | Optional mapping        |
| `geolocation_city`            | City name       | Optional mapping        |
| `geolocation_state`           | State name      | Optional mapping        |

## Important Rule

The geolocation table contains repeated ZIP-code prefixes.

Therefore, it will not be used in the first cleaning phase.

It may be introduced later if geographic analysis becomes important.

---

# Planned Project Tables

The raw Olist files will later be transformed into analysis-ready tables.

| Future Table           | Grain                        | Purpose                                                           |
| ---------------------- | ---------------------------- | ----------------------------------------------------------------- |
| `order_items_enriched` | One row per item in an order | Product, price, promotion, discount and estimated-margin analysis |
| `orders_enriched`      | One row per order            | Order economics, delivery, reviews, cancellation analysis         |
| `customer_features`    | One row per customer         | RFM, cohorts, CLV and discount dependency                         |
| `customer_segments`    | One row per customer         | Actionable customer segmentation                                  |

---

# Expected Data Flow

The overall project data flow will be:

```text
Raw Olist CSV files
        ↓
Clean base tables
        ↓
Enriched order/item tables
        ↓
Customer-level features
        ↓
Customer segmentation
        ↓
Discount dependency analysis
        ↓
Business recommendations
```

---

# Observed vs Estimated vs Simulated Fields

A major requirement of this project is to clearly distinguish actual Olist data from assumptions created by the project.

## Observed Fields

These fields exist directly in the original Olist dataset.

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
delivery dates
product category
```

These can be described as observed Olist data.

---

## Estimated Fields

These fields will be calculated later using documented assumptions.

Examples:

```text
estimated_cogs
estimated_payment_fee
estimated_fulfillment_cost
estimated_return_cost
estimated_contribution_margin
```

These are not actual Olist financial records.

They are analytical estimates created for the project.

---

## Simulated Fields

These fields will be created to model a realistic promotion scenario.

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

These are not historical Olist promotion records.

They are simulated scenario variables.

---

# Field Classification Rule

Every newly created field must belong to one of these categories:

```text
OBSERVED
ESTIMATED
SIMULATED
```

No estimated or simulated field will be presented as an observed Olist field.

---

# Key Business Questions Supported by the Data

After cleaning and feature engineering, the project will investigate questions such as:

## Customer Behavior

* How frequently do customers purchase?
* What percentage of customers make repeat purchases?
* How long does it take customers to purchase again?
* Which customers have high lifetime value?

## Discount Dependency

* Which customer segments are most responsive to simulated discounts?
* Do customers exposed to repeated discounts become less likely to purchase at full price?
* Which customers show signs of discount dependency?
* Does discount exposure correlate with purchase frequency?
* Which discount levels appear financially sustainable?

## Product Behavior

* Which categories are most sensitive to promotions?
* Which categories have stronger estimated margins?
* Which categories may be dangerous to discount heavily?

## Customer Economics

* Does increasing discount depth improve customer value?
* Does the additional purchase behavior compensate for lost margin?
* Which customers generate positive contribution margin after estimated costs?

## Business Strategy

* Which customers should receive discounts?
* Which customers should receive smaller discounts?
* Which customers should receive no discount?
* Where should a business use targeted promotions instead of blanket discounts?

---

# Analytical Limitations

The following limitations must remain visible throughout the project.

## 1. No Historical Discount Data

Olist does not provide actual historical discount percentages.

Therefore, discount dependency cannot be directly measured from observed Olist discount behavior.

A synthetic promotion layer will be used for scenario analysis.

---

## 2. No Historical Promotion Campaign Data

The dataset does not identify:

* Campaign IDs
* Coupon exposure
* Promotion dates
* Marketing channels
* Customer campaign targeting

Therefore, these fields will be simulated later.

---

## 3. No Product Cost Data

Olist does not provide seller product costs or COGS.

Therefore, profitability calculations will use estimated category-level cost assumptions.

---

## 4. No Explicit Post-Delivery Return Table

Olist does not provide a complete explicit customer return/refund dataset.

Canceled and unavailable orders will therefore be analyzed separately.

Cancellation must not be described as equivalent to a customer return.

---

## 5. No Direct Causal Evidence

Because the discount variable will be simulated, the project cannot claim:

```text
"Discount X caused customer behavior Y."
```

Instead, the project can discuss:

* Modeled relationships
* Scenario outcomes
* Business simulations
* Hypothetical experiment design

A real business would need randomized experimentation or appropriate causal-analysis methods to establish causal impact.

---

# Primary Analytical Population

For the main revenue and customer economics analysis:

```text
order_status = 'delivered'
```

Canceled and unavailable orders will be excluded from successful revenue calculations.

They may be analyzed separately for operational and cancellation insights.

---

# Data Quality Principles

The project will follow these principles:

1. Do not overwrite raw Olist data.
2. Keep raw CSV files unchanged.
3. Create cleaned tables separately.
4. Use documented transformations.
5. Preserve original identifiers.
6. Use `customer_unique_id` for customer-level analysis.
7. Distinguish observed, estimated and simulated data.
8. Do not silently invent missing business information.
9. Document assumptions before implementing them.
10. Validate cleaned tables before feature engineering.

---

# Raw-to-Analysis Mapping

The major relationships between the tables are:

```text
customers
    │
    │ customer_id
    ▼
orders
    │
    ├────────────── order_id ──────────────┐
    │                                      │
    ▼                                      ▼
order_items                         order_payments
    │
    ├── product_id ──→ products
    │
    └── seller_id ───→ sellers

orders
    │
    └── order_id ───→ order_reviews
```

The product category translation table connects to:

```text
products.product_category_name
        ↓
product_category_translation.product_category_name
        ↓
product_category_name_english
```

---

# Future Enrichment Layer

After the clean tables have been validated, the project may create additional fields.

## Promotion Fields

```text
promotion_id
discount_pct
discount_amount
synthetic_paid_price
is_discounted
```

## Cost Fields

```text
estimated_cogs
estimated_payment_fee
estimated_fulfillment_cost
estimated_return_cost
```

## Profitability Fields

```text
estimated_contribution_margin
estimated_margin_pct
```

## Customer Behavior Fields

```text
purchase_count
first_purchase_date
last_purchase_date
days_since_previous_purchase
average_order_value
customer_lifetime_value
discount_exposure_count
discount_exposure_rate
```

## Segmentation Fields

```text
rfm_segment
discount_dependency_segment
customer_value_segment
```

These fields will only be created after their definitions and assumptions have been documented.

---

# Final Data Dictionary Principle

The purpose of this document is not only to explain column names.

It establishes the analytical rules for the entire project.

The project must always distinguish between:

```text
WHAT OLIST ACTUALLY OBSERVED
              ↓
WHAT WE CALCULATE
              ↓
WHAT WE SIMULATE
```

This distinction is essential for producing a credible portfolio project and preventing unsupported business claims.
