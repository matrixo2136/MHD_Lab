from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))

import pandas as pd
from mhd_utils import read_sales_raw, output_dir, save_text

OUT = output_dir("LAB1")

df = read_sales_raw()
df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
df["total_value"] = df["quantity"] * df["unit_price"]
df["year"] = df["order_date"].dt.year

sales_by_country = df.groupby("country", as_index=False)["total_value"].sum().sort_values("total_value", ascending=False)
sales_by_product = df.groupby("product_name", as_index=False)["total_value"].sum().sort_values("total_value", ascending=False)
sales_by_year = df.groupby("year", as_index=False)["total_value"].sum().sort_values("year")
sales_aggregated = df.groupby(["country", "year"], as_index=False)["total_value"].sum()
high_value = df[df["total_value"] > 1000].copy()
high_value_count = high_value.groupby("country").size().reset_index(name="transaction_count")

sales_aggregated.to_csv(OUT / "sales_aggregated.csv", index=False)
sales_by_country.to_csv(OUT / "sales_by_country.csv", index=False)
sales_by_product.to_csv(OUT / "sales_by_product.csv", index=False)
sales_by_year.to_csv(OUT / "sales_by_year.csv", index=False)
high_value.to_csv(OUT / "high_value_sales.csv", index=False)
high_value_count.to_csv(OUT / "high_value_count_by_country.csv", index=False)

summary = f"""
LAB1 wykonano poprawnie.
Liczba rekordów: {len(df)}
Łączna wartość sprzedaży: {df['total_value'].sum():.2f}
Liczba transakcji powyżej 1000: {len(high_value)}
"""
save_text(OUT / "summary.txt", summary)
print(summary)
