from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))

import pandas as pd
from mhd_utils import read_online_retail, prepare_online_retail, output_dir, save_text

OUT = output_dir("LAB2")
INMON = OUT / "inmon_3nf"
STAR = OUT / "star_schema"
INMON.mkdir(exist_ok=True)
STAR.mkdir(exist_ok=True)

raw = read_online_retail()
df = prepare_online_retail(raw)

country = df[["Country"]].drop_duplicates().sort_values("Country").reset_index(drop=True)
country.insert(0, "country_id", range(1, len(country) + 1))
country = country.rename(columns={"Country": "country_name"})

df = df.merge(country, left_on="Country", right_on="country_name", how="left")

customer = df[["CustomerID", "country_id"]].drop_duplicates().reset_index(drop=True)
customer.insert(0, "customer_id", range(1, len(customer) + 1))
customer = customer.rename(columns={"CustomerID": "customer_natural_id"})

product = df[["StockCode", "Description"]].drop_duplicates().reset_index(drop=True)
product.insert(0, "product_id", range(1, len(product) + 1))
product = product.rename(columns={"StockCode": "stock_code", "Description": "description"})

invoice = df[["InvoiceNo", "InvoiceDate", "CustomerID", "country_id"]].drop_duplicates().reset_index(drop=True)
invoice = invoice.rename(columns={"InvoiceNo": "invoice_no", "InvoiceDate": "invoice_date", "CustomerID": "customer_natural_id"})

line = df[["InvoiceNo", "StockCode", "Quantity", "UnitPrice", "Revenue"]].copy()
line.insert(0, "invoice_line_id", range(1, len(line) + 1))
line = line.rename(columns={"InvoiceNo": "invoice_no", "StockCode": "stock_code", "Quantity": "quantity", "UnitPrice": "unit_price", "Revenue": "revenue"})

country.to_csv(INMON / "country_3nf.csv", index=False)
customer.to_csv(INMON / "customer_3nf.csv", index=False)
product.to_csv(INMON / "product_3nf.csv", index=False)
invoice.to_csv(INMON / "invoice_3nf.csv", index=False)
line.to_csv(INMON / "invoice_line_3nf.csv", index=False)

_dim_country = country.rename(columns={"country_id": "country_key"})
_dim_customer = customer.rename(columns={"customer_id": "customer_key"})
_dim_product = product.rename(columns={"product_id": "product_key"})

dim_date = df[["InvoiceDate", "Year", "Month", "Day"]].drop_duplicates().sort_values("InvoiceDate").reset_index(drop=True)
dim_date.insert(0, "date_key", range(1, len(dim_date) + 1))

fact = df.merge(_dim_customer, left_on=["CustomerID", "country_id"], right_on=["customer_natural_id", "country_id"], how="left")
fact = fact.merge(_dim_product, left_on=["StockCode", "Description"], right_on=["stock_code", "description"], how="left")
fact = fact.merge(dim_date[["date_key", "InvoiceDate"]], on="InvoiceDate", how="left")
fact = fact[["InvoiceNo", "customer_key", "product_key", "date_key", "country_id", "Quantity", "UnitPrice", "Revenue"]]
fact = fact.rename(columns={"InvoiceNo": "invoice_no", "country_id": "country_key", "Quantity": "quantity", "UnitPrice": "unit_price", "Revenue": "revenue"})
fact.insert(0, "sales_key", range(1, len(fact) + 1))

_dim_country.to_csv(STAR / "dim_country.csv", index=False)
_dim_customer.to_csv(STAR / "dim_customer.csv", index=False)
_dim_product.to_csv(STAR / "dim_product.csv", index=False)
dim_date.to_csv(STAR / "dim_date.csv", index=False)
fact.to_csv(STAR / "fact_sales.csv", index=False)

notes = """
Model 3NF ogranicza redundancję, ale wymaga wielu połączeń tabel przy analizie OLAP.
Model gwiazdy upraszcza analizę, ponieważ tabela faktów łączy się bezpośrednio z wymiarami.
"""
save_text(OUT / "notes.txt", notes)
print("LAB2 zakończone. Wyniki zapisano w LAB2/output.")
