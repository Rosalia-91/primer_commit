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
        suffixes=("_Customer", "_Store")
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

    return analytical_df


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

    customer_summary = (
        df.groupby(group_cols, as_index=False)
        .agg(
            transactions=("TransactionID", "nunique"),
            net_sales=("net_sales", "sum"),
            profit=("profit", "sum"),
            quantity=("Quantity", "sum"),
        )
        .sort_values("net_sales", ascending=False)
    )

    return customer_summary


def add_customer_segment(customer_summary: pd.DataFrame) -> pd.DataFrame:
    segmented = customer_summary.copy()

    ranked_sales = segmented["net_sales"].rank(method="first")
    segmented["CustomerSegment"] = pd.qcut(
        ranked_sales,
        q=3,
        labels=["Bajo", "Medio", "Alto"]
    )

    return segmented


def get_customer_segmented_summary(df: pd.DataFrame) -> pd.DataFrame:
    customer_summary = get_customer_summary(df)
    return add_customer_segment(customer_summary)


def get_customer_segment_sales(df: pd.DataFrame) -> pd.DataFrame:
    segmented = get_customer_segmented_summary(df)

    segment_sales = (
        segmented.groupby("CustomerSegment", as_index=False)["net_sales"]
        .sum()
    )

    order_map = {"Bajo": 0, "Medio": 1, "Alto": 2}
    segment_sales["segment_order"] = segment_sales["CustomerSegment"].astype(str).map(order_map)
    segment_sales = segment_sales.sort_values("segment_order").drop(columns="segment_order")

    return segment_sales


def get_gender_sales(df: pd.DataFrame) -> pd.DataFrame:
    if "Gender" not in df.columns:
        return pd.DataFrame(columns=["Gender", "net_sales"])

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