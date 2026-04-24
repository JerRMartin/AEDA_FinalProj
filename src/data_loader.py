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

# Each entry: (tab_label, csv_file_name, columns_to_exclude)
RAW_TABLE_TABS = [
    ("Chat Messages",    "chat_messages",    []),
    ("Data Extractions", "data_extractions", []),
    ("Data Points",      "data_points",      []),
    ("Documents",        "documents",        []),
    ("Graphs",           "graphs",           []),
    ("Infrastructures",  "infrastructures",  []),
    ("Locations",        "locations",        []),
    ("Organizations",    "organization",     []),
    ("Projects",         "projects",         []),
]


@st.cache_data(show_spinner=False)
def load_raw_table(base_path: Path, name: str) -> pd.DataFrame:
    return pd.read_csv(base_path / "csv" / name)


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
        ("VALIDATED", "The extraction has been reviewed and approved by a human analyst in PRISM, as indicated by a non-null validated_by user ID."),
        ("UNVALIDATED", "The extraction was created and logged a processing timestamp (validated_at), but no human reviewer has approved it (validated_by is null)."),
    ]
    return pd.DataFrame(records, columns=["Field", "Description"])

_KEY_TERMS_BY_TAB: dict[str, list[tuple[str, str]]] = {
    "Chat Messages": [
        ("MSW", "Municipal Solid Waste"),
        ("PRISM", "Plastics Recovery Insights Steering Model"),
        ("PW", "Plastic Waste"),
    ],
    "Data Extractions": [
        ("BAU", "Business As Usual"),
        ("MSW", "Municipal Solid Waste"),
        ("PW", "Plastic Waste"),
    ],
    "Data Points": [
        ("HDPE", "High-Density Polyethylene"),
        ("LDPE", "Low-Density Polyethylene"),
        ("MLP", "Multi-Layered Plastic"),
        ("MSW", "Municipal Solid Waste"),
        ("PET", "Polyethylene Terephthalate"),
        ("PP", "Polypropylene"),
        ("PS", "Polystyrene"),
        ("PVC", "Polyvinyl Chloride"),
        ("PW", "Plastic Waste"),
        ("SUP", "Single-Use Plastic"),
    ],
    "Documents": [
        ("AEPW", "Alliance to End Plastic Waste"),
        ("CPCB", "Central Pollution Control Board"),
        ("CSIRO", "Commonwealth Scientific and Industrial Research Organisation"),
        ("EDA", "Exploratory Data Analysis"),
        ("EPA", "Environmental Protection Agency"),
        ("GIZ", "Deutsche Gesellschaft für Internationale Zusammenarbeit"),
        ("IUCN", "International Union for Conservation of Nature"),
        ("NGO", "Non-Governmental Organization"),
        ("OECD", "Organisation for Economic Co-operation and Development"),
        ("UNCRD", "United Nations Centre for Regional Development"),
        ("UNEP", "United Nations Environment Programme"),
    ],
    "Graphs": [
        ("MSW", "Municipal Solid Waste"),
        ("PW", "Plastic Waste"),
    ],
    "Infrastructures": [
        ("ABS", "Acrylonitrile Butadiene Styrene"),
        ("HDPE", "High-Density Polyethylene"),
        ("LDPE", "Low-Density Polyethylene"),
        ("PC", "Polycarbonate"),
        ("PET", "Polyethylene Terephthalate"),
        ("PP", "Polypropylene"),
        ("PS", "Polystyrene"),
        ("PVC", "Polyvinyl Chloride"),
    ],
    "Locations": [
        ("AEPW", "Alliance to End Plastic Waste"),
    ],
    "Organizations": [
        ("AEPW", "Alliance to End Plastic Waste"),
    ],
    "Projects": [
        ("AEPW", "Alliance to End Plastic Waste"),
        ("GDP", "Gross Domestic Product"),
        ("ISWM", "Integrated Solid Waste Management"),
        ("IWC", "Informal Waste Collector"),
        ("MSW", "Municipal Solid Waste"),
        ("MVP", "Minimum Viable Product"),
        ("PCR", "Post-Consumer Recycled"),
        ("PCX", "Plastic Credit Exchange"),
        ("PRISM", "Plastics Recovery Insights Steering Model"),
        ("PW", "Plastic Waste"),
        ("TCI", "The Circulate Initiative"),
        ("WaCT", "Waste Wise City Tool"),
    ],
}


def get_key_terms(tab: str | None = None) -> pd.DataFrame:
    if tab is not None:
        rows = _KEY_TERMS_BY_TAB.get(tab, [])
    else:
        seen: set[str] = set()
        rows = []
        for terms in _KEY_TERMS_BY_TAB.values():
            for term, definition in terms:
                if term not in seen:
                    seen.add(term)
                    rows.append((term, definition))
        rows.sort(key=lambda x: x[0])
    return pd.DataFrame(rows, columns=["Term", "Definition"])