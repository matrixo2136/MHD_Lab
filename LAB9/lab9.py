import sqlite3
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
COMMON_DATA_DIR = PROJECT_DIR / "data_common"
LOCAL_DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output" / "reporting"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def find_data_file() -> Path:
    possible_files = [
        COMMON_DATA_DIR / "Online_Retail.csv",
        COMMON_DATA_DIR / "online_retail.csv",
        COMMON_DATA_DIR / "Online_Retail_II.csv",
        COMMON_DATA_DIR / "online_retail_II.csv",
        COMMON_DATA_DIR / "Online_Retail_II.xlsx",
        COMMON_DATA_DIR / "online_retail_II.xlsx",
        LOCAL_DATA_DIR / "Online_Retail.csv",
        LOCAL_DATA_DIR / "Online_Retail_II.csv",
        LOCAL_DATA_DIR / "Online_Retail_II.xlsx",
    ]

    for file_path in possible_files:
        if file_path.exists():
            return file_path

    raise FileNotFoundError(
        "Nie znaleziono danych. Umieść Online_Retail.csv lub Online_Retail_II.xlsx "
        "w głównym folderze data_common/."
    )


def read_data(file_path: Path) -> pd.DataFrame:
    if file_path.suffix.lower() == ".csv":
        return pd.read_csv(file_path, encoding="ISO-8859-1")

    if file_path.suffix.lower() in [".xlsx", ".xls"]:
        sheets = pd.read_excel(file_path, sheet_name=None)
        return pd.concat(sheets.values(), ignore_index=True)

    raise ValueError(f"Nieobsługiwany format pliku: {file_path.suffix}")


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(
        columns={
            "Invoice": "InvoiceNo",
            "Customer ID": "CustomerID",
            "Price": "UnitPrice",
        }
    )

    required_columns = [
        "InvoiceNo",
        "StockCode",
        "Description",
        "Quantity",
        "InvoiceDate",
        "UnitPrice",
        "CustomerID",
        "Country",
    ]

    missing = [column for column in required_columns if column not in df.columns]
    if missing:
        raise ValueError(f"Brak wymaganych kolumn: {missing}")

    return df


def create_category(stock_code) -> str:
    code = str(stock_code).upper().strip()

    if code.startswith("POST"):
        return "Postage"
    if code.startswith("M"):
        return "Manual"
    if code.startswith("D"):
        return "Discount"
    if code.startswith("C2"):
        return "Carriage"
    if code and code[0].isdigit():
        return f"Product group {code[0]}"

    return "Other"


def prepare_data(df: pd.DataFrame) -> pd.DataFrame:
    df = normalize_columns(df)

    rows_before = len(df)

    df = df.dropna(subset=["CustomerID"]).copy()
    df = df[~df["InvoiceNo"].astype(str).str.startswith("C")]

    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
    df["UnitPrice"] = pd.to_numeric(df["UnitPrice"], errors="coerce")
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")

    df = df.dropna(subset=["Quantity", "UnitPrice", "InvoiceDate"])
    df = df[df["Quantity"] > 0]
    df = df[df["UnitPrice"] > 0]

    df["CustomerID"] = df["CustomerID"].astype(int).astype(str)
    df["InvoiceNo"] = df["InvoiceNo"].astype(str)
    df["StockCode"] = df["StockCode"].astype(str)
    df["Description"] = df["Description"].fillna("Unknown product").astype(str)
    df["Country"] = df["Country"].fillna("Unknown country").astype(str)

    df["Revenue"] = df["Quantity"] * df["UnitPrice"]
    df["Date"] = df["InvoiceDate"].dt.date.astype(str)
    df["Category"] = df["StockCode"].apply(create_category)

    report = pd.DataFrame(
        [
            {
                "rows_before_cleaning": rows_before,
                "rows_after_cleaning": len(df),
                "removed_rows": rows_before - len(df),
                "unique_customers": df["CustomerID"].nunique(),
                "unique_products": df["StockCode"].nunique(),
                "unique_invoices": df["InvoiceNo"].nunique(),
            }
        ]
    )
    report.to_csv(OUTPUT_DIR / "data_preparation_report.csv", index=False)

    return df


