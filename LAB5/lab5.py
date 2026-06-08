from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mhd_utils import read_online_retail, read_online_retail_ii, prepare_online_retail, output_dir, save_text

OUT = output_dir("LAB5") / "olap"
OUT.mkdir(exist_ok=True)

parts = [read_online_retail()]
second = read_online_retail_ii()
if second is not None:
    parts.append(second)

df = prepare_online_retail(pd.concat(parts, ignore_index=True))

rollup = df.groupby("Year", as_index=False)["Revenue"].sum()
drilldown = df.groupby(["Year", "Month"], as_index=False)["Revenue"].sum()
slice_uk = df[df["Country"] == "United Kingdom"]
dice_uk_2011 = df[(df["Country"] == "United Kingdom") & (df["Year"] == 2011)]
pivot_country_year = pd.pivot_table(df, values="Revenue", index="Country", columns="Year", aggfunc="sum", fill_value=0)

top10_countries = df.groupby("Country", as_index=False)["Revenue"].sum().sort_values("Revenue", ascending=False).head(10)
month_sales = df.groupby(["Year", "Month"], as_index=False)["Revenue"].sum().sort_values("Revenue", ascending=False)
cube_country_month = pd.pivot_table(df, values="Revenue", index="Country", columns="Month", aggfunc="sum", fill_value=0)
year_country = df.groupby(["Country", "Year"], as_index=False)["Revenue"].sum()
best_year = year_country.loc[year_country.groupby("Country")["Revenue"].idxmax()].sort_values("Country")
product_country = df.groupby(["Country", "StockCode", "Description"], as_index=False)["Revenue"].sum()
top5_products = product_country.sort_values(["Country", "Revenue"], ascending=[True, False]).groupby("Country").head(5)

rollup.to_csv(OUT / "rollup_sales_by_year.csv", index=False)
drilldown.to_csv(OUT / "drilldown_sales_by_year_month.csv", index=False)
slice_uk.groupby(["Year", "Month"], as_index=False)["Revenue"].sum().to_csv(OUT / "slice_uk_monthly.csv", index=False)
dice_uk_2011.groupby("Month", as_index=False)["Revenue"].sum().to_csv(OUT / "dice_uk_2011_monthly.csv", index=False)
pivot_country_year.to_csv(OUT / "pivot_country_year.csv")
top10_countries.to_csv(OUT / "task1_top10_countries.csv", index=False)
month_sales.head(1).to_csv(OUT / "task2_best_month.csv", index=False)
cube_country_month.to_csv(OUT / "task3_cube_country_month.csv")
best_year.to_csv(OUT / "task4_best_year_by_country.csv", index=False)
top5_products.to_csv(OUT / "task5_top5_products_by_country.csv", index=False)

heatmap_data = cube_country_month.loc[top10_countries["Country"]]
plt.figure(figsize=(12, 6))
plt.imshow(heatmap_data.values, aspect="auto")
plt.xticks(range(len(heatmap_data.columns)), heatmap_data.columns)
plt.yticks(range(len(heatmap_data.index)), heatmap_data.index)
plt.colorbar(label="Revenue")
plt.title("Sprzedaż według kraju i miesiąca")
plt.tight_layout()
plt.savefig(OUT / "bonus_heatmap.png")
plt.close()

notes = """
Roll-up pokazuje agregację do poziomu roku.
Drill-down zwiększa szczegółowość do roku i miesiąca.
Slice wybiera jeden wymiar, np. United Kingdom.
Dice filtruje wiele wymiarów jednocześnie, np. kraj i rok.
Pivot pełni rolę prostej kostki OLAP.
"""
save_text(OUT / "olap_notes.txt", notes)
print("LAB5 zakończone. Wyniki zapisano w LAB5/output/olap.")
