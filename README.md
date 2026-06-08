# MHD_Lab - wersja uproszczona dla laboratoriów

Repozytorium przygotowane do laboratoriów z przedmiotu **Mechanizmy Hurtowni Danych**.

## Struktura

```text
MHD_Lab/
├── data_common/          # wspólne dane dla wszystkich laboratoriów
├── LAB1/
├── LAB2/
├── LAB3/
├── LAB4/
├── LAB5/
├── LAB6/
├── LAB7/
├── mhd_utils.py          # wspólne funkcje pomocnicze
├── requirements.txt
└── .gitignore
```

## Dane

Do folderu `data_common/` wrzuć tylko raz:

```text
sales_raw.csv
Online_Retail.csv
Online_Retail_II.xlsx      # opcjonalnie, potrzebne głównie do LAB4/LAB5
```

Dzięki temu pliki danych nie są duplikowane w każdym laboratorium.

## Uruchamianie lokalnie

```powershell
cd C:\Users\Ja\Desktop\MHD_Lab
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Przykład uruchomienia:

```powershell
python LAB1\lab1.py
python LAB2\lab2.py
python LAB3\lab3.py
python LAB4\lab4.py
python LAB5\lab5.py
python LAB6\lab6.py
python LAB7\lab7.py
```

## PythonAnywhere

```bash
cd ~/MHD_Lab
source ~/.virtualenvs/MHD_Lab/bin/activate
pip install -r requirements.txt
python LAB7/lab7.py
```

Wyniki zapisują się w folderach `LABX/output/`.
