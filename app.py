import streamlit as st

from src.config import APP_TITLE, DATA_FILE
from src.data_processing import (
    apply_dashboard_filters,
    build_analytical_dataset,
    get_active_filters_summary,
    get_filter_options,
    load_source_tables,
)
from src.sections import (
    render_customers_view,
    render_executive_view,
    render_products_view,
    render_table_view,
    render_trends_view,
)
from src.ui import (
    inject_custom_style,
    render_filter_status,
    render_filters,
    render_header,
    render_navigation,
    render_sidebar_status,
)


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

        selected_view = render_navigation()

        filter_options = get_filter_options(df)
        filters = render_filters(filter_options)

        filtered_df = apply_dashboard_filters(df, filters)
        active_filters = get_active_filters_summary(filters, filter_options["gender_map"])

        render_sidebar_status(df, filtered_df)
        
        if filtered_df.empty:
            st.warning(
                "No hay datos para la combinación de filtros seleccionada. "
                "Ajusta los filtros e inténtalo de nuevo."
            )
            st.stop()

        render_filter_status(df, filtered_df, active_filters, filters["top_n"])

        views_map = {
            "Resumen ejecutivo": lambda data: render_executive_view(data),
            "Tendencias comerciales": lambda data: render_trends_view(data),
            "Análisis de productos": lambda data: render_products_view(data, filters["top_n"]),
            "Clientes y segmentos": lambda data: render_customers_view(data, filters["top_n"]),
            "Exploración tabular": lambda data: render_table_view(data),
        }

        views_map[selected_view](filtered_df)

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