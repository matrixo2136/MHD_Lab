# LAB9 - Raportowanie i analiza: Pandas vs SQL

Laboratorium przygotowuje proste raporty sprzedażowe w dwóch wersjach:

- Pandas
- SQL na lokalnej bazie SQLite

## Zakres

Skrypt odpowiada na pytania:

1. Ile sprzedano produktów w każdej kategorii?
2. Który klient kupuje najwięcej?
3. Jak zmieniła się sprzedaż w ostatnich dniach?
4. Czy wyniki Pandas i SQL są zgodne?
5. Jakie wnioski można przekazać biznesowi?

## Dane

Skrypt korzysta ze wspólnego folderu:

```text
data_common/
```

Wystarczy, że w głównym folderze projektu znajduje się jeden z plików:

```text
data_common/Online_Retail.csv
data_common/Online_Retail_II.xlsx
data_common/Online_Retail_II.csv
```

Nie trzeba kopiować danych do folderu LAB9.

## Uruchomienie

Z głównego folderu projektu:

```bash
python LAB9/lab9_reporting_pandas_sql.py
```

## Wyniki

Wyniki zapisują się w:

```text
LAB9/output/reporting/
```

Najważniejsze pliki:

- `pandas_category_report.csv`
- `sql_category_report.csv`
- `pandas_top10_customers.csv`
- `sql_top10_customers.csv`
- `pandas_recent_sales.csv`
- `sql_recent_sales.csv`
- `pandas_vs_sql_comparison.csv`
- `comparison_summary.txt`
- `business_insights.txt`
- `used_sql_queries.sql`
- `lab9_reporting.sqlite`
