import plotly.express as px
import streamlit as st

from src.data_processing import (
    get_category_quantity,
    get_customer_segment_sales,
    get_customer_summary,
    get_executive_metrics,
    get_gender_sales,
    get_monthly_payment_mix,
    get_monthly_snapshot,
    get_monthly_summary,
    get_monthly_transactions,
    get_numeric_summary,
    get_product_summary,
    get_profit_by_region,
    get_quality_summary,
    get_sales_by_category,
    get_sales_by_payment,
    get_subcategory_summary,
)
from src.ui import format_currency, format_delta, format_number, render_mini_card


def render_executive_view(df) -> None:
    st.markdown('<div class="section-title">Resumen ejecutivo</div>', unsafe_allow_html=True)

    metrics = get_executive_metrics(df)
    current, previous = get_monthly_snapshot(df)

    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    kpi_col1.metric(
        "Ventas último mes",
        format_currency(current["net_sales"]),
        format_delta(current["net_sales"], previous["net_sales"], is_currency=True),
    )
    kpi_col2.metric(
        "Utilidad último mes",
        format_currency(current["profit"]),
        format_delta(current["profit"], previous["profit"], is_currency=True),
    )
    kpi_col3.metric(
        "Transacciones último mes",
        format_number(current["transactions"]),
        format_delta(current["transactions"], previous["transactions"]),
    )
    kpi_col4.metric(
        "Ticket promedio último mes",
        format_currency(current["average_ticket"]),
        format_delta(current["average_ticket"], previous["average_ticket"], is_currency=True),
    )

    st.caption(
        f"Comparación entre {current['year_month']} y {previous['year_month']}."
    )

    st.divider()

    summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)
    summary_col1.metric("Ventas netas acumuladas", format_currency(metrics["net_sales"]))
    summary_col2.metric("Utilidad acumulada", format_currency(metrics["profit"]))
    summary_col3.metric("Transacciones acumuladas", format_number(metrics["transactions"]))
    summary_col4.metric("Ticket promedio global", format_currency(metrics["average_ticket"]))

    best_category = get_sales_by_category(df).iloc[0]
    best_region = get_profit_by_region(df).iloc[0]
    best_payment_method = get_sales_by_payment(df).iloc[0]

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

    monthly_summary = get_monthly_summary(df)
    sales_by_payment = get_sales_by_payment(df)

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


