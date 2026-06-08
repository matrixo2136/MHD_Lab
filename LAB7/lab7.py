from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))

import time
import pandas as pd
from mhd_utils import require_file, output_dir, save_text

OUT = output_dir("LAB7") / "optimization"
OUT.mkdir(exist_ok=True)

start = time.perf_counter()
df = pd.read_csv(require_file("Online_Retail.csv"), encoding="ISO-8859-1")
load_time = time.perf_counter() - start

missing = df.isna().sum().reset_index()
missing.columns = ["column", "missing_values"]
missing.to_csv(OUT / "missing_values.csv", index=False)
df.dtypes.astype(str).reset_index().rename(columns={"index": "column", 0: "dtype"}).to_csv(OUT / "dtypes_before.csv", index=False)

base = df.copy()
base["InvoiceDate"] = pd.to_datetime(base["InvoiceDate"], errors="coerce")
base["Quantity"] = pd.to_numeric(base["Quantity"], errors="coerce")
base["UnitPrice"] = pd.to_numeric(base["UnitPrice"], errors="coerce")
base = base.dropna(subset=["CustomerID", "InvoiceDate", "Quantity", "UnitPrice"])
base = base[(base["Quantity"] > 0) & (base["UnitPrice"] > 0)]
base = base.drop_duplicates().copy()
base["CustomerID"] = base["CustomerID"].astype(int)
base["Revenue"] = base["Quantity"] * base["UnitPrice"]
base["Month"] = base["InvoiceDate"].dt.month

optimized = base.copy()
for col in ["InvoiceNo", "StockCode", "Description", "Country"]:
    optimized[col] = optimized[col].astype("category")
optimized["Quantity"] = pd.to_numeric(optimized["Quantity"], downcast="integer")
optimized["UnitPrice"] = pd.to_numeric(optimized["UnitPrice"], downcast="float")
optimized["Revenue"] = pd.to_numeric(optimized["Revenue"], downcast="float")
optimized["CustomerID"] = pd.to_numeric(optimized["CustomerID"], downcast="integer")
optimized["Month"] = pd.to_numeric(optimized["Month"], downcast="integer")

memory = pd.DataFrame([
    {"dataset": "before", "memory_mb": base.memory_usage(deep=True).sum() / 1024 / 1024},
    {"dataset": "after", "memory_mb": optimized.memory_usage(deep=True).sum() / 1024 / 1024},
])
memory["change_percent"] = (memory["memory_mb"] / memory.loc[0, "memory_mb"] - 1) * 100
memory.to_csv(OUT / "memory_comparison.csv", index=False)
optimized.dtypes.astype(str).reset_index().rename(columns={"index": "column", 0: "dtype"}).to_csv(OUT / "dtypes_after.csv", index=False)


def measure(name, data):
    tests = []
    operations = {
        "sales_by_country": lambda x: x.groupby("Country", observed=True)["Revenue"].sum(),
        "sales_by_month": lambda x: x.groupby("Month", observed=True)["Revenue"].sum(),
        "top10_customers": lambda x: x.groupby("CustomerID")["Revenue"].sum().sort_values(ascending=False).head(10),
        "uk_products": lambda x: x[x["Country"] == "United Kingdom"],
        "sales_over_1000": lambda x: x[x["Revenue"] > 1000],
    }
    for op_name, func in operations.items():
        start = time.perf_counter()
        result = func(data)
        seconds = time.perf_counter() - start
        rows = len(result) if hasattr(result, "__len__") else 1
        tests.append({"dataset": name, "operation": op_name, "seconds": seconds, "rows": rows})
    return tests

times = pd.DataFrame(measure("before", base) + measure("after", optimized))
times.to_csv(OUT / "operation_times_comparison.csv", index=False)

report = f"""
Czas wczytywania pliku: {load_time:.4f} s.
Liczba rekordów źródłowych: {len(df)}.
Liczba rekordów po przygotowaniu: {len(base)}.
Pamięć przed optymalizacją: {memory.loc[0, 'memory_mb']:.2f} MB.
Pamięć po optymalizacji: {memory.loc[1, 'memory_mb']:.2f} MB.

Wnioski:
Zmiana kolumn tekstowych na category i downcasting typów liczbowych zmniejszyły zużycie pamięci.
Część operacji może przyspieszyć, zwłaszcza grupowania po kolumnach kategorycznych.
Mniejsze użycie pamięci nie zawsze gwarantuje szybsze wykonanie każdej operacji, ponieważ wynik zależy też od typu operacji i liczby grup.
"""
save_text(OUT / "conclusions.txt", report)
print(report)
