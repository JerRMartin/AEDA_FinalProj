from pathlib import Path

import pandas as pd
import streamlit as st

from src.charts import (
    create_bar_chart,
    create_box_plot,
    create_correlation_heatmap,
    create_distribution_chart,
    create_donut_chart,
    create_scatter_chart,
    create_trend_chart,
)
from src.data_loader import get_analysis_dataset, get_data_dictionary
from src.metrics import build_insight_text, compute_kpis
from src.utils import (
    APP_SUBTITLE,
    APP_TITLE,
    DATASET_NAME,
    DATASET_SOURCE_TEXT,
    DEFAULT_TOP_N,
    inject_custom_css,
    make_download_frame,
    render_empty_state,
    render_filter_summary,
    render_kpi_card,
)


st.set_page_config(
    page_title="PRISM Analytical Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


def initialize_state(df: pd.DataFrame) -> None:
    min_year = int(df["year"].min())
    max_year = int(df["year"].max())

    defaults = {
        "year_range": (min_year, max_year),
        "selected_groups": sorted(df["data_group"].dropna().unique().tolist()),
        "selected_countries": sorted(df["country_name"].dropna().unique().tolist()),
        "selected_statuses": sorted(df["validation_status"].dropna().unique().tolist()),
        "numeric_only": False,
        "top_n": DEFAULT_TOP_N,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_filters(df: pd.DataFrame) -> None:
    min_year = int(df["year"].min())
    max_year = int(df["year"].max())
    st.session_state.year_range = (min_year, max_year)
    st.session_state.selected_groups = sorted(df["data_group"].dropna().unique().tolist())
    st.session_state.selected_countries = sorted(df["country_name"].dropna().unique().tolist())
    st.session_state.selected_statuses = sorted(df["validation_status"].dropna().unique().tolist())
    st.session_state.numeric_only = False
    st.session_state.top_n = DEFAULT_TOP_N


def filter_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    filtered = df.copy()
    year_start, year_end = st.session_state.year_range
    filtered = filtered[filtered["year"].between(year_start, year_end)]
    filtered = filtered[filtered["data_group"].isin(st.session_state.selected_groups)]
    filtered = filtered[filtered["country_name"].isin(st.session_state.selected_countries)]
    filtered = filtered[filtered["validation_status"].isin(st.session_state.selected_statuses)]

    if st.session_state.numeric_only:
        filtered = filtered[filtered["is_numeric_value"]]

    return filtered


def render_header() -> None:
    st.title(APP_TITLE)
    st.caption(f"{DATASET_NAME} | {APP_SUBTITLE}")


    st.markdown("### Data Dictionary")
    with st.expander("Data dictionary for dashboard fields"):
        st.dataframe(get_data_dictionary(), use_container_width=True, hide_index=True)


def render_sidebar(df: pd.DataFrame) -> None:
    st.sidebar.header("Filter Panel")

    if st.sidebar.button("Reset filters", use_container_width=True, type="secondary"):
        reset_filters(df)

    st.sidebar.multiselect(
        "Data groups",
        options=sorted(df["data_group"].dropna().unique().tolist()),
        key="selected_groups",
    )
    st.sidebar.multiselect(
        "Countries",
        options=sorted(df["country_name"].dropna().unique().tolist()),
        key="selected_countries",
    )
    st.sidebar.multiselect(
        "Validation status",
        options=sorted(df["validation_status"].dropna().unique().tolist()),
        key="selected_statuses",
    )
    st.sidebar.checkbox("Numeric observations only", key="numeric_only")
    st.sidebar.slider("Top-N categories for ranking charts", 5, 20, key="top_n")
    st.sidebar.slider(
        "Observation year range",
        min_value=int(df["year"].min()),
        max_value=int(df["year"].max()),
        key="year_range",
    )


def main() -> None:
    inject_custom_css(Path("assets/theme.css"))
    dataset = get_analysis_dataset(Path("."))
    initialize_state(dataset)
    render_header()
    render_sidebar(dataset)

    filtered = filter_dataframe(dataset)
    render_filter_summary(filtered, dataset)

    if filtered.empty:
        render_empty_state()
        return

    kpis = compute_kpis(filtered)
    kpi_cols = st.columns(5)
    for col, metric in zip(kpi_cols, kpis):
        with col:
            render_kpi_card(metric["label"], metric["value"], metric["delta"])

    st.markdown("### Analytical Overview")
    st.write(
        "The opening view summarizes evidence volume, topical composition, validation status, and quality dispersion before moving into relationships and trends."
    )

    overview_left, overview_right = st.columns((1.3, 1))
    with overview_left:
        st.plotly_chart(
            create_bar_chart(filtered, top_n=st.session_state.top_n),
            use_container_width=True,
        )
        st.caption(
            "Amount chart: ranks the most prevalent indicators in the active filtered view to reveal which measures dominate the evidence base."
        )
    with overview_right:
        st.plotly_chart(
            create_donut_chart(filtered),
            use_container_width=True,
        )
        st.caption(
            "Proportion chart: shows the validation mix so the viewer can quickly assess evidence verification in the current slice."
        )

    tab_overview, tab_relationships, tab_trends = st.tabs(
        ["Overview", "Relationships", "Trends & Export"]
    )

    with tab_overview:
        dist_col, box_col = st.columns(2)
        with dist_col:
            st.plotly_chart(
                create_distribution_chart(filtered),
                use_container_width=True,
            )
            st.caption(
                "Distribution chart: examines how overall quality scores are spread, including concentration and tail behavior."
            )
        with box_col:
            st.plotly_chart(
                create_box_plot(filtered),
                use_container_width=True,
            )
            st.caption(
                "Distribution by group: compares quality score dispersion across PRISM data groups to highlight variation and outliers."
            )

    with tab_relationships:
        scatter_col, heatmap_col = st.columns(2)
        with scatter_col:
            st.plotly_chart(
                create_scatter_chart(filtered),
                use_container_width=True,
            )
            st.caption(
                "Association chart: compares source credibility and overall quality, making it easier to see whether stronger sources align with stronger records."
            )
        with heatmap_col:
            st.plotly_chart(
                create_correlation_heatmap(filtered),
                use_container_width=True,
            )
            st.caption(
                "Association matrix: summarizes score correlations among the extraction quality dimensions used in the PRISM pipeline."
            )

    with tab_trends:
        st.plotly_chart(
            create_trend_chart(filtered),
            use_container_width=True,
        )
        st.caption(
            "Evolution chart: tracks annual extraction volume and mean quality, supporting temporal comparisons within the selected analytical slice."
        )

        st.markdown("### Key Insights")
        st.info(build_insight_text(filtered))

        st.markdown("### Download Filtered Dataset")

        download_df = make_download_frame(filtered)
        st.download_button(
            "Download filtered dataset as CSV",
            data=download_df.to_csv(index=False).encode("utf-8"),
            file_name="prism_filtered_dashboard_view.csv",
            mime="text/csv",
            use_container_width=False,
        )

if __name__ == "__main__":
    main()
