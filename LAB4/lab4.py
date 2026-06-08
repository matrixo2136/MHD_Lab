from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))

import pandas as pd
from mhd_utils import read_online_retail, read_online_retail_ii, prepare_online_retail, output_dir, save_text

OUT = output_dir("LAB4")
BASIC = OUT / "basic"
INTEGRATED = OUT / "integrated"
BASIC.mkdir(exist_ok=True)
INTEGRATED.mkdir(exist_ok=True)

raw1 = read_online_retail()
df1 = prepare_online_retail(raw1)

fact = df1[["InvoiceNo", "StockCode", "CustomerID", "InvoiceDate", "Quantity", "UnitPrice", "Revenue", "Year", "Month", "Day", "Country"]].copy()
fact = fact.rename(columns={"InvoiceNo": "invoice_no", "StockCode": "stock_code", "CustomerID": "customer_id", "InvoiceDate": "invoice_date", "Quantity": "quantity", "UnitPrice": "unit_price", "Revenue": "revenue"})
fact.to_csv(BASIC / "fact_sales.csv", index=False)

basic_report = f"""
Extract: {len(raw1)} rekordów.
Transform po czyszczeniu: {len(df1)} rekordów.
Load: zapisano fact_sales.csv.
Revenue łącznie: {df1['Revenue'].sum():.2f}
"""
save_text(BASIC / "etl_report.txt", basic_report)

raw2 = read_online_retail_ii()
if raw2 is None:
    save_text(INTEGRATED / "integration_notes.txt", "Brak pliku Online_Retail_II. Wykonano tylko podstawowy ETL.")
    print("LAB4: brak drugiego źródła. Część podstawowa gotowa.")
else:
    df2 = prepare_online_retail(raw2)
    df_all = pd.concat([df1, df2], ignore_index=True)
    duplicate_key = ["InvoiceNo", "StockCode", "CustomerID", "InvoiceDate", "Quantity", "UnitPrice"]
    duplicates = df_all[df_all.duplicated(subset=duplicate_key, keep=False)]

    price_check = df_all.groupby(["StockCode", "Description"], as_index=False).agg(
        min_price=("UnitPrice", "min"),
        max_price=("UnitPrice", "max"),
        rows=("UnitPrice", "size")
    )
    price_conflicts = price_check[price_check["min_price"] != price_check["max_price"]]

    fact_all = df_all[["InvoiceNo", "StockCode", "CustomerID", "InvoiceDate", "Quantity", "UnitPrice", "Revenue", "Year", "Month", "Day", "Country", "Source"]].copy()
    fact_all = fact_all.rename(columns={"InvoiceNo": "invoice_no", "StockCode": "stock_code", "CustomerID": "customer_id", "InvoiceDate": "invoice_date", "Quantity": "quantity", "UnitPrice": "unit_price", "Revenue": "revenue", "Source": "source"})
    fact_all.to_csv(INTEGRATED / "fact_sales_integrated.csv", index=False)

    duplicates.head(1000).to_csv(INTEGRATED / "duplicates_sample.csv", index=False)
    price_conflicts.head(1000).to_csv(INTEGRATED / "price_conflicts_sample.csv", index=False)
    df_all.groupby("Source").size().reset_index(name="rows").to_csv(INTEGRATED / "source_rows_count.csv", index=False)

    notes = f"""
Połączono dane funkcją concat, ponieważ zbiory mają tę samą strukturę po standaryzacji kolumn.
Liczba rekordów źródła 1 po czyszczeniu: {len(df1)}.
Liczba rekordów źródła 2 po czyszczeniu: {len(df2)}.
Liczba rekordów po integracji: {len(df_all)}.
Wykryte potencjalne duplikaty: {len(duplicates)}.
Wykryte potencjalne konflikty cenowe: {len(price_conflicts)}.
"""
    save_text(INTEGRATED / "integration_notes.txt", notes)
    print("LAB4 zakończone. Wyniki zapisano w LAB4/output.")
