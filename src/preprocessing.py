import numpy as np
import pandas as pd


def _parse_numeric_value(series: pd.Series) -> pd.Series:
    cleaned = (
        series.astype(str)
        .str.replace(",", "", regex=False)
        .str.replace("%", "", regex=False)
        .str.replace("$", "", regex=False)
        .str.strip()
        .replace({"": np.nan, "NA": np.nan, "nan": np.nan, "None": np.nan})
    )
    return pd.to_numeric(cleaned, errors="coerce")


def _resolve_location_hierarchy(locations: pd.DataFrame) -> pd.DataFrame:
    loc = locations.copy()
    loc["id"] = loc["id"].astype(str)
    loc["parent_id"] = loc["parent_id"].astype(str).replace({"nan": np.nan, "": np.nan})

    node_lookup = loc.set_index("id")[["location_name", "type", "parent_id"]].to_dict("index")
    resolved = []

    for row in loc.itertuples(index=False):
        current_id = row.id
        visited = set()
        country_name = row.location_name if row.type == "country" else np.nan
        province_name = row.location_name if row.type == "province" else np.nan

        while current_id and current_id in node_lookup and current_id not in visited:
            visited.add(current_id)
            node = node_lookup[current_id]
            if node["type"] == "country":
                country_name = node["location_name"]
            if node["type"] == "province" and pd.isna(province_name):
                province_name = node["location_name"]
            current_id = node["parent_id"]

        resolved.append(
            {
                "location_id": row.id,
                "location_name": row.location_name,
                "location_type": row.type,
                "country_name": country_name,
                "province_name": province_name,
            }
        )

    resolved_df = pd.DataFrame(resolved)
    resolved_df["country_name"] = resolved_df["country_name"].fillna("Unspecified")
    resolved_df["province_name"] = resolved_df["province_name"].fillna("Unspecified")
    return resolved_df


def _clean_documents(documents: pd.DataFrame) -> pd.DataFrame:
    doc = documents.copy()
    doc["created_at"] = pd.to_datetime(doc["created_at"], errors="coerce")
    doc["updated_at"] = pd.to_datetime(doc["updated_at"], errors="coerce")
    doc["reported_year"] = pd.to_numeric(doc["reported_year"], errors="coerce")
    return doc.rename(
        columns={
            "id": "document_id",
            "document_name": "document_name",
            "file_type": "file_type",
            "reported_year": "reported_year",
            "organization_type": "organization_type",
            "organization_country": "organization_country",
            "publishers": "publishers",
            "extraction_status": "document_extraction_status",
        }
    )[
        [
            "document_id",
            "document_name",
            "file_type",
            "reported_year",
            "organization_type",
            "organization_country",
            "publishers",
            "document_extraction_status",
            "created_at",
            "updated_at",
        ]
    ]


def _clean_data_points(data_points: pd.DataFrame) -> pd.DataFrame:
    points = data_points.copy()
    points["created_at"] = pd.to_datetime(points["created_at"], errors="coerce")
    return points.rename(
        columns={
            "id": "data_point_id",
            "name": "data_point_name",
            "description": "data_point_description",
        }
    )


def _clean_extractions(data_extractions: pd.DataFrame) -> pd.DataFrame:
    extractions = data_extractions.copy()

    numeric_columns = [
        "year",
        "source_page",
        "data_source_score",
        "data_completeness_score",
        "geographic_level_score",
        "temporal_relevance_year_difference",
        "temporal_relevance_score",
        "inconsistency_score",
        "overall_quality_score",
    ]
    for col in numeric_columns:
        extractions[col] = pd.to_numeric(extractions[col], errors="coerce")

    for col in ["created_at", "validated_at"]:
        extractions[col] = pd.to_datetime(extractions[col], errors="coerce")

    extractions["numeric_value"] = _parse_numeric_value(extractions["value"])
    extractions["is_numeric_value"] = extractions["numeric_value"].notna()
    extractions["is_duplicated"] = extractions["is_duplicated"].map(
        {"t": True, "f": False, True: True, False: False}
    )
    extractions["validation_status"] = extractions["validation_status"].fillna("Unknown")
    extractions["data_type"] = extractions["data_type"].fillna("Unknown")
    extractions["quality_band"] = pd.cut(
        extractions["overall_quality_score"],
        bins=[-np.inf, 49, 69, 84, np.inf],
        labels=["Low", "Moderate", "High", "Very high"],
    )
    extractions["year"] = extractions["year"].fillna(
        extractions["validated_at"].dt.year
    )
    extractions["year"] = extractions["year"].astype("Int64")

    return extractions.rename(columns={"id": "extraction_id", "file_id": "document_id"})


def build_analysis_dataset(raw_tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    extractions = _clean_extractions(raw_tables["data_extractions"])
    documents = _clean_documents(raw_tables["documents"])
    data_points = _clean_data_points(raw_tables["data_points"])
    locations = _resolve_location_hierarchy(raw_tables["locations"])

    df = (
        extractions.merge(documents, on="document_id", how="left")
        .merge(data_points, on="data_point_id", how="left")
        .merge(locations, on="location_id", how="left")
    )

    df["data_group"] = (
        df["data_group"].fillna("Unknown").str.replace("_", " ").str.title()
    )
    df["country_name"] = df["country_name"].fillna("Unspecified")
    df["location_name"] = df["location_name"].fillna("Unspecified")
    df["location_type"] = df["location_type"].fillna("Unknown").str.title()
    df["organization_country"] = df["organization_country"].fillna("Unknown")
    df["document_name"] = df["document_name"].fillna("Unknown document")
    df["file_type"] = df["file_type"].fillna("Unknown").str.upper()
    df["publishers"] = df["publishers"].fillna("Unknown")
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df = df[df["year"].notna()].copy()
    df["year"] = df["year"].astype(int)
    df = df.sort_values(["year", "country_name", "data_group"]).reset_index(drop=True)

    return df
