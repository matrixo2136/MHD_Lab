from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mhd_utils import read_online_retail, prepare_online_retail, output_dir, save_text

OUT = output_dir("LAB6")
df = prepare_online_retail(read_online_retail())

pivot = pd.pivot_table(df, values="Revenue", index="Country", columns="Month", aggfunc="sum", fill_value=0)
month_ranking = df.groupby("Month", as_index=False)["Revenue"].sum().sort_values("Revenue", ascending=False)
country_ranking = df.groupby("Country", as_index=False)["Revenue"].sum().sort_values("Revenue", ascending=False)
top10_countries = country_ranking.head(10)
customers = df.groupby("CustomerID", as_index=False)["Revenue"].sum().sort_values("Revenue", ascending=False)
top10_customers = customers.head(10)
avg_customer_revenue = customers["Revenue"].mean()

q25 = country_ranking["Revenue"].quantile(0.25)
q75 = country_ranking["Revenue"].quantile(0.75)
country_ranking["Segment"] = country_ranking["Revenue"].apply(lambda x: "Top 25%" if x >= q75 else ("Dolne 25%" if x <= q25 else "Środkowe 50%"))
segment_summary = country_ranking.groupby("Segment", as_index=False).agg(countries=("Country", "count"), revenue=("Revenue", "sum"))

pivot.to_csv(OUT / "task1_pivot_country_month.csv")
month_ranking.to_csv(OUT / "task1_month_ranking.csv", index=False)
top10_countries.to_csv(OUT / "task2_top10_countries.csv", index=False)
customers.to_csv(OUT / "task3_customer_revenue.csv", index=False)
top10_customers.to_csv(OUT / "task3_top10_customers.csv", index=False)
country_ranking.to_csv(OUT / "task4_country_segments.csv", index=False)
segment_summary.to_csv(OUT / "task4_segment_summary.csv", index=False)

plt.figure(figsize=(10, 5))
plt.bar(top10_countries["Country"], top10_countries["Revenue"])
plt.xticks(rotation=45, ha="right")
plt.title("TOP 10 krajów według przychodu")
plt.tight_layout()
plt.savefig(OUT / "chart_top10_countries.png")
plt.close()

plt.figure(figsize=(10, 5))
plt.plot(month_ranking.sort_values("Month")["Month"], month_ranking.sort_values("Month")["Revenue"], marker="o")
plt.title("Sprzedaż według miesięcy")
plt.tight_layout()
plt.savefig(OUT / "chart_monthly_revenue.png")
plt.close()

conclusions = f"""
Najważniejsze kraje to przede wszystkim: {', '.join(top10_countries['Country'].head(3).tolist())}.
Sprzedaż nie jest równomierna między krajami, ponieważ najwyżej sklasyfikowane kraje generują największą część przychodu.
Najlepszy miesiąc sprzedażowy to miesiąc {int(month_ranking.iloc[0]['Month'])}.
Średni przychód na klienta wynosi {avg_customer_revenue:.2f}.
"""
save_text(OUT / "task5_conclusions.txt", conclusions)
print("LAB6 zakończone. Wyniki zapisano w LAB6/output.")
