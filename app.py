from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

EXPECTED_SHEETS = ("Customers", "Products", "Stores", "Transactions")

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "raw" / "retail_sales_dataset.xlsx"


def format_currency(value: float) -> str:
    return f"${value:,.2f}"


def format_number(value: float | int) -> str:
    return f"{value:,.0f}"


def format_delta(current: float, previous: float, is_currency: bool = False) -> str:
    delta = current - previous
    if is_currency:
        return f"{delta:,.2f}"
    return f"{delta:,.0f}"


def load_source_tables(file_path: Path) -> dict[str, pd.DataFrame]:
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

    return {
        "Customers": pd.read_excel(file_path, sheet_name="Customers"),
        "Products": pd.read_excel(file_path, sheet_name="Products"),
        "Stores": pd.read_excel(file_path, sheet_name="Stores"),
        "Transactions": pd.read_excel(file_path, sheet_name="Transactions")
    }


def build_analytical_dataset(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    customers = tables["Customers"].copy()
    products = tables["Products"].copy()
    stores = tables["Stores"].copy()
    transactions = tables["Transactions"].copy()

    customers["BirthDate"] = pd.to_datetime(customers["BirthDate"], errors="coerce")
    customers["JoinDate"] = pd.to_datetime(customers["JoinDate"], errors="coerce")
    transactions["Date"] = pd.to_datetime(transactions["Date"], errors="coerce")

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
            "Region": "StoreRegion"
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


def inject_custom_style() -> None:
    st.markdown(
        """
        <style>
        .main-title {
            font-size: 2.1rem;
            font-weight: 700;
            margin-bottom: 0.15rem;
        }

        .subtitle {
            color: #6b7280;
            margin-bottom: 1.2rem;
        }

        .section-title {
            font-size: 1.35rem;
            font-weight: 600;
            margin-top: 0.4rem;
            margin-bottom: 0.7rem;
        }

        .info-box {
            background-color: #f7f9fc;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            padding: 1rem 1.1rem;
            margin-bottom: 1rem;
        }

        .mini-card {
            background-color: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            padding: 0.9rem 1rem;
            margin-bottom: 0.8rem;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
        }

        .mini-card-title {
            font-size: 0.9rem;
            color: #6b7280;
            margin-bottom: 0.2rem;
        }

        .mini-card-value {
            font-size: 1.1rem;
            font-weight: 600;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


def render_header() -> None:
    st.markdown('<div class="main-title">Dashboard Retail + IA</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="subtitle">Día 3 · Diseño visual y navegación básica del dashboard</div>',
        unsafe_allow_html=True
    )


def get_monthly_snapshot(df: pd.DataFrame) -> tuple[dict, dict]:
    monthly = (
        df.groupby("year_month", as_index=False)
        .agg(
            net_sales=("net_sales", "sum"),
            profit=("profit", "sum"),
            transactions=("TransactionID", "nunique")
        )
        .sort_values("year_month")
    )

    monthly["average_ticket"] = monthly["net_sales"] / monthly["transactions"]

    if monthly.shape[0] == 1:
        current = monthly.iloc[-1].to_dict()
        previous = {
            "net_sales": 0.0,
            "profit": 0.0,
            "transactions": 0.0,
            "average_ticket": 0.0,
            "year_month": "Sin periodo previo"
        }
    else:
        current = monthly.iloc[-1].to_dict()
        previous = monthly.iloc[-2].to_dict()

    return current, previous


def build_quality_summary(df: pd.DataFrame) -> pd.DataFrame:
    quality_summary = pd.DataFrame({
        "columna": df.columns,
        "tipo_dato": df.dtypes.astype(str).values,
        "nulos": df.isna().sum().values,
        "porcentaje_nulos": (df.isna().mean() * 100).round(2).values,
        "valores_unicos": df.nunique(dropna=False).values
    })

    return quality_summary.sort_values(
        by=["porcentaje_nulos", "valores_unicos"],
        ascending=[False, False]
    )


def render_mini_card(title: str, value: str) -> None:
    st.markdown(
        f"""
        <div class="mini-card">
            <div class="mini-card-title">{title}</div>
            <div class="mini-card-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_sidebar(df: pd.DataFrame) -> str:
    st.sidebar.header("Navegación")
    selected_view = st.sidebar.radio(
        "Selecciona una sección",
        (
            "Resumen ejecutivo",
            "Tendencias comerciales",
            "Análisis de productos",
            "Clientes y transacciones",
            "Exploración tabular"
        )
    )

    st.sidebar.markdown("---")
    st.sidebar.subheader("Estado del dataset")
    st.sidebar.success("Datos cargados correctamente")
    st.sidebar.write(f"Registros integrados: {df.shape[0]:,}")
    st.sidebar.write(f"Columnas analíticas: {df.shape[1]:,}")
    st.sidebar.write(f"Transacciones únicas: {df['TransactionID'].nunique():,}")
    st.sidebar.write(f"Productos únicos: {df['ProductID'].nunique():,}")
    st.sidebar.write(f"Tiendas únicas: {df['StoreID'].nunique():,}")

    st.sidebar.markdown("---")
    st.sidebar.caption(
        "En esta fase la barra lateral se usa para navegación. "
        "Los filtros interactivos se trabajarán más adelante."
    )

    return selected_view


def render_executive_view(df: pd.DataFrame) -> None:
    st.markdown('<div class="section-title">Resumen ejecutivo</div>', unsafe_allow_html=True)

    current, previous = get_monthly_snapshot(df)

    total_transactions = df["TransactionID"].nunique()
    total_net_sales = df["net_sales"].sum()
    total_profit = df["profit"].sum()
    average_ticket = df["net_sales"].mean()

    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    kpi_col1.metric(
        "Ventas último mes",
        format_currency(current["net_sales"]),
        format_delta(current["net_sales"], previous["net_sales"], is_currency=True)
    )
    kpi_col2.metric(
        "Utilidad último mes",
        format_currency(current["profit"]),
        format_delta(current["profit"], previous["profit"], is_currency=True)
    )
    kpi_col3.metric(
        "Transacciones último mes",
        format_number(current["transactions"]),
        format_delta(current["transactions"], previous["transactions"])
    )
    kpi_col4.metric(
        "Ticket promedio último mes",
        format_currency(current["average_ticket"]),
        format_delta(current["average_ticket"], previous["average_ticket"], is_currency=True)
    )

    st.caption(
        f"Comparación entre {current['year_month']} y "
        f"{previous['year_month'] if previous['year_month'] else 'el periodo anterior'}."
    )

    st.divider()

    summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)
    summary_col1.metric("Ventas netas acumuladas", format_currency(total_net_sales))
    summary_col2.metric("Utilidad acumulada", format_currency(total_profit))
    summary_col3.metric("Transacciones acumuladas", format_number(total_transactions))
    summary_col4.metric("Ticket promedio global", format_currency(average_ticket))

    best_category = (
        df.groupby("Category", as_index=False)["net_sales"]
        .sum()
        .sort_values("net_sales", ascending=False)
        .iloc[0]
    )

    best_region = (
        df.groupby("StoreRegion", as_index=False)["profit"]
        .sum()
        .sort_values("profit", ascending=False)
        .iloc[0]
    )

    best_payment_method = (
        df.groupby("PaymentMethod", as_index=False)["net_sales"]
        .sum()
        .sort_values("net_sales", ascending=False)
        .iloc[0]
    )

    st.divider()

    info_col1, info_col2, info_col3 = st.columns(3)
    with info_col1:
        render_mini_card(
            "Categoría con más ventas",
            f"{best_category['Category']} · {format_currency(best_category['net_sales'])}"
        )
    with info_col2:
        render_mini_card(
            "Región con mayor utilidad",
            f"{best_region['StoreRegion']} · {format_currency(best_region['profit'])}"
        )
    with info_col3:
        render_mini_card(
            "Método de pago dominante",
            f"{best_payment_method['PaymentMethod']} · {format_currency(best_payment_method['net_sales'])}"
        )

    monthly_summary = (
        df.groupby("year_month", as_index=False)
        .agg(
            net_sales=("net_sales", "sum"),
            profit=("profit", "sum"),
            transactions=("TransactionID", "nunique")
        )
        .sort_values("year_month")
    )

    sales_by_payment = (
        df.groupby("PaymentMethod", as_index=False)["net_sales"]
        .sum()
        .sort_values("net_sales", ascending=False)
    )

    tab1, tab2, tab3 = st.tabs(
        ["Tendencia mensual", "Métodos de pago", "Tabla resumen"]
    )

    with tab1:
        fig_monthly_sales = px.line(
            monthly_summary,
            x="year_month",
            y="net_sales",
            markers=True,
            title="Ventas netas por mes"
        )
        st.plotly_chart(fig_monthly_sales, use_container_width=True)

    with tab2:
        fig_payment_method = px.bar(
            sales_by_payment,
            x="PaymentMethod",
            y="net_sales",
            title="Ventas netas por método de pago"
        )
        st.plotly_chart(fig_payment_method, use_container_width=True)

    with tab3:
        st.dataframe(monthly_summary, use_container_width=True, hide_index=True)

    with st.expander("Cómo interpretar esta vista"):
        st.write(
            "Esta sección está diseñada para lectura rápida. Primero se revisa el comportamiento "
            "del último mes, luego el acumulado global y después algunos hallazgos clave del negocio."
        )


def render_trends_view(df: pd.DataFrame) -> None:
    st.markdown('<div class="section-title">Tendencias comerciales</div>', unsafe_allow_html=True)

    sales_by_category = (
        df.groupby("Category", as_index=False)["net_sales"]
        .sum()
        .sort_values("net_sales", ascending=False)
    )

    profit_by_region = (
        df.groupby("StoreRegion", as_index=False)["profit"]
        .sum()
        .sort_values("profit", ascending=False)
    )

    monthly_profit = (
        df.groupby("year_month", as_index=False)["profit"]
        .sum()
        .sort_values("year_month")
    )

    monthly_transactions = (
        df.groupby("year_month", as_index=False)["TransactionID"]
        .nunique()
        .rename(columns={"TransactionID": "transactions"})
        .sort_values("year_month")
    )

    tab1, tab2, tab3 = st.tabs(
        ["Ventas y utilidad", "Regiones y categorías", "Transacciones"]
    )

    with tab1:
        chart_col1, chart_col2 = st.columns(2)

        fig_monthly_profit = px.line(
            monthly_profit,
            x="year_month",
            y="profit",
            markers=True,
            title="Utilidad mensual"
        )

        fig_transactions = px.bar(
            monthly_transactions,
            x="year_month",
            y="transactions",
            title="Transacciones por mes"
        )

        chart_col1.plotly_chart(fig_monthly_profit, use_container_width=True)
        chart_col2.plotly_chart(fig_transactions, use_container_width=True)

    with tab2:
        chart_col3, chart_col4 = st.columns(2)

        fig_category_sales = px.bar(
            sales_by_category,
            x="Category",
            y="net_sales",
            title="Ventas netas por categoría"
        )

        fig_region_profit = px.bar(
            profit_by_region,
            x="StoreRegion",
            y="profit",
            title="Utilidad por región"
        )

        chart_col3.plotly_chart(fig_category_sales, use_container_width=True)
        chart_col4.plotly_chart(fig_region_profit, use_container_width=True)

    with tab3:
        monthly_mix = (
            df.groupby(["year_month", "PaymentMethod"], as_index=False)["net_sales"]
            .sum()
            .sort_values(["year_month", "net_sales"], ascending=[True, False])
        )

        fig_monthly_mix = px.bar(
            monthly_mix,
            x="year_month",
            y="net_sales",
            color="PaymentMethod",
            title="Composición mensual por método de pago"
        )

        st.plotly_chart(fig_monthly_mix, use_container_width=True)

    st.markdown(
        """
        <div class="info-box">
        Esta sección separa el análisis temporal del análisis comparativo. La idea es que el usuario
        pueda distinguir entre comportamiento en el tiempo y diferencias entre categorías o regiones.
        </div>
        """,
        unsafe_allow_html=True
    )


def render_products_view(df: pd.DataFrame) -> None:
    st.markdown('<div class="section-title">Análisis de productos</div>', unsafe_allow_html=True)

    product_summary = (
        df.groupby(["ProductName", "Category", "SubCategory"], as_index=False)
        .agg(
            net_sales=("net_sales", "sum"),
            profit=("profit", "sum"),
            quantity=("Quantity", "sum")
        )
        .sort_values("net_sales", ascending=False)
    )

    top_products = product_summary.head(10)

    subcategory_summary = (
        df.groupby("SubCategory", as_index=False)
        .agg(
            net_sales=("net_sales", "sum"),
            profit=("profit", "sum"),
            quantity=("Quantity", "sum")
        )
        .sort_values("net_sales", ascending=False)
    )

    category_quantity = (
        df.groupby("Category", as_index=False)["Quantity"]
        .sum()
        .sort_values("Quantity", ascending=False)
    )

    top_profitable_products = (
        product_summary.sort_values("profit", ascending=False).head(10)
    )

    tab1, tab2, tab3 = st.tabs(
        ["Productos líderes", "Subcategorías", "Comparativas"]
    )

    with tab1:
        chart_col1, chart_col2 = st.columns(2)

        fig_top_products = px.bar(
            top_products.sort_values("net_sales"),
            x="net_sales",
            y="ProductName",
            orientation="h",
            title="Top 10 productos por ventas netas"
        )

        fig_top_profit_products = px.bar(
            top_profitable_products.sort_values("profit"),
            x="profit",
            y="ProductName",
            orientation="h",
            title="Top 10 productos por utilidad"
        )

        chart_col1.plotly_chart(fig_top_products, use_container_width=True)
        chart_col2.plotly_chart(fig_top_profit_products, use_container_width=True)

    with tab2:
        chart_col3, chart_col4 = st.columns(2)

        fig_subcategory_sales = px.bar(
            subcategory_summary.head(10).sort_values("net_sales"),
            x="net_sales",
            y="SubCategory",
            orientation="h",
            title="Top 10 subcategorías por ventas netas"
        )

        fig_subcategory_profit = px.bar(
            subcategory_summary.sort_values("profit", ascending=False).head(10).sort_values("profit"),
            x="profit",
            y="SubCategory",
            orientation="h",
            title="Top 10 subcategorías por utilidad"
        )

        chart_col3.plotly_chart(fig_subcategory_sales, use_container_width=True)
        chart_col4.plotly_chart(fig_subcategory_profit, use_container_width=True)

    with tab3:
        chart_col5, chart_col6 = st.columns(2)

        fig_category_quantity = px.bar(
            category_quantity,
            x="Category",
            y="Quantity",
            title="Cantidad vendida por categoría"
        )

        fig_product_scatter = px.scatter(
            product_summary.head(50),
            x="quantity",
            y="net_sales",
            size="profit",
            hover_name="ProductName",
            title="Relación entre cantidad, ventas y utilidad"
        )

        chart_col5.plotly_chart(fig_category_quantity, use_container_width=True)
        chart_col6.plotly_chart(fig_product_scatter, use_container_width=True)

    st.dataframe(
        top_products[["ProductName", "Category", "SubCategory", "quantity", "net_sales", "profit"]],
        use_container_width=True,
        hide_index=True
    )


def render_customers_view(df: pd.DataFrame) -> None:
    st.markdown('<div class="section-title">Clientes y transacciones</div>', unsafe_allow_html=True)

    customer_label = "CustomerName" if "CustomerName" in df.columns else "CustomerID"

    customer_summary = (
        df.groupby(["CustomerID", customer_label], as_index=False)
        .agg(
            transactions=("TransactionID", "nunique"),
            net_sales=("net_sales", "sum"),
            profit=("profit", "sum"),
            quantity=("Quantity", "sum")
        )
        .sort_values("net_sales", ascending=False)
    )

    top_customers = customer_summary.head(10)
    most_active_customers = customer_summary.sort_values("transactions", ascending=False).head(10)

    ticket_distribution = customer_summary.copy()
    ticket_distribution["avg_ticket_customer"] = (
        ticket_distribution["net_sales"] / ticket_distribution["transactions"]
    )

    tab1, tab2, tab3 = st.tabs(
        ["Clientes con más ventas", "Clientes más activos", "Distribución"]
    )

    with tab1:
        fig_top_customers = px.bar(
            top_customers.sort_values("net_sales"),
            x="net_sales",
            y=customer_label,
            orientation="h",
            title="Top 10 clientes por ventas netas"
        )
        st.plotly_chart(fig_top_customers, use_container_width=True)

    with tab2:
        fig_most_active = px.bar(
            most_active_customers.sort_values("transactions"),
            x="transactions",
            y=customer_label,
            orientation="h",
            title="Top 10 clientes por número de transacciones"
        )
        st.plotly_chart(fig_most_active, use_container_width=True)

    with tab3:
        fig_customer_ticket = px.histogram(
            ticket_distribution,
            x="avg_ticket_customer",
            nbins=20,
            title="Distribución del ticket promedio por cliente"
        )
        st.plotly_chart(fig_customer_ticket, use_container_width=True)

    st.dataframe(
        customer_summary.head(20),
        use_container_width=True,
        hide_index=True
    )


def render_table_view(df: pd.DataFrame) -> None:
    st.markdown('<div class="section-title">Exploración tabular</div>', unsafe_allow_html=True)

    quality_summary = build_quality_summary(df)
    numeric_summary = df.select_dtypes(include="number").describe().T.reset_index()
    numeric_summary = numeric_summary.rename(columns={"index": "columna"})

    preview_tab, schema_tab, quality_tab, stats_tab = st.tabs(
        ["Vista previa", "Esquema", "Calidad de datos", "Estadística descriptiva"]
    )

    with preview_tab:
        preview_col1, preview_col2, preview_col3 = st.columns(3)
        preview_col1.metric("Filas", format_number(df.shape[0]))
        preview_col2.metric("Columnas", format_number(df.shape[1]))
        preview_col3.metric("Productos únicos", format_number(df["ProductID"].nunique()))
        st.dataframe(df.head(50), use_container_width=True)

    with schema_tab:
        schema_df = pd.DataFrame({
            "columna": df.columns,
            "tipo_dato": df.dtypes.astype(str).values
        })
        st.dataframe(schema_df, use_container_width=True, hide_index=True)

    with quality_tab:
        st.dataframe(quality_summary, use_container_width=True, hide_index=True)

        duplicate_transactions = df["TransactionID"].duplicated().sum()
        st.info(f"Transacciones duplicadas por TransactionID: {duplicate_transactions:,}")

    with stats_tab:
        st.dataframe(numeric_summary, use_container_width=True, hide_index=True)

    with st.expander("Qué debe aprender el alumno en esta vista"):
        st.write(
            "Esta vista no está pensada para el usuario final del negocio, sino para que el alumno "
            "entienda qué tipo de tabla está alimentando el dashboard, qué columnas tiene, "
            "qué calidad presentan y qué métricas numéricas resumen su contenido."
        )


st.set_page_config(
    page_title="Dashboard Retail + IA",
    page_icon="📊",
    layout="wide"
)

inject_custom_style()
render_header()

try:
    source_tables = load_source_tables(DATA_FILE)
    df = build_analytical_dataset(source_tables)

    selected_view = render_sidebar(df)

    if selected_view == "Resumen ejecutivo":
        render_executive_view(df)
    elif selected_view == "Tendencias comerciales":
        render_trends_view(df)
    elif selected_view == "Análisis de productos":
        render_products_view(df)
    elif selected_view == "Clientes y transacciones":
        render_customers_view(df)
    else:
        render_table_view(df)

except FileNotFoundError as error:
    st.error(str(error))
    st.info(
        "Coloca el archivo 'retail_sales_dataset.xlsx' dentro de la carpeta 'data/raw/' "
        "y vuelve a ejecutar la aplicación."
    )

except ValueError as error:
    st.error(str(error))

except Exception as error:
    st.error(f"Ocurrió un error inesperado: {error}")