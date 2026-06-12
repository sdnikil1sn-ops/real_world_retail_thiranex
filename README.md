# Real-world Data Project: Retail Sales Analysis

This project uses a retail sales dataset to perform end-to-end applied data analysis and simple sales prediction.

## Key Features

- Uses a domain-specific retail dataset.
- Cleans and prepares sales, discount, inventory, and customer-rating data.
- Analyzes revenue by region, product category, store type, and month.
- Builds a simple moving-average forecast for the next month.
- Presents findings, visualizations, and conclusions in an HTML report.

## Project Structure

```text
data/
  retail_sales.csv
outputs/
  cleaned_retail_sales.csv
  category_summary.csv
  monthly_summary.csv
  region_summary.csv
  forecast_summary.csv
  retail_report.html
src/
  retail_analysis.py
```

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
python src/retail_analysis.py
```

## Expected Outcome

After running the project, you will have cleaned retail data, summary CSV files, a simple forecast, and a report explaining sales performance and business conclusions.

