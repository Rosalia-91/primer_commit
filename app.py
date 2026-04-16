import streamlit as st

from src.config import APP_TITLE, DATA_FILE
from src.data_processing import build_analytical_dataset, load_source_tables
from src.sections import (
    render_customers_view,
    render_executive_view,
    render_products_view,
    render_table_view,
    render_trends_view,
)
from src.ui import inject_custom_style, render_header, render_sidebar


def main() -> None:
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon="📊",
        layout="wide"
    )

    inject_custom_style()
    render_header()

    try:
        source_tables = load_source_tables(str(DATA_FILE))
        df = build_analytical_dataset(source_tables)

        selected_view = render_sidebar(df)

        views_map = {
            "Resumen ejecutivo": render_executive_view,
            "Tendencias comerciales": render_trends_view,
            "Análisis de productos": render_products_view,
            "Clientes y segmentos": render_customers_view,
            "Exploración tabular": render_table_view,
        }

        views_map[selected_view](df)

    except FileNotFoundError as error:
        st.error(str(error))
        st.info(
            "Coloca el archivo 'retail_sales_dataset.xlsx' dentro de la carpeta "
            "'data/raw/' y vuelve a ejecutar la aplicación."
        )

    except ValueError as error:
        st.error(str(error))

    except Exception as error:
        st.error(f"Ocurrió un error inesperado: {error}")


if __name__ == "__main__":
    main()