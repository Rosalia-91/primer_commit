from pathlib import Path

APP_TITLE = "Dashboard Retail + IA"
APP_SUBTITLE = "Día 5 · Interactividad del dashboard con filtros"

EXPECTED_SHEETS = ("Customers", "Products", "Stores", "Transactions")

VIEWS = (
    "Resumen ejecutivo",
    "Tendencias comerciales",
    "Análisis de productos",
    "Clientes y segmentos",
    "Exploración tabular",
)

DEFAULT_TOP_N = 10
MIN_TOP_N = 5
MAX_TOP_N = 20

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "raw" / "retail_sales_dataset.xlsx"
