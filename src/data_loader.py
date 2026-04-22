from pathlib import Path

import pandas as pd
import streamlit as st

from src.preprocessing import build_analysis_dataset


REQUIRED_TABLES = {
    "data_extractions": "csv/data_extractions",
    "documents": "csv/documents",
    "data_points": "csv/data_points",
    "locations": "csv/locations",
}


@st.cache_data(show_spinner="Loading and preprocessing PRISM tables...")
def load_raw_tables(base_path: Path) -> dict[str, pd.DataFrame]:
    tables = {}
    for name, relative_path in REQUIRED_TABLES.items():
        path = base_path / relative_path
        tables[name] = pd.read_csv(path)
    return tables


@st.cache_data(show_spinner="Building analysis dataset...")
def get_analysis_dataset(base_path: Path) -> pd.DataFrame:
    raw_tables = load_raw_tables(base_path)
    return build_analysis_dataset(raw_tables)


def get_data_dictionary() -> pd.DataFrame:
    records = [
        ("year", "Observation year attached to the extraction record."),
        ("country_name", "Country inferred from the location hierarchy."),
        ("location_name", "Original PRISM location linked to the record."),
        ("data_point_name", "Indicator or metric extracted from the document."),
        ("data_group", "Higher-level thematic grouping of the data point."),
        ("numeric_value", "Numeric version of `value` when the text can be parsed."),
        ("overall_quality_score", "Composite score for source, completeness, geography, and time."),
        ("data_source_score", "PRISM score for source credibility."),
        ("data_completeness_score", "PRISM score for completeness."),
        ("geographic_level_score", "PRISM score for geographic specificity."),
        ("temporal_relevance_score", "PRISM score for time relevance."),
        ("validation_status", "Whether the extraction is validated in the export."),
        ("document_name", "Original source document name."),
        ("organization_country", "Publisher country field from the documents table."),
    ]
    return pd.DataFrame(records, columns=["Field", "Description"])
