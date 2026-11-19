# Power BI ready sales example

This folder is a small, messy Indian sales file and a saved v2 recipe. The script previews the recipe, applies that reviewed plan, and writes tables you can load into Power BI.

It prepares model inputs. It does not create a `.pbix` file, visuals, measures, or a dashboard.

## What is messy in `sales.csv`

- Amounts use `₹` and thousands separators. Two amounts are blank or `n/a`.
- Dates are mostly `dd/mm/yyyy`. Two rows use another format: `2025-03-01` and `15-Jan-2025`.
- City names mix codes, spelling, case, and a padded value: `HYD`, `Hyd`, `BLR`, `Bangalore`, `mumbai`, `DEL`.
- Order `1001` is duplicated.
- `Customer ID` values such as `001` need to stay text.

## Run it

From the repository root:

```bash
python examples/power_bi_ready/prepare.py --output examples/power_bi_ready/output
```

The script loads `recipe.json`, previews `sales.csv`, and applies that same plan. Preview does not modify the source file.

## What the recipe does

`recipe.json` is a `powerbi_ready` recipe:

- `order_id` and `customer_id` stay text, so leading zeroes are kept.
- `amount` is a number. `₹` and commas are removed. Blank and `n/a` stay null.
- `order_date` must match `%d/%m/%Y`. Other formats are quarantined, not guessed.
- City aliases map to one name each: Hyderabad, Bengaluru, Mumbai, and New Delhi.
- Exact duplicate rows are removed after conversion.
- `order_id` is the sales key.
- A continuous `date` table is built from the valid order dates. April is fiscal month 1, so 15 January 2025 is fiscal year 2025 and fiscal month 10.

## What Power BI gets

In the output directory:

| File | Contents |
| --- | --- |
| `powerbi_ready_sales.csv` | Eight ready orders. |
| `powerbi_ready_date.csv` | One row per day from 15 January 2025 through 3 February 2025. |
| `powerbi_ready.xlsx` | Both tables as sheets. |
| `powerbi_ready_readiness.json` | Field types, the score, and the date relationship. |
| `pipeline_report.json` | The stage-by-stage change log. |
| `sales_rejected.csv` | Orders `1004` and `1005`, kept out because their dates do not match `%d/%m/%Y`. |
| `recipe.json` | The recipe that produced this run. |

Sales field types are Text for the ids, city, and channel, Date for `order_date`, and Decimal Number for `amount`. The date table uses Date, whole numbers, text month names, and a true/false weekend flag. `sales.order_date` relates many-to-one to `date.date`.

The change log records heading cleanup, the two null amounts, city renames, two quarantined dates, one removed duplicate, and the Power BI type pass. Rows that were quarantined are not in the sales table.

Load the CSV or Excel files into Power BI. Check the types against `powerbi_ready_readiness.json` before you build visuals. If a source date format changes, update `date_format` and review a new preview. This recipe will not silently accept a second format.
