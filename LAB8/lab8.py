import os
import time
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
COMMON_DATA_DIR = PROJECT_DIR / "data_common"
LOCAL_DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output" / "aggregation_performance"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

LARGE_MULTIPLIER = int(os.getenv("LAB8_MULTIPLIER", "5"))


def find_data_file() -> Path:
    possible_files = [
        COMMON_DATA_DIR / "Online_Retail_II.csv",
        COMMON_DATA_DIR / "online_retail_II.csv",
        COMMON_DATA_DIR / "Online_Retail_II.xlsx",
        COMMON_DATA_DIR / "online_retail_II.xlsx",
        LOCAL_DATA_DIR / "Online_Retail_II.csv",
        LOCAL_DATA_DIR / "online_retail_II.csv",
        LOCAL_DATA_DIR / "Online_Retail_II.xlsx",
        LOCAL_DATA_DIR / "online_retail_II.xlsx",
    ]

    for file_path in possible_files:
        if file_path.exists():
            return file_path

    raise FileNotFoundError(
        "Nie znaleziono Online_Retail_II.csv ani Online_Retail_II.xlsx. "
        "Umieść plik w głównym folderze data_common/."
    )


def read_data(file_path: Path):
    start = time.perf_counter()

    if file_path.suffix.lower() == ".csv":
        df = pd.read_csv(file_path, encoding="ISO-8859-1")
    elif file_path.suffix.lower() in [".xlsx", ".xls"]:
        sheets = pd.read_excel(file_path, sheet_name=None)
        df = pd.concat(sheets.values(), ignore_index=True)
    else:
        raise ValueError(f"Nieobsługiwany format pliku: {file_path.suffix}")

    return df, time.perf_counter() - start


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(
        columns={
            "Invoice": "InvoiceNo",
            "Customer ID": "CustomerID",
            "Price": "UnitPrice",
        }
    )

    required = [
        "InvoiceNo",
        "StockCode",
        "Description",
        "Quantity",
        "InvoiceDate",
        "UnitPrice",
        "CustomerID",
        "Country",
    ]

    missing = [column for column in required if column not in df.columns]
    if missing:
        raise ValueError(f"Brak wymaganych kolumn: {missing}")

    return df


def prepare_data(df: pd.DataFrame) -> pd.DataFrame:
    df = normalize_columns(df)
    rows_before = len(df)

    df = df.dropna(subset=["CustomerID"]).copy()
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
    df["UnitPrice"] = pd.to_numeric(df["UnitPrice"], errors="coerce")
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")

    df = df.dropna(subset=["Quantity", "UnitPrice", "InvoiceDate"])
    df = df[df["Quantity"] > 0]
    df = df[df["UnitPrice"] > 0]

    df["TotalPrice"] = df["Quantity"] * df["UnitPrice"]
    df["Month"] = df["InvoiceDate"].dt.to_period("M").astype(str)

    df["CustomerID"] = df["CustomerID"].astype(int).astype(str)
    df["InvoiceNo"] = df["InvoiceNo"].astype(str)
    df["Country"] = df["Country"].astype(str)
    df["StockCode"] = df["StockCode"].astype(str)

    pd.DataFrame([
        {
            "rows_before_cleaning": rows_before,
            "rows_after_cleaning": len(df),
            "removed_rows": rows_before - len(df),
        }
    ]).to_csv(OUTPUT_DIR / "data_preparation_report.csv", index=False)

    return df


def save_extract_report(raw_df: pd.DataFrame, file_path: Path, load_time: float) -> None:
    raw_df.isna().sum().reset_index().rename(
        columns={"index": "column", 0: "missing_values"}
    ).to_csv(OUTPUT_DIR / "missing_values.csv", index=False)

    raw_df.dtypes.astype(str).reset_index().rename(
        columns={"index": "column", 0: "dtype"}
    ).to_csv(OUTPUT_DIR / "dtypes.csv", index=False)

    memory_mb = raw_df.memory_usage(deep=True).sum() / 1024 / 1024

    with open(OUTPUT_DIR / "extract_report.txt", "w", encoding="utf-8") as file:
        file.write("LAB8 - wczytanie i analiza danych\n\n")
        file.write(f"Plik danych: {file_path}\n")
        file.write(f"Czas wczytywania: {load_time:.6f} s\n")
        file.write(f"Liczba rekordów: {len(raw_df)}\n")
        file.write(f"Liczba kolumn: {raw_df.shape[1]}\n")
        file.write(f"Zużycie pamięci: {memory_mb:.2f} MB\n\n")
        file.write("Typy danych:\n")
        file.write(raw_df.dtypes.astype(str).to_string())
        file.write("\n\nBraki danych:\n")
        file.write(raw_df.isna().sum().to_string())


