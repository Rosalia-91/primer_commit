import streamlit as st

from src.config import APP_SUBTITLE, APP_TITLE, VIEWS


def format_currency(value: float) -> str:
    return f"${value:,.2f}"


def format_number(value: float | int) -> str:
    return f"{value:,.0f}"


def format_delta(current: float, previous: float) -> str:
    return f"{current - previous:,.2f}"


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


def render_sidebar(df) -> str:
    st.sidebar.header("Navegación")
    selected_view = st.sidebar.radio("Selecciona una sección", VIEWS)

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