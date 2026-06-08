from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))

import pandas as pd
from mhd_utils import read_online_retail, prepare_online_retail, output_dir, save_text

OUT = output_dir("LAB3")
df = prepare_online_retail(read_online_retail())

dim_product = df[["StockCode", "Description"]].drop_duplicates().reset_index(drop=True)
dim_product.insert(0, "product_key", range(1, len(dim_product) + 1))
dim_product = dim_product.rename(columns={"StockCode": "stock_code", "Description": "product_name"})

dim_country = df[["Country"]].drop_duplicates().sort_values("Country").reset_index(drop=True)
dim_country.insert(0, "country_key", range(1, len(dim_country) + 1))
dim_country = dim_country.rename(columns={"Country": "country_name"})

dim_invoice = df[["InvoiceNo", "InvoiceDate"]].drop_duplicates().sort_values("InvoiceNo").reset_index(drop=True)
dim_invoice.insert(0, "invoice_key", range(1, len(dim_invoice) + 1))
dim_invoice = dim_invoice.rename(columns={"InvoiceNo": "invoice_no", "InvoiceDate": "invoice_date"})

dim_date = df[["InvoiceDate", "Year", "Month", "Day"]].drop_duplicates().sort_values("InvoiceDate").reset_index(drop=True)
dim_date.insert(0, "date_key", range(1, len(dim_date) + 1))
dim_date = dim_date.rename(columns={"InvoiceDate": "date"})

customer_scd = df.groupby(["CustomerID", "Country"], as_index=False).agg(
    valid_from=("InvoiceDate", "min"),
    last_seen=("InvoiceDate", "max")
).sort_values(["CustomerID", "valid_from"])
customer_scd["version_no"] = customer_scd.groupby("CustomerID").cumcount() + 1
customer_scd["is_current"] = customer_scd.groupby("CustomerID")["last_seen"].transform("max").eq(customer_scd["last_seen"])
customer_scd["valid_to"] = customer_scd["last_seen"].where(~customer_scd["is_current"], pd.NaT)
customer_scd.insert(0, "customer_key", range(1, len(customer_scd) + 1))
customer_scd = customer_scd.rename(columns={"CustomerID": "customer_natural_id", "Country": "country"})

fact = df.merge(dim_product, left_on=["StockCode", "Description"], right_on=["stock_code", "product_name"], how="left")
fact = fact.merge(dim_country, left_on="Country", right_on="country_name", how="left")
fact = fact.merge(dim_invoice[["invoice_key", "invoice_no"]], left_on="InvoiceNo", right_on="invoice_no", how="left")
fact = fact.merge(dim_date[["date_key", "date"]], left_on="InvoiceDate", right_on="date", how="left")
fact = fact.merge(customer_scd[["customer_key", "customer_natural_id", "country"]], left_on=["CustomerID", "Country"], right_on=["customer_natural_id", "country"], how="left")

fact = fact[["invoice_key", "date_key", "customer_key", "product_key", "country_key", "Quantity", "UnitPrice", "Revenue"]]
fact.insert(0, "sales_key", range(1, len(fact) + 1))
fact = fact.rename(columns={"Quantity": "quantity", "UnitPrice": "unit_price", "Revenue": "revenue"})

dim_product.to_csv(OUT / "DimProduct.csv", index=False)
dim_country.to_csv(OUT / "DimCountry.csv", index=False)
dim_invoice.to_csv(OUT / "DimInvoice.csv", index=False)
dim_date.to_csv(OUT / "DimDate.csv", index=False)
customer_scd.to_csv(OUT / "DimCustomer_SCD2.csv", index=False)
fact.to_csv(OUT / "FactSales.csv", index=False)

fact.merge(dim_country, on="country_key").groupby("country_name", as_index=False)["revenue"].sum().sort_values("revenue", ascending=False).to_csv(OUT / "sales_by_country.csv", index=False)
fact.merge(dim_date, on="date_key").groupby(["Year", "Month"], as_index=False)["revenue"].sum().to_csv(OUT / "sales_by_month.csv", index=False)

notes = """
Grain: pojedyncza pozycja faktury. Jeden rekord w FactSales opisuje sprzedaż konkretnego produktu na konkretnej fakturze.
Takie ziarno daje największą elastyczność analiz, np. według produktu, klienta, kraju i czasu.
Każdy wymiar ma klucz sztuczny, a tabela faktów przechowuje wyłącznie klucze obce i miary.
Dla DimCustomer zastosowano SCD2, aby zachować historię zmian kraju klienta.
"""
save_text(OUT / "design_notes.txt", notes)
print("LAB3 zakończone. Wyniki zapisano w LAB3/output.")
