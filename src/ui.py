import streamlit as st

from src.config import DEFAULT_TOP_N, MAX_TOP_N, MIN_TOP_N, APP_SUBTITLE, APP_TITLE, VIEWS


def format_currency(value: float) -> str:
    return f"${value:,.2f}"


def format_number(value: float | int) -> str:
    return f"{value:,.0f}"


def format_delta(current: float, previous: float, is_currency: bool = False) -> str:
    delta = current - previous
    if is_currency:
        return f"${delta:,.2f}"
    return f"{delta:,.0f}"


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
    st.markdown(f'<div class="main-title">{APP_TITLE}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="subtitle">{APP_SUBTITLE}</div>', unsafe_allow_html=True)


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


def render_navigation() -> str:
    st.sidebar.header("Navegación")
    selected_view = st.sidebar.radio("Selecciona una sección", VIEWS)
    return selected_view


def render_filters(filter_options: dict) -> dict:
    st.sidebar.markdown("---")
    st.sidebar.header("Filtros")

    date_range = st.sidebar.date_input(
        "Rango de fechas",
        value=(filter_options["min_date"], filter_options["max_date"]),
        min_value=filter_options["min_date"],
        max_value=filter_options["max_date"],
    )

    regions = st.sidebar.multiselect(
        "Región",
        options=filter_options["regions"],
        default=[]
    )

    categories = st.sidebar.multiselect(
        "Categoría",
        options=filter_options["categories"],
        default=[]
    )

    payment_methods = st.sidebar.multiselect(
        "Método de pago",
        options=filter_options["payment_methods"],
        default=[]
    )

    gender_labels = {
        "M": "Masculino",
        "F": "Femenino"
    }

    genders = st.sidebar.multiselect(
        "Género",
        options=filter_options["genders"],
        default=[],
        format_func=lambda value: gender_labels.get(value, value)
    )

    customer_segments = st.sidebar.multiselect(
        "Segmento de cliente",
        options=filter_options["customer_segments"],
        default=[]
    )

    top_n = st.sidebar.slider(
        "Cantidad para rankings",
        min_value=MIN_TOP_N,
        max_value=MAX_TOP_N,
        value=DEFAULT_TOP_N,
        step=1
    )

    if len(date_range) == 1:
        date_range = (date_range[0], date_range[0])

    return {
        "date_range": date_range,
        "regions": regions,
        "categories": categories,
        "payment_methods": payment_methods,
        "genders": genders,
        "customer_segments": customer_segments,
        "top_n": top_n,
    }


def render_sidebar_status(total_df, filtered_df) -> None:
    st.sidebar.markdown("---")
    st.sidebar.subheader("Estado del dashboard")
    st.sidebar.success("Filtros aplicados correctamente")
    st.sidebar.write(f"Filas filtradas: {filtered_df.shape[0]:,}")
    st.sidebar.write(f"Transacciones filtradas: {filtered_df['TransactionID'].nunique():,}")
    st.sidebar.write(f"Filas totales: {total_df.shape[0]:,}")
    st.sidebar.write(f"Productos visibles: {filtered_df['ProductID'].nunique():,}")


def render_filter_status(total_df, filtered_df, active_filters: list[str], top_n: int) -> None:
    col1, col2, col3 = st.columns(3)
    col1.metric("Filas visibles", f"{filtered_df.shape[0]:,}")
    col2.metric("Transacciones visibles", f"{filtered_df['TransactionID'].nunique():,}")
    col3.metric("Top N actual", f"{top_n}")

    if active_filters:
        filters_text = " | ".join(active_filters)
    else:
        filters_text = "Sin filtros específicos; se está mostrando el rango completo del dataset."

    st.markdown(
        f"""
        <div class="info-box">
        <strong>Contexto actual del análisis:</strong><br>
        {filters_text}<br><br>
        <strong>Rango visible:</strong> {filtered_df['TransactionDate'].min().date()} a
        {filtered_df['TransactionDate'].max().date()}<br>
        <strong>Porcentaje aproximado del dataset visible:</strong>
        {(filtered_df.shape[0] / total_df.shape[0]) * 100:.2f}%
        </div>
        """,
        unsafe_allow_html=True
    )