def render_trends_view(df) -> None:
    st.markdown('<div class="section-title">Tendencias comerciales</div>', unsafe_allow_html=True)

    sales_by_category = get_sales_by_category(df)
    profit_by_region = get_profit_by_region(df)
    monthly_summary = get_monthly_summary(df)
    monthly_transactions = get_monthly_transactions(df)
    monthly_mix = get_monthly_payment_mix(df)

    tab1, tab2, tab3 = st.tabs(
        ["Ventas y utilidad", "Regiones y categorías", "Transacciones"]
    )

    with tab1:
        chart_col1, chart_col2 = st.columns(2)

        fig_monthly_profit = px.line(
            monthly_summary,
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
        fig_monthly_mix = px.bar(
            monthly_mix,
            x="year_month",
            y="net_sales",
            color="PaymentMethod",
            title="Composición mensual por método de pago"
        )
        st.plotly_chart(fig_monthly_mix, use_container_width=True)


def render_products_view(df, top_n: int) -> None:
    st.markdown('<div class="section-title">Análisis de productos</div>', unsafe_allow_html=True)

    product_summary = get_product_summary(df)
    subcategory_summary = get_subcategory_summary(df)
    category_quantity = get_category_quantity(df)

    top_products = product_summary.head(top_n)
    top_profit_products = product_summary.sort_values("profit", ascending=False).head(top_n)

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
            title=f"Top {top_n} productos por ventas netas"
        )

        fig_top_profit_products = px.bar(
            top_profit_products.sort_values("profit"),
            x="profit",
            y="ProductName",
            orientation="h",
            title=f"Top {top_n} productos por utilidad"
        )

        chart_col1.plotly_chart(fig_top_products, use_container_width=True)
        chart_col2.plotly_chart(fig_top_profit_products, use_container_width=True)

    with tab2:
        chart_col3, chart_col4 = st.columns(2)

        fig_subcategory_sales = px.bar(
            subcategory_summary.head(top_n).sort_values("net_sales"),
            x="net_sales",
            y="SubCategory",
            orientation="h",
            title=f"Top {top_n} subcategorías por ventas netas"
        )

        fig_subcategory_profit = px.bar(
            subcategory_summary.sort_values("profit", ascending=False).head(top_n).sort_values("profit"),
            x="profit",
            y="SubCategory",
            orientation="h",
            title=f"Top {top_n} subcategorías por utilidad"
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


def render_customers_view(df, top_n: int) -> None:
    st.markdown('<div class="section-title">Clientes y segmentos</div>', unsafe_allow_html=True)

    customer_summary = get_customer_summary(df)
    segment_sales = get_customer_segment_sales(df)
    gender_sales = get_gender_sales(df)

    customer_label = "CustomerFullName" if "CustomerFullName" in customer_summary.columns else "CustomerID"

    top_customers = customer_summary.head(top_n)
    most_active_customers = customer_summary.sort_values("transactions", ascending=False).head(top_n)

    ticket_distribution = customer_summary.copy()
    ticket_distribution["avg_ticket_customer"] = (
        ticket_distribution["net_sales"] / ticket_distribution["transactions"]
    )

    tab1, tab2, tab3 = st.tabs(
        ["Segmentos y clientes", "Perfil del cliente", "Tabla resumen"]
    )

    with tab1:
        chart_col1, chart_col2 = st.columns(2)

        fig_segment_sales = px.bar(
            segment_sales,
            x="CustomerSegment",
            y="net_sales",
            title="Ventas netas por segmento de cliente"
        )

        fig_top_customers = px.bar(
            top_customers.sort_values("net_sales"),
            x="net_sales",
            y=customer_label,
            orientation="h",
            title=f"Top {top_n} clientes por ventas netas"
        )

        chart_col1.plotly_chart(fig_segment_sales, use_container_width=True)
        chart_col2.plotly_chart(fig_top_customers, use_container_width=True)

    with tab2:
        chart_col3, chart_col4 = st.columns(2)

        if not gender_sales.empty:
            fig_gender_sales = px.bar(
                gender_sales,
                x="GenderLabel",
                y="net_sales",
                title="Ventas netas por género"
            )
            chart_col3.plotly_chart(fig_gender_sales, use_container_width=True)
        else:
            chart_col3.info("No hay información de género disponible.")

        fig_customer_ticket = px.histogram(
            ticket_distribution,
            x="avg_ticket_customer",
            nbins=20,
            title="Distribución del ticket promedio por cliente"
        )
        chart_col4.plotly_chart(fig_customer_ticket, use_container_width=True)

        st.plotly_chart(
            px.bar(
                most_active_customers.sort_values("transactions"),
                x="transactions",
                y=customer_label,
                orientation="h",
                title=f"Top {top_n} clientes por número de transacciones"
            ),
            use_container_width=True
        )

    with tab3:
        columns_to_show = [
            col for col in [
                "CustomerID",
                customer_label,
                "Gender",
                "CustomerSegment",
                "transactions",
                "net_sales",
                "profit"
            ] if col in customer_summary.columns
        ]

        st.dataframe(
            customer_summary[columns_to_show].head(20),
            use_container_width=True,
            hide_index=True
        )


def render_table_view(df) -> None:
    st.markdown('<div class="section-title">Exploración tabular</div>', unsafe_allow_html=True)

    quality_summary = get_quality_summary(df)
    numeric_summary = get_numeric_summary(df)

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
        schema_df = quality_summary[["columna", "tipo_dato"]]
        st.dataframe(schema_df, use_container_width=True, hide_index=True)

    with quality_tab:
        st.dataframe(quality_summary, use_container_width=True, hide_index=True)
        duplicate_transactions = df["TransactionID"].duplicated().sum()
        st.info(f"Transacciones duplicadas por TransactionID: {duplicate_transactions:,}")

    with stats_tab:
        st.dataframe(numeric_summary, use_container_width=True, hide_index=True)