def build_sales_and_products(df: pd.DataFrame):
    products = (
        df[["StockCode", "Description", "Category"]]
        .drop_duplicates(subset=["StockCode"])
        .rename(
            columns={
                "StockCode": "product_id",
                "Description": "product_name",
                "Category": "category",
            }
        )
        .reset_index(drop=True)
    )

    sales = df[
        [
            "InvoiceNo",
            "StockCode",
            "CustomerID",
            "Quantity",
            "UnitPrice",
            "Revenue",
            "InvoiceDate",
            "Date",
            "Country",
        ]
    ].rename(
        columns={
            "InvoiceNo": "invoice_no",
            "StockCode": "product_id",
            "CustomerID": "customer_id",
            "Quantity": "quantity",
            "UnitPrice": "unit_price",
            "Revenue": "revenue",
            "InvoiceDate": "invoice_date",
            "Date": "date",
            "Country": "country",
        }
    )

    sales["invoice_date"] = sales["invoice_date"].astype(str)

    return sales, products


def pandas_reports(sales: pd.DataFrame, products: pd.DataFrame):
    full = sales.merge(products, on="product_id", how="left")

    category_report = (
        full.groupby("category")
        .agg(
            total_quantity=("quantity", "sum"),
            total_revenue=("revenue", "sum"),
            unique_products=("product_id", "nunique"),
        )
        .reset_index()
        .sort_values("total_quantity", ascending=False)
    )

    customer_report = (
        full.groupby("customer_id")
        .agg(
            total_quantity=("quantity", "sum"),
            total_revenue=("revenue", "sum"),
            invoices=("invoice_no", "nunique"),
        )
        .reset_index()
        .sort_values(["total_quantity", "total_revenue"], ascending=False)
    )

    recent_dates = sorted(full["date"].dropna().unique())[-3:]
    recent_sales = (
        full[full["date"].isin(recent_dates)]
        .groupby("date")
        .agg(
            total_quantity=("quantity", "sum"),
            total_revenue=("revenue", "sum"),
            invoices=("invoice_no", "nunique"),
        )
        .reset_index()
        .sort_values("date")
    )

    category_report.to_csv(OUTPUT_DIR / "pandas_category_report.csv", index=False)
    customer_report.head(10).to_csv(OUTPUT_DIR / "pandas_top10_customers.csv", index=False)
    recent_sales.to_csv(OUTPUT_DIR / "pandas_recent_sales.csv", index=False)

    return category_report, customer_report, recent_sales


def sql_reports(sales: pd.DataFrame, products: pd.DataFrame):
    db_path = OUTPUT_DIR / "lab9_reporting.sqlite"

    with sqlite3.connect(db_path) as connection:
        sales.to_sql("sales", connection, if_exists="replace", index=False)
        products.to_sql("products", connection, if_exists="replace", index=False)

        category_sql = """
        SELECT
            p.category,
            SUM(s.quantity) AS total_quantity,
            SUM(s.revenue) AS total_revenue,
            COUNT(DISTINCT s.product_id) AS unique_products
        FROM sales s
        JOIN products p ON s.product_id = p.product_id
        GROUP BY p.category
        ORDER BY total_quantity DESC;
        """

        customer_sql = """
        SELECT
            s.customer_id,
            SUM(s.quantity) AS total_quantity,
            SUM(s.revenue) AS total_revenue,
            COUNT(DISTINCT s.invoice_no) AS invoices
        FROM sales s
        GROUP BY s.customer_id
        ORDER BY total_quantity DESC, total_revenue DESC
        LIMIT 10;
        """

        recent_sql = """
        SELECT
            s.date,
            SUM(s.quantity) AS total_quantity,
            SUM(s.revenue) AS total_revenue,
            COUNT(DISTINCT s.invoice_no) AS invoices
        FROM sales s
        WHERE s.date IN (
            SELECT DISTINCT date
            FROM sales
            ORDER BY date DESC
            LIMIT 3
        )
        GROUP BY s.date
        ORDER BY s.date;
        """

        category_report = pd.read_sql_query(category_sql, connection)
        customer_report = pd.read_sql_query(customer_sql, connection)
        recent_sales = pd.read_sql_query(recent_sql, connection)

    category_report.to_csv(OUTPUT_DIR / "sql_category_report.csv", index=False)
    customer_report.to_csv(OUTPUT_DIR / "sql_top10_customers.csv", index=False)
    recent_sales.to_csv(OUTPUT_DIR / "sql_recent_sales.csv", index=False)

    with open(OUTPUT_DIR / "used_sql_queries.sql", "w", encoding="utf-8") as file:
        file.write("-- Raport: liczba sprzedanych produktów w każdej kategorii\n")
        file.write(category_sql.strip())
        file.write("\n\n-- Raport: klient kupujący najwięcej\n")
        file.write(customer_sql.strip())
        file.write("\n\n-- Raport: sprzedaż w ostatnich dniach\n")
        file.write(recent_sql.strip())

    return category_report, customer_report, recent_sales


