from pathlib import Path

import pandas as pd
import streamlit as st

from src.charts import (
    create_correlation_heatmap,
    create_data_points_by_group,
    create_documents_by_country,
    create_documents_by_filetype,
    create_documents_by_year,
    create_extraction_quality_histogram,
    create_extraction_validation_donut,
    create_extractions_by_year,
    create_infra_by_status,
    create_infra_by_type,
    create_infra_choropleth,
    create_message_sender_donut,
    create_message_wordcloud,
    create_locations_by_country_type,
    create_locations_by_type,
    create_messages_timeline,
    create_projects_by_countries,
    create_projects_by_status,
    create_scatter_chart,
    create_trend_chart,
)
from src.data_loader import (
    RAW_TABLE_TABS,
    get_analysis_dataset,
    get_key_terms,
    load_raw_table,
)
from src.metrics import build_insight_text, compute_kpis
from src.utils import (
    APP_SUBTITLE,
    APP_TITLE,
    DATASET_NAME,
    DEFAULT_TOP_N,
    inject_custom_css,
    make_download_frame,
    render_caption,
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


def apply_sidebar_filters(df: pd.DataFrame) -> pd.DataFrame:
    filtered = df.copy()
    year_start, year_end = st.session_state.year_range

    if "year" in filtered.columns:
        filtered = filtered[
            pd.to_numeric(filtered["year"], errors="coerce").between(year_start, year_end)
        ]
    elif "reported_year" in filtered.columns:
        filtered = filtered[
            pd.to_numeric(filtered["reported_year"], errors="coerce").between(year_start, year_end)
        ]

    if "validation_status" in filtered.columns:
        filtered = filtered[filtered["validation_status"].isin(st.session_state.selected_statuses)]

    return filtered


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
    st.sidebar.slider(
        "Observation year range",
        min_value=int(df["year"].min()),
        max_value=int(df["year"].max()),
        key="year_range",
    )
def render_kpis(df: pd.DataFrame) -> None:
    filtered = filter_dataframe(df)
    render_filter_summary(filtered, df)

    if filtered.empty:
        render_empty_state()
        return

    kpis = compute_kpis(filtered)
    kpi_cols = st.columns(5)
    for col, metric in zip(kpi_cols, kpis):
        with col:
            render_kpi_card(metric["label"], metric["value"], metric["delta"])


def render_analytics(dataset: pd.DataFrame) -> None:
    st.markdown("### Analytical Overview")
    filtered = filter_dataframe(dataset)

    if filtered.empty:
        render_empty_state()
        return

    scatter_col, heatmap_col = st.columns(2)
    with scatter_col:
        st.plotly_chart(
            create_scatter_chart(filtered),
            use_container_width=True,
        )

    with heatmap_col:
        st.plotly_chart(
            create_correlation_heatmap(filtered),
            use_container_width=True,
        )

    st.plotly_chart(
        create_trend_chart(filtered),
        use_container_width=True,
    )

    with st.expander("Key Terms and Acronyms"):
        st.dataframe(get_key_terms(), use_container_width=True, hide_index=True)

def _render_chat_messages(df: pd.DataFrame) -> None:
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(create_message_wordcloud(df), use_container_width=True)
    with col2:
        st.plotly_chart(create_message_sender_donut(df), use_container_width=True)
    st.plotly_chart(create_messages_timeline(df), use_container_width=True)



def _render_data_extractions(df: pd.DataFrame) -> None:
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(create_extractions_by_year(df), use_container_width=True)
    with col2:
        st.plotly_chart(create_extraction_validation_donut(df), use_container_width=True)
    st.plotly_chart(create_extraction_quality_histogram(df), use_container_width=True)


def _render_data_points(df: pd.DataFrame) -> None:
    st.plotly_chart(create_data_points_by_group(df), use_container_width=True)


def _render_documents(df: pd.DataFrame) -> None:
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(create_documents_by_filetype(df), use_container_width=True)
    with col2:
        st.plotly_chart(create_documents_by_year(df), use_container_width=True)
    st.plotly_chart(
        create_documents_by_country(df, top_n=st.session_state.top_n),
        use_container_width=True,
    )


def _render_infrastructures(df: pd.DataFrame) -> None:
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(create_infra_by_type(df), use_container_width=True)
    with col2:
        st.plotly_chart(create_infra_by_status(df), use_container_width=True)
    st.plotly_chart(create_infra_choropleth(df), use_container_width=True)


def _render_locations(df: pd.DataFrame) -> None:
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(create_locations_by_type(df), use_container_width=True)
    with col2:
        st.plotly_chart(create_locations_by_country_type(df), use_container_width=True)


def _render_projects(df: pd.DataFrame) -> None:
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(create_projects_by_status(df), use_container_width=True)
    with col2:
        st.plotly_chart(create_projects_by_countries(df), use_container_width=True)


_CSV_CHART_RENDERERS = {
    "chat_messages": _render_chat_messages,
    "data_extractions": _render_data_extractions,
    "data_points": _render_data_points,
    "documents": _render_documents,
    "infrastructures": _render_infrastructures,
    "locations": _render_locations,
    "projects": _render_projects,
}


def render_csv_tab(tab_label: str, file_name: str, df: pd.DataFrame) -> None:

    filtered = apply_sidebar_filters(df)
    if file_name in _CSV_CHART_RENDERERS:
        _CSV_CHART_RENDERERS[file_name](filtered)

    total, visible = len(df), len(filtered)
    suffix = f" · {visible:,} of {total:,} rows after filters" if visible != total else f" · {total:,} rows"
    render_caption(f"{len(df.columns)} columns{suffix}")
    st.dataframe(filtered, use_container_width=True, hide_index=True)

    terms = get_key_terms(tab_label)
    if not terms.empty:
        with st.expander("Key Terms and Acronyms"):
            st.dataframe(terms, use_container_width=True, hide_index=True)


def render_insights_and_download(df: pd.DataFrame) -> None:
    filtered = filter_dataframe(df)
    col1, col2 = st.columns([0.7, 0.3])
    with col1:
            st.markdown("### Key Insights")
            st.info(build_insight_text(filtered))
    with col2:
        st.markdown("### Download Filtered Dataset")
        download_df = make_download_frame(filtered)
        st.download_button(
            "Download filtered dataset as CSV",
            data=download_df.to_csv(index=False).encode("utf-8"),
            file_name="prism_filtered_dashboard_view.csv",
            mime="text/csv",
            use_container_width=False,
        )


def main() -> None:
    inject_custom_css(Path("assets/theme.css"))
    dataset = get_analysis_dataset(Path("."))
    initialize_state(dataset)
    render_sidebar(dataset)

    st.title(APP_TITLE)
    st.caption(f"{DATASET_NAME} | {APP_SUBTITLE}")
    render_kpis(dataset)
    st.space("medium")

    tab_names = ["Analytics"] + [label for label, *_ in RAW_TABLE_TABS] + ["Insights & Download"]
    tabs = st.tabs(tab_names)

    with tabs[0]:
        render_analytics(dataset)

    for tab, (tab_label, file_name, exclude_cols) in zip(tabs[1:-1], RAW_TABLE_TABS):
        with tab:
            df = load_raw_table(Path("."), file_name)
            if exclude_cols:
                df = df.drop(columns=[c for c in exclude_cols if c in df.columns])
            render_csv_tab(tab_label, file_name, df)

    with tabs[-1]:
        render_insights_and_download(dataset)


if __name__ == "__main__":
    main()