def measure(dataset_name: str, operation: str, method: str, function):
    start = time.perf_counter()
    result = function()
    elapsed = time.perf_counter() - start

    if isinstance(result, pd.Series):
        output = result.reset_index()
    else:
        output = result.reset_index() if result.index.name is not None else result.copy()

    file_name = f"{dataset_name}_{operation}_{method}.csv"
    output.to_csv(OUTPUT_DIR / file_name, index=False)

    return {
        "dataset": dataset_name,
        "operation": operation,
        "method": method,
        "time_seconds": elapsed,
        "result_rows": len(output),
        "output_file": file_name,
    }


def run_aggregations(df: pd.DataFrame, dataset_name: str) -> pd.DataFrame:
    country_index = df.set_index("Country")
    month_index = df.set_index("Month")
    customer_index = df.set_index("CustomerID")

    tests = [
        ("sales_by_country", "groupby", lambda: df.groupby("Country")["TotalPrice"].sum().sort_values(ascending=False)),
        ("sales_by_country", "pivot_table", lambda: pd.pivot_table(df, values="TotalPrice", index="Country", aggfunc="sum").sort_values("TotalPrice", ascending=False)),
        ("sales_by_country", "set_index", lambda: country_index.groupby(level=0)["TotalPrice"].sum().sort_values(ascending=False)),
        ("sales_by_month", "groupby", lambda: df.groupby("Month")["TotalPrice"].sum().sort_index()),
        ("sales_by_month", "pivot_table", lambda: pd.pivot_table(df, values="TotalPrice", index="Month", aggfunc="sum").sort_index()),
        ("sales_by_month", "set_index", lambda: month_index.groupby(level=0)["TotalPrice"].sum().sort_index()),
        ("transactions_by_customer", "groupby", lambda: df.groupby("CustomerID")["InvoiceNo"].nunique().sort_values(ascending=False)),
        ("transactions_by_customer", "pivot_table", lambda: pd.pivot_table(df, values="InvoiceNo", index="CustomerID", aggfunc=pd.Series.nunique).sort_values("InvoiceNo", ascending=False)),
        ("transactions_by_customer", "set_index", lambda: customer_index.groupby(level=0)["InvoiceNo"].nunique().sort_values(ascending=False)),
    ]

    rows = []
    for operation, method, function in tests:
        rows.append(measure(dataset_name, operation, method, function))

    return pd.DataFrame(rows)


def write_final_report(timings: pd.DataFrame, rows_normal: int, rows_large: int) -> None:
    fastest = timings.sort_values("time_seconds").groupby(["dataset", "operation"]).first().reset_index()
    fastest.to_csv(OUTPUT_DIR / "fastest_methods.csv", index=False)

    average = timings.groupby(["dataset", "method"])["time_seconds"].mean().reset_index().sort_values(["dataset", "time_seconds"])
    average.to_csv(OUTPUT_DIR / "average_time_by_method.csv", index=False)

    fastest_normal = average[average["dataset"] == "normal"].iloc[0]["method"]
    fastest_large = average[average["dataset"] == "large"].iloc[0]["method"]

    with open(OUTPUT_DIR / "final_report.txt", "w", encoding="utf-8") as file:
        file.write("LAB8 - raport końcowy\n\n")
        file.write(f"Rekordy po czyszczeniu: {rows_normal}\n")
        file.write(f"Rekordy po powiększeniu zbioru: {rows_large}\n")
        file.write(f"Mnożnik zbioru dużego: {LARGE_MULTIPLIER}\n\n")
        file.write(f"Najszybsza metoda średnio na zbiorze podstawowym: {fastest_normal}\n")
        file.write(f"Najszybsza metoda średnio na zbiorze dużym: {fastest_large}\n\n")
        file.write("Wnioski:\n")
        file.write("Najbardziej czytelną metodą jest groupby(), ponieważ zapis jest prosty i dobrze pasuje do typowych agregacji analitycznych.\n")
        file.write("pivot_table() jest wygodna, gdy chcemy tworzyć tabele przestawne, ale przy prostych agregacjach może mieć większy narzut.\n")
        file.write("set_index() może pomóc, gdy wielokrotnie analizujemy dane po tej samej kolumnie, ale samo utworzenie indeksu także kosztuje czas.\n")
        file.write("Przy bardzo dużych hurtowniach danych główne problemy to czas wykonania, zużycie pamięci i konieczność ograniczania zakresu danych lub stosowania agregacji wstępnych.\n")


def main():
    data_file = find_data_file()
    raw_df, load_time = read_data(data_file)

    save_extract_report(raw_df, data_file, load_time)

    df = prepare_data(raw_df)
    timings_normal = run_aggregations(df, "normal")

    large_df = pd.concat([df] * LARGE_MULTIPLIER, ignore_index=True)
    timings_large = run_aggregations(large_df, "large")

    timings = pd.concat([timings_normal, timings_large], ignore_index=True)
    timings.to_csv(OUTPUT_DIR / "aggregation_times.csv", index=False)

    write_final_report(timings, len(df), len(large_df))

    print("LAB8 zakończone.")
    print(f"Użyty plik danych: {data_file}")
    print(f"Wyniki zapisano w: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
