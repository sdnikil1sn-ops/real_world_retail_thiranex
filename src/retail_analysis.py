from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "retail_sales.csv"
OUTPUT_DIR = ROOT / "outputs"


def money(value: float) -> str:
    return f"Rs. {value:,.0f}"


def load_and_clean() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    df = df.drop_duplicates().copy()
    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")

    text_columns = ["region", "store_type", "category", "product"]
    for column in text_columns:
        df[column] = df[column].fillna("Unknown").astype(str).str.strip()

    numeric_columns = [
        "units_sold",
        "unit_price",
        "discount_percent",
        "inventory_level",
        "customer_rating",
    ]
    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")
        df[column] = df[column].fillna(df[column].median())

    df["discount_amount"] = (
        df["units_sold"] * df["unit_price"] * df["discount_percent"] / 100
    ).round(2)
    df["gross_revenue"] = (df["units_sold"] * df["unit_price"]).round(2)
    df["net_revenue"] = (df["gross_revenue"] - df["discount_amount"]).round(2)
    df["month"] = df["order_date"].dt.to_period("M").astype(str)
    df["stock_risk"] = pd.cut(
        df["inventory_level"],
        bins=[0, 60, 120, float("inf")],
        labels=["High", "Medium", "Low"],
        include_lowest=True,
    )
    return df.sort_values("order_date")


def create_summaries(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    monthly = df.groupby("month").agg(
        orders=("order_id", "count"),
        units_sold=("units_sold", "sum"),
        net_revenue=("net_revenue", "sum"),
        avg_rating=("customer_rating", "mean"),
    ).round(2)

    last_three_average = monthly["net_revenue"].tail(3).mean()
    forecast = pd.DataFrame(
        {
            "forecast_month": ["2026-09"],
            "method": ["3-month moving average"],
            "predicted_net_revenue": [round(last_three_average, 2)],
        }
    )

    return {
        "monthly_summary": monthly,
        "region_summary": df.groupby("region").agg(
            orders=("order_id", "count"),
            units_sold=("units_sold", "sum"),
            net_revenue=("net_revenue", "sum"),
            avg_rating=("customer_rating", "mean"),
        ).round(2),
        "category_summary": df.groupby("category").agg(
            orders=("order_id", "count"),
            units_sold=("units_sold", "sum"),
            net_revenue=("net_revenue", "sum"),
            avg_discount=("discount_percent", "mean"),
            avg_inventory=("inventory_level", "mean"),
        ).round(2),
        "store_type_summary": df.groupby("store_type").agg(
            orders=("order_id", "count"),
            net_revenue=("net_revenue", "sum"),
            avg_order_value=("net_revenue", "mean"),
        ).round(2),
        "forecast_summary": forecast,
    }


def save_outputs(df: pd.DataFrame, summaries: dict[str, pd.DataFrame]) -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    df.to_csv(OUTPUT_DIR / "cleaned_retail_sales.csv", index=False)
    for name, table in summaries.items():
        table.to_csv(OUTPUT_DIR / f"{name}.csv")


def bar_chart(title: str, series: pd.Series, color: str) -> str:
    values = series.astype(float)
    max_value = max(values.max(), 1)
    rows = []
    for label, value in values.items():
        width = 100 * value / max_value
        rows.append(
            f"""
            <div class="bar-row">
              <div class="bar-label">{label}</div>
              <div class="bar-track"><div class="bar-fill" style="width:{width:.1f}%; background:{color};"></div></div>
              <div class="bar-value">{money(value)}</div>
            </div>
            """
        )
    return f"<section><h2>{title}</h2>{''.join(rows)}</section>"


def line_chart(title: str, series: pd.Series) -> str:
    values = series.astype(float)
    max_value = max(values.max(), 1)
    width = 680
    height = 240
    step = width / max(len(values) - 1, 1)
    points = []
    labels = []

    for index, (label, value) in enumerate(values.items()):
        x = index * step
        y = height - (value / max_value * (height - 34)) - 12
        points.append(f"{x:.1f},{y:.1f}")
        labels.append(f'<text x="{x:.1f}" y="235" text-anchor="middle">{label}</text>')

    circles = "".join(
        f'<circle cx="{point.split(",")[0]}" cy="{point.split(",")[1]}" r="5"></circle>'
        for point in points
    )
    return f"""
    <section>
      <h2>{title}</h2>
      <svg viewBox="0 0 {width} {height}" role="img" aria-label="{title}">
        <polyline points="{' '.join(points)}"></polyline>
        {circles}
        {''.join(labels)}
      </svg>
    </section>
    """


def conclusions(df: pd.DataFrame, summaries: dict[str, pd.DataFrame]) -> str:
    top_region = summaries["region_summary"]["net_revenue"].idxmax()
    top_category = summaries["category_summary"]["net_revenue"].idxmax()
    top_store_type = summaries["store_type_summary"]["net_revenue"].idxmax()
    low_stock_count = int((df["stock_risk"] == "High").sum())
    forecast_value = float(summaries["forecast_summary"]["predicted_net_revenue"].iloc[0])

    items = [
        f"{top_region} is the strongest region by net revenue.",
        f"{top_category} is the leading category and should remain a priority for campaigns.",
        f"{top_store_type} sales generated the highest channel revenue.",
        f"{low_stock_count} records show high stock risk, so inventory planning needs attention.",
        f"The next-month revenue forecast is {money(forecast_value)} using a 3-month moving average.",
    ]
    return "".join(f"<li>{item}</li>" for item in items)


def build_report(df: pd.DataFrame, summaries: dict[str, pd.DataFrame]) -> str:
    total_revenue = float(df["net_revenue"].sum())
    total_units = int(df["units_sold"].sum())
    avg_rating = float(df["customer_rating"].mean())
    forecast_value = float(summaries["forecast_summary"]["predicted_net_revenue"].iloc[0])

    region_total = summaries["region_summary"]["net_revenue"].sort_values(ascending=False)
    category_total = summaries["category_summary"]["net_revenue"].sort_values(ascending=False)
    store_total = summaries["store_type_summary"]["net_revenue"].sort_values(ascending=False)
    monthly_total = summaries["monthly_summary"]["net_revenue"]

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Retail Sales Analysis Report</title>
  <style>
    body {{
      margin: 0;
      background: #f5f7fb;
      color: #172033;
      font-family: Arial, Helvetica, sans-serif;
      line-height: 1.5;
    }}
    main {{
      max-width: 1120px;
      margin: 0 auto;
      padding: 32px 20px 48px;
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: 32px;
    }}
    h2 {{
      margin: 0 0 18px;
      font-size: 20px;
    }}
    .subtitle {{
      margin: 0 0 24px;
      color: #586174;
    }}
    .metrics {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
      gap: 14px;
      margin: 24px 0;
    }}
    .metric, section {{
      background: #ffffff;
      border: 1px solid #dce3ef;
      border-radius: 8px;
      padding: 18px;
      box-shadow: 0 8px 20px rgba(23, 32, 51, 0.06);
    }}
    .metric span {{
      display: block;
      color: #586174;
      font-size: 13px;
    }}
    .metric strong {{
      display: block;
      margin-top: 8px;
      font-size: 22px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 18px;
    }}
    .bar-row {{
      display: grid;
      grid-template-columns: 120px 1fr 120px;
      gap: 12px;
      align-items: center;
      margin: 12px 0;
      font-size: 14px;
    }}
    .bar-track {{
      height: 14px;
      background: #e9edf5;
      border-radius: 999px;
      overflow: hidden;
    }}
    .bar-fill {{
      height: 100%;
      border-radius: 999px;
    }}
    .bar-value {{
      color: #39445a;
      text-align: right;
    }}
    svg {{
      width: 100%;
      height: auto;
    }}
    polyline {{
      fill: none;
      stroke: #2f6fed;
      stroke-width: 4;
    }}
    circle {{
      fill: #00a676;
      stroke: #ffffff;
      stroke-width: 2;
    }}
    text {{
      fill: #586174;
      font-size: 13px;
    }}
    ul {{
      margin: 0;
      padding-left: 20px;
    }}
    @media (max-width: 640px) {{
      .bar-row {{
        grid-template-columns: 1fr;
        gap: 6px;
      }}
      .bar-value {{
        text-align: left;
      }}
    }}
  </style>
