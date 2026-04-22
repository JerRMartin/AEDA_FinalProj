from pathlib import Path
from typing import Optional, Union

import pandas as pd
import streamlit as st


APP_TITLE = "PRISM Evidence Analytics Dashboard"
DATASET_NAME = "PRISM Database Export"
APP_SUBTITLE = "An exploratory dashboard for analyzing evidence quality, coverage, and temporal patterns"
DATASET_SOURCE_TEXT = (
    "local PRISM production database export included in this project (`csv/` tables, exported April 15, 2026). "
    "No public dataset URL was provided with the export."
)
DEFAULT_TOP_N = 10

PRIMARY_ACCENT = "#1D3557"
SECONDARY_ACCENT = "#457B9D"
HIGHLIGHT = "#2A9D8F"
WARM_ACCENT = "#E9C46A"
SOFT_RED = "#D26466"
LIGHT_BG = "#F7F5F2"
CARD_BG = "#FFFFFF"
TEXT_DARK = "#17324D"
MUTED_TEXT = "#6B7B8C"

APP_TEMPLATE = "plotly_white"
QUALITY_SCALE = [
    [0.0, "#EAF2F8"],
    [0.25, "#BFD7EA"],
    [0.5, "#6C9BCF"],
    [0.75, "#2F6690"],
    [1.0, PRIMARY_ACCENT],
]

STATUS_COLOR_MAP = {
    "VALIDATED": PRIMARY_ACCENT,
    "UNVALIDATED": WARM_ACCENT,
    "Unknown": MUTED_TEXT,
}

BASE_CATEGORICAL_PALETTE = [
    PRIMARY_ACCENT,
    SECONDARY_ACCENT,
    HIGHLIGHT,
    WARM_ACCENT,
    SOFT_RED,
    "#7A8E99",
    "#A98467",
]


def build_color_map(categories: list[str]) -> dict[str, str]:
    ordered = sorted(categories)
    return {
        category: BASE_CATEGORICAL_PALETTE[i % len(BASE_CATEGORICAL_PALETTE)]
        for i, category in enumerate(ordered)
    }


def format_compact_number(value: Optional[Union[float, int]]) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    value = float(value)
    if abs(value) >= 1_000_000_000:
        return f"{value / 1_000_000_000:.1f}B"
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if abs(value) >= 1_000:
        return f"{value / 1_000:.1f}K"
    return f"{value:,.0f}"


def format_decimal(value: Optional[Union[float, int]], suffix: str = "") -> str:
    if value is None or pd.isna(value):
        return "N/A"
    return f"{float(value):,.2f}{suffix}"


def format_percent(value: Optional[float]) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    return f"{value:.1%}"


def inject_custom_css(css_path: Path) -> None:
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)


def render_kpi_card(label: str, value: str, delta: str) -> None:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-delta">{delta}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_filter_summary(filtered: pd.DataFrame, full_df: pd.DataFrame) -> None:
    share = len(filtered) / len(full_df) if len(full_df) else 0
    st.markdown(
        f"""
        <div class="summary-banner">
            <strong>Current analytical scope:</strong> {len(filtered):,} records across {filtered['country_name'].nunique():,} countries,
            {filtered['data_point_name'].nunique():,} indicators, and {filtered['document_id'].nunique():,} documents.
            This represents {share:.1%} of the full export after filtering.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty_state() -> None:
    st.warning(
        "The active filters returned zero records. Broaden the year range or restore additional countries, data groups, or validation states."
    )


def make_download_frame(df: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "year",
        "country_name",
        "location_name",
        "location_type",
        "data_group",
        "data_point_name",
        "numeric_value",
        "value",
        "unit",
        "overall_quality_score",
        "validation_status",
        "document_name",
        "organization_country",
        "file_type",
    ]
    existing = [col for col in columns if col in df.columns]
    return df[existing].copy()