def compare_reports(pandas_category: pd.DataFrame, sql_category: pd.DataFrame):
    pandas_check = pandas_category.copy()
    sql_check = sql_category.copy()

    pandas_check["total_revenue"] = pandas_check["total_revenue"].round(2)
    sql_check["total_revenue"] = sql_check["total_revenue"].round(2)

    comparison = pandas_check.merge(
        sql_check,
        on="category",
        how="outer",
        suffixes=("_pandas", "_sql"),
    )

    comparison["quantity_equal"] = (
        comparison["total_quantity_pandas"].round(2)
        == comparison["total_quantity_sql"].round(2)
    )
    comparison["revenue_equal"] = (
        comparison["total_revenue_pandas"].round(2)
        == comparison["total_revenue_sql"].round(2)
    )

    comparison.to_csv(OUTPUT_DIR / "pandas_vs_sql_comparison.csv", index=False)

    all_ok = bool(comparison["quantity_equal"].all() and comparison["revenue_equal"].all())

    with open(OUTPUT_DIR / "comparison_summary.txt", "w", encoding="utf-8") as file:
        file.write("Porównanie Pandas vs SQL\n\n")
        if all_ok:
            file.write("Wyniki raportu kategorii są zgodne w Pandas i SQL.\n")
        else:
            file.write("Wyniki raportu kategorii różnią się i wymagają sprawdzenia.\n")


def write_business_insights(category_report: pd.DataFrame, customer_report: pd.DataFrame, recent_sales: pd.DataFrame):
    best_category = category_report.iloc[0]
    best_customer = customer_report.iloc[0]

    recent_text = recent_sales.to_string(index=False)

    with open(OUTPUT_DIR / "business_insights.txt", "w", encoding="utf-8") as file:
        file.write("LAB9 - krótkie insighty dla biznesu\n\n")

        file.write("1. Najlepiej sprzedająca się kategoria\n")
        file.write(
            f"Największą liczbę sprzedanych sztuk ma kategoria "
            f"{best_category['category']}: {best_category['total_quantity']:.0f} sztuk.\n"
        )
        file.write(
            f"Przychód tej kategorii wynosi około {best_category['total_revenue']:.2f}.\n\n"
        )

        file.write("2. Najważniejszy klient\n")
        file.write(
            f"Najwięcej kupił klient {best_customer['customer_id']}: "
            f"{best_customer['total_quantity']:.0f} sztuk, "
            f"przychód {best_customer['total_revenue']:.2f}.\n\n"
        )

        file.write("3. Sprzedaż w ostatnich dniach danych\n")
        file.write(recent_text)
        file.write("\n\n")

        file.write("4. Rekomendacje biznesowe\n")
        file.write(
            "Najważniejsze kategorie warto monitorować pod kątem dostępności magazynowej. "
            "Klientów o największym wolumenie zakupów można potraktować jako grupę priorytetową "
            "w działaniach sprzedażowych. Porównanie Pandas i SQL pokazuje, że oba narzędzia "
            "mogą dać te same wyniki, ale SQL jest bardziej naturalny do raportowania w firmowej bazie, "
            "a Pandas jest wygodny do szybkiej analizy i prototypowania.\n"
        )


def main():
    data_file = find_data_file()
    raw_df = read_data(data_file)
    df = prepare_data(raw_df)

    sales, products = build_sales_and_products(df)

    sales.to_csv(OUTPUT_DIR / "sales_table.csv", index=False)
    products.to_csv(OUTPUT_DIR / "products_table.csv", index=False)

    pandas_category, pandas_customer, pandas_recent = pandas_reports(sales, products)
    sql_category, sql_customer, sql_recent = sql_reports(sales, products)

    compare_reports(pandas_category, sql_category)
    write_business_insights(pandas_category, pandas_customer, pandas_recent)

    print("LAB9 zakończone.")
    print(f"Użyty plik danych: {data_file}")
    print(f"Wyniki zapisano w: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
