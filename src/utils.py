import re
from pathlib import Path
from typing import Optional, Union

import pandas as pd
import streamlit as st


APP_TITLE = "Plastics Recovery Insights Steering Model (PRISM) Evidence Analytics Dashboard"
DATASET_NAME = "PRISM Dataset"
APP_SUBTITLE = "An exploratory dashboard for analyzing evidence quality, coverage, and temporal patterns"
DATASET_SOURCE_TEXT = (
    "local PRISM production database export included in this project (`csv/` tables, exported April 15, 2026). "
    "No public dataset URL was provided with the export."
)
DEFAULT_TOP_N = 12

PRIMARY_ACCENT = "#1D3557"
SECONDARY_ACCENT = "#457B9D"
HIGHLIGHT = "#2A9D8F"
WARM_ACCENT = "#E9C46A"
SOFT_RED = "#D26466"
LIGHT_BG = "#F7F5F2"
CARD_BG = "#FFFFFF"
TEXT_DARK = "#17324D"
MUTED_TEXT = "#6B7B8C"

_CSS_VARS: dict[str, str] = {
    "--primary-accent": PRIMARY_ACCENT,
    "--secondary-accent": SECONDARY_ACCENT,
    "--highlight": HIGHLIGHT,
    "--warm-accent": WARM_ACCENT,
    "--soft-red": SOFT_RED,
    "--light-bg": LIGHT_BG,
    "--card-bg": CARD_BG,
    "--text-dark": TEXT_DARK,
    "--muted-text": MUTED_TEXT,
}

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


ACRONYM_GLOSSARY: dict[str, str] = {
    "ABS":   "Acrylonitrile Butadiene Styrene",
    "AEPW":  "Alliance to End Plastic Waste",
    "AI":    "Artificial Intelligence",
    "BAU":   "Business As Usual",
    "CPCB":  "Central Pollution Control Board",
    "CSIRO": "Commonwealth Scientific and Industrial Research Organisation",
    "EDA":   "Exploratory Data Analysis",
    "EPA":   "Environmental Protection Agency",
    "GDP":   "Gross Domestic Product",
    "GIZ":   "Deutsche Gesellschaft für Internationale Zusammenarbeit",
    "HDPE":  "High-Density Polyethylene",
    "ISWM":  "Integrated Solid Waste Management",
    "IUCN":  "International Union for Conservation of Nature",
    "IWC":   "Informal Waste Collector",
    "JWT":   "JSON Web Token",
    "LDPE":  "Low-Density Polyethylene",
    "MLP":   "Multi-Layered Plastic",
    "MSW":   "Municipal Solid Waste",
    "MVP":   "Minimum Viable Product",
    "NGO":   "Non-Governmental Organization",
    "OECD":  "Organisation for Economic Co-operation and Development",
    "PC":    "Polycarbonate",
    "PCR":   "Post-Consumer Recycled",
    "PCX":   "Plastic Credit Exchange",
    "PET":   "Polyethylene Terephthalate",
    "PP":    "Polypropylene",
    "PRISM": "Plastics Recovery Insights Steering Model",
    "PS":    "Polystyrene",
    "PVC":   "Polyvinyl Chloride",
    "PW":    "Plastic Waste",
    "SUP":   "Single-Use Plastic",
    "TCI":   "The Circulate Initiative",
    "UNCRD": "United Nations Centre for Regional Development",
    "UNEP":  "United Nations Environment Programme",
    "WaCT":  "Waste Wise City Tool",
}

# Sort longest first so "PRISM" is tried before "PS", "PCR" before "PC", etc.
_ACRONYM_RE = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in sorted(ACRONYM_GLOSSARY, key=len, reverse=True)) + r")\b"
)


def acronymize(text: str) -> str:
    return _ACRONYM_RE.sub(
        lambda m: f'<abbr title="{ACRONYM_GLOSSARY[m.group()]}">{m.group()}</abbr>',
        text,
    )


def render_caption(text: str) -> None:
    st.markdown(f'<p class="app-caption">{acronymize(text)}</p>', unsafe_allow_html=True)


def inject_custom_css(css_path: Path) -> None:
    if css_path.exists():
        root_block = ":root {\n" + "".join(f"  {k}: {v};\n" for k, v in _CSS_VARS.items()) + "}\n"
        st.markdown(f"<style>{root_block}{css_path.read_text()}</style>", unsafe_allow_html=True)


def render_kpi_card(label: str, value: str, delta: str) -> None:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{acronymize(label)}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-delta">{acronymize(delta)}</div>
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
