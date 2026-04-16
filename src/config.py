from pathlib import Path

APP_TITLE = "Dashboard Retail + IA"
APP_SUBTITLE = "Día 4 · Modularización básica del proyecto"

EXPECTED_SHEETS = ("Customers", "Products", "Stores", "Transactions")

VIEWS = (
    "Resumen ejecutivo",
    "Tendencias comerciales",
    "Análisis de productos",
    "Clientes y segmentos",
    "Exploración tabular",
)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "raw" / "retail_sales_dataset.xlsx"