</head>
<body>
  <main>
    <h1>Retail Sales Analysis Report</h1>
    <p class="subtitle">A real-world retail dataset analyzed for sales performance, inventory risk, and next-month revenue prediction.</p>
    <div class="metrics">
      <div class="metric"><span>Total net revenue</span><strong>{money(total_revenue)}</strong></div>
      <div class="metric"><span>Total units sold</span><strong>{total_units:,}</strong></div>
      <div class="metric"><span>Average rating</span><strong>{avg_rating:.1f}</strong></div>
      <div class="metric"><span>Next forecast</span><strong>{money(forecast_value)}</strong></div>
    </div>
    <section style="margin-bottom:18px;">
      <h2>Conclusions</h2>
      <ul>{conclusions(df, summaries)}</ul>
    </section>
    <div class="grid">
      {bar_chart("Net Revenue by Region", region_total, "#2f6fed")}
      {bar_chart("Net Revenue by Category", category_total, "#00a676")}
      {bar_chart("Net Revenue by Store Type", store_total, "#ef7b45")}
      {line_chart("Monthly Net Revenue Trend", monthly_total)}
    </div>
  </main>
</body>
</html>
"""


def main() -> None:
    df = load_and_clean()
    summaries = create_summaries(df)
    save_outputs(df, summaries)
    (OUTPUT_DIR / "retail_report.html").write_text(
        build_report(df, summaries),
        encoding="utf-8",
    )

    forecast = float(summaries["forecast_summary"]["predicted_net_revenue"].iloc[0])
    print(f"Rows analyzed: {len(df)}")
    print(f"Total net revenue: {money(float(df['net_revenue'].sum()))}")
    print(f"Next-month forecast: {money(forecast)}")
    print(f"Report written to: {OUTPUT_DIR / 'retail_report.html'}")


if __name__ == "__main__":
    main()

