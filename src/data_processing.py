from pathlib import Path

import pandas as pd
import streamlit as st

from src.config import EXPECTED_SHEETS


def validate_workbook(file_path: Path) -> None:
    if not file_path.exists():
        raise FileNotFoundError(
            "No se encontró el archivo 'retail_sales_dataset.xlsx' en 'data/raw/'."
        )

    xls = pd.ExcelFile(file_path)
    missing_sheets = [sheet for sheet in EXPECTED_SHEETS if sheet not in xls.sheet_names]

    if missing_sheets:
        raise ValueError(
            "Faltan hojas necesarias para el proyecto: " + ", ".join(missing_sheets)
        )


@st.cache_data(show_spinner=False)
def load_source_tables(file_path_str: str) -> dict[str, pd.DataFrame]:
    file_path = Path(file_path_str)
    validate_workbook(file_path)

    return {
        "Customers": pd.read_excel(file_path, sheet_name="Customers"),
        "Products": pd.read_excel(file_path, sheet_name="Products"),
        "Stores": pd.read_excel(file_path, sheet_name="Stores"),
        "Transactions": pd.read_excel(file_path, sheet_name="Transactions"),
    }


def build_analytical_dataset(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    customers = tables["Customers"].copy()
    products = tables["Products"].copy()
    stores = tables["Stores"].copy()
    transactions = tables["Transactions"].copy()

    customers["BirthDate"] = pd.to_datetime(customers["BirthDate"], errors="coerce")
    customers["JoinDate"] = pd.to_datetime(customers["JoinDate"], errors="coerce")
    transactions["Date"] = pd.to_datetime(transactions["Date"], errors="coerce")

    customers["CustomerFullName"] = (
        customers["FirstName"].astype(str).str.strip()
        + " "
        + customers["LastName"].astype(str).str.strip()
    )

    analytical_df = transactions.merge(customers, on="CustomerID", how="left")
    analytical_df = analytical_df.merge(products, on="ProductID", how="left")
    analytical_df = analytical_df.merge(
        stores,
        on="StoreID",
        how="left",
        suffixes=("_Customer", "_Store"),
    )

    analytical_df = analytical_df.rename(
        columns={
            "Date": "TransactionDate",
            "City_Customer": "CustomerCity",
            "City_Store": "StoreCity",
            "Region": "StoreRegion",
        }
    )

    analytical_df["gross_sales"] = analytical_df["Quantity"] * analytical_df["UnitPrice"]
    analytical_df["discount_amount"] = analytical_df["gross_sales"] * analytical_df["Discount"]
    analytical_df["net_sales"] = analytical_df["gross_sales"] - analytical_df["discount_amount"]
    analytical_df["total_cost"] = analytical_df["Quantity"] * analytical_df["CostPrice"]
    analytical_df["profit"] = analytical_df["net_sales"] - analytical_df["total_cost"]

    analytical_df["year"] = analytical_df["TransactionDate"].dt.year
    analytical_df["month"] = analytical_df["TransactionDate"].dt.month
    analytical_df["year_month"] = analytical_df["TransactionDate"].dt.to_period("M").astype(str)

    customer_sales = (
        analytical_df.groupby("CustomerID", as_index=False)["net_sales"]
        .sum()
        .rename(columns={"net_sales": "customer_total_sales"})
    )

    ranked_sales = customer_sales["customer_total_sales"].rank(method="first")
    customer_sales["CustomerSegment"] = pd.qcut(
        ranked_sales,
        q=3,
        labels=["Bajo", "Medio", "Alto"]
    )

    analytical_df = analytical_df.merge(
        customer_sales[["CustomerID", "CustomerSegment"]],
        on="CustomerID",
        how="left"
    )

    return analytical_df


def get_filter_options(df: pd.DataFrame) -> dict:
    segment_order = {"Bajo": 0, "Medio": 1, "Alto": 2}

    customer_segments = sorted(
        df["CustomerSegment"].dropna().astype(str).unique().tolist(),
        key=lambda x: segment_order.get(x, 99)
    )

    gender_map = {"M": "Masculino", "F": "Femenino"}

    genders = sorted(df["Gender"].dropna().astype(str).unique().tolist())

    return {
        "min_date": df["TransactionDate"].min().date(),
        "max_date": df["TransactionDate"].max().date(),
        "regions": sorted(df["StoreRegion"].dropna().astype(str).unique().tolist()),
        "categories": sorted(df["Category"].dropna().astype(str).unique().tolist()),
        "payment_methods": sorted(df["PaymentMethod"].dropna().astype(str).unique().tolist()),
        "customer_segments": customer_segments,
        "genders": genders,
        "gender_map": gender_map,
    }


def apply_dashboard_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    filtered_df = df.copy()

    start_date, end_date = filters["date_range"]
    start_timestamp = pd.to_datetime(start_date)
    end_timestamp = pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

    filtered_df = filtered_df[
        (filtered_df["TransactionDate"] >= start_timestamp)
        & (filtered_df["TransactionDate"] <= end_timestamp)
    ]

    if filters["regions"]:
        filtered_df = filtered_df[filtered_df["StoreRegion"].isin(filters["regions"])]

    if filters["categories"]:
        filtered_df = filtered_df[filtered_df["Category"].isin(filters["categories"])]

    if filters["payment_methods"]:
        filtered_df = filtered_df[filtered_df["PaymentMethod"].isin(filters["payment_methods"])]

    if filters["genders"]:
        filtered_df = filtered_df[filtered_df["Gender"].isin(filters["genders"])]

    if filters["customer_segments"]:
        filtered_df = filtered_df[
            filtered_df["CustomerSegment"].astype(str).isin(filters["customer_segments"])
        ]

    return filtered_df


def get_active_filters_summary(filters: dict, gender_map: dict) -> list[str]:
    active_filters = []

    if filters["regions"]:
        active_filters.append("Regiones: " + ", ".join(filters["regions"]))

    if filters["categories"]:
        active_filters.append("Categorías: " + ", ".join(filters["categories"]))

    if filters["payment_methods"]:
        active_filters.append("Métodos de pago: " + ", ".join(filters["payment_methods"]))

    if filters["genders"]:
        gender_labels = [gender_map.get(value, value) for value in filters["genders"]]
        active_filters.append("Género: " + ", ".join(gender_labels))

    if filters["customer_segments"]:
        active_filters.append("Segmentos: " + ", ".join(filters["customer_segments"]))

    return active_filters


def get_executive_metrics(df: pd.DataFrame) -> dict[str, float]:
    return {
        "transactions": float(df["TransactionID"].nunique()),
        "net_sales": float(df["net_sales"].sum()),
        "profit": float(df["profit"].sum()),
        "average_ticket": float(df["net_sales"].mean()),
    }


def get_monthly_summary(df: pd.DataFrame) -> pd.DataFrame:
    monthly_summary = (
        df.groupby("year_month", as_index=False)
        .agg(
            net_sales=("net_sales", "sum"),
            profit=("profit", "sum"),
            transactions=("TransactionID", "nunique"),
        )
        .sort_values("year_month")
    )

    monthly_summary["average_ticket"] = (
        monthly_summary["net_sales"] / monthly_summary["transactions"]
    )

    return monthly_summary


def get_monthly_snapshot(df: pd.DataFrame) -> tuple[dict, dict]:
    monthly_summary = get_monthly_summary(df)

    if monthly_summary.shape[0] == 1:
        current = monthly_summary.iloc[-1].to_dict()
        previous = {
            "year_month": "Sin periodo previo",
            "net_sales": 0.0,
            "profit": 0.0,
            "transactions": 0.0,
            "average_ticket": 0.0,
        }
    else:
        current = monthly_summary.iloc[-1].to_dict()
        previous = monthly_summary.iloc[-2].to_dict()

    return current, previous


def get_sales_by_payment(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("PaymentMethod", as_index=False)["net_sales"]
        .sum()
        .sort_values("net_sales", ascending=False)
    )


def get_sales_by_category(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("Category", as_index=False)["net_sales"]
        .sum()
        .sort_values("net_sales", ascending=False)
    )


def get_profit_by_region(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("StoreRegion", as_index=False)["profit"]
        .sum()
        .sort_values("profit", ascending=False)
    )


def get_monthly_transactions(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("year_month", as_index=False)["TransactionID"]
        .nunique()
        .rename(columns={"TransactionID": "transactions"})
        .sort_values("year_month")
    )


def get_monthly_payment_mix(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby(["year_month", "PaymentMethod"], as_index=False)["net_sales"]
        .sum()
        .sort_values(["year_month", "net_sales"], ascending=[True, False])
    )


def get_product_summary(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby(["ProductName", "Category", "SubCategory"], as_index=False)
        .agg(
            net_sales=("net_sales", "sum"),
            profit=("profit", "sum"),
            quantity=("Quantity", "sum"),
        )
        .sort_values("net_sales", ascending=False)
    )


def get_subcategory_summary(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("SubCategory", as_index=False)
        .agg(
            net_sales=("net_sales", "sum"),
            profit=("profit", "sum"),
            quantity=("Quantity", "sum"),
        )
        .sort_values("net_sales", ascending=False)
    )


def get_category_quantity(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("Category", as_index=False)["Quantity"]
        .sum()
        .sort_values("Quantity", ascending=False)
    )


def get_customer_summary(df: pd.DataFrame) -> pd.DataFrame:
    group_cols = ["CustomerID"]

    if "CustomerFullName" in df.columns:
        group_cols.append("CustomerFullName")

    if "Gender" in df.columns:
        group_cols.append("Gender")

    if "CustomerSegment" in df.columns:
        group_cols.append("CustomerSegment")

    return (
        df.groupby(group_cols, as_index=False)
        .agg(
            transactions=("TransactionID", "nunique"),
            net_sales=("net_sales", "sum"),
            profit=("profit", "sum"),
            quantity=("Quantity", "sum"),
        )
        .sort_values("net_sales", ascending=False)
    )


def get_customer_segment_sales(df: pd.DataFrame) -> pd.DataFrame:
    segment_sales = (
        df.groupby("CustomerSegment", as_index=False)["net_sales"]
        .sum()
    )

    segment_order = {"Bajo": 0, "Medio": 1, "Alto": 2}
    segment_sales["segment_order"] = segment_sales["CustomerSegment"].astype(str).map(segment_order)

    return segment_sales.sort_values("segment_order").drop(columns="segment_order")


def get_gender_sales(df: pd.DataFrame) -> pd.DataFrame:
    if "Gender" not in df.columns:
        return pd.DataFrame(columns=["Gender", "net_sales", "GenderLabel"])

    gender_sales = (
        df.groupby("Gender", as_index=False)["net_sales"]
        .sum()
        .sort_values("net_sales", ascending=False)
    )

    gender_sales["GenderLabel"] = gender_sales["Gender"].replace(
        {"M": "Masculino", "F": "Femenino"}
    )

    return gender_sales


def get_quality_summary(df: pd.DataFrame) -> pd.DataFrame:
    quality_summary = pd.DataFrame(
        {
            "columna": df.columns,
            "tipo_dato": df.dtypes.astype(str).values,
            "nulos": df.isna().sum().values,
            "porcentaje_nulos": (df.isna().mean() * 100).round(2).values,
            "valores_unicos": df.nunique(dropna=False).values,
        }
    )

    return quality_summary.sort_values(
        by=["porcentaje_nulos", "valores_unicos"],
        ascending=[False, False]
    )


def get_numeric_summary(df: pd.DataFrame) -> pd.DataFrame:
    numeric_summary = df.select_dtypes(include="number").describe().T.reset_index()
    return numeric_summary.rename(columns={"index": "columna"})