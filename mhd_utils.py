from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data_common"


def output_dir(lab_name: str) -> Path:
    path = ROOT / lab_name / "output"
    path.mkdir(parents=True, exist_ok=True)
    return path


def require_file(name: str) -> Path:
    path = DATA / name
    if not path.exists():
        raise FileNotFoundError(f"Brak pliku: {path}")
    return path


def read_sales_raw() -> pd.DataFrame:
    return pd.read_csv(require_file("sales_raw.csv"))


def read_online_retail(name="Online_Retail.csv") -> pd.DataFrame:
    return standardize_online_retail(pd.read_csv(require_file(name), encoding="ISO-8859-1"), name)


def read_online_retail_ii():
    candidates = [
        DATA / "Online_Retail_II.xlsx",
        DATA / "online_retail_II.xlsx",
        DATA / "Online_Retail_II.csv",
        DATA / "online_retail_II.csv",
    ]
    for path in candidates:
        if path.exists():
            if path.suffix.lower() in [".xlsx", ".xls"]:
                return standardize_online_retail(pd.read_excel(path), path.name)
            return standardize_online_retail(pd.read_csv(path, encoding="ISO-8859-1"), path.name)
    return None


def standardize_online_retail(df: pd.DataFrame, source_name="source") -> pd.DataFrame:
    names = {
        "Invoice": "InvoiceNo",
        "Customer ID": "CustomerID",
        "Price": "UnitPrice",
    }
    df = df.rename(columns={old: new for old, new in names.items() if old in df.columns})
    needed = ["InvoiceNo", "StockCode", "Description", "Quantity", "InvoiceDate", "UnitPrice", "CustomerID", "Country"]
    missing = [col for col in needed if col not in df.columns]
    if missing:
        raise ValueError(f"Brak kolumn w {source_name}: {missing}")
    df = df[needed].copy()
    df["Source"] = source_name
    return df


def prepare_online_retail(df: pd.DataFrame, remove_returns=True) -> pd.DataFrame:
    df = df.copy()
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
    df["UnitPrice"] = pd.to_numeric(df["UnitPrice"], errors="coerce")
    df["Description"] = df["Description"].fillna("Unknown product")
    df["Country"] = df["Country"].fillna("Unknown")
    df = df.dropna(subset=["CustomerID", "InvoiceDate", "Quantity", "UnitPrice"])
    df = df[~df["InvoiceNo"].astype(str).str.startswith("C")]
    if remove_returns:
        df = df[(df["Quantity"] > 0) & (df["UnitPrice"] > 0)]
    else:
        df = df[df["UnitPrice"] >= 0]
    df = df.drop_duplicates().copy()
    df["CustomerID"] = df["CustomerID"].astype(int)
    df["Revenue"] = df["Quantity"] * df["UnitPrice"]
    df["Year"] = df["InvoiceDate"].dt.year
    df["Month"] = df["InvoiceDate"].dt.month
    df["Day"] = df["InvoiceDate"].dt.day
    return df


def save_text(path: Path, text: str):
    path.write_text(text.strip() + "\n", encoding="utf-8")
