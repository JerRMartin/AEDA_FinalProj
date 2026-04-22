import pandas as pd

from src.utils import format_compact_number, format_decimal, format_percent


def compute_kpis(df: pd.DataFrame) -> list[dict[str, str]]:
    total_observations = len(df)
    distinct_documents = df["document_id"].nunique()
    median_quality = df["overall_quality_score"].median()
    validated_share = (df["validation_status"] == "VALIDATED").mean()
    numeric_mean = df["numeric_value"].mean()
    top_country = (
        df["country_name"].value_counts().idxmax() if not df["country_name"].empty else "N/A"
    )

    return [
        {
            "label": "Observations",
            "value": format_compact_number(total_observations),
            "delta": f"{format_compact_number(distinct_documents)} documents",
        },
        {
            "label": "Median Quality",
            "value": format_decimal(median_quality, suffix="/100"),
            "delta": "Composite PRISM score",
        },
        {
            "label": "Validated Share",
            "value": format_percent(validated_share),
            "delta": "Share of filtered records",
        },
        {
            "label": "Mean Numeric Value",
            "value": format_compact_number(numeric_mean),
            "delta": "Parsed from extraction value",
        },
        {
            "label": "Top Country",
            "value": top_country,
            "delta": "Largest filtered evidence volume",
        },
    ]


def build_insight_text(df: pd.DataFrame) -> str:
    top_group = df["data_group"].value_counts().idxmax()
    top_country = df["country_name"].value_counts().idxmax()
    yearly_counts = df.groupby("year").size()
    peak_year = int(yearly_counts.idxmax())
    peak_year_count = int(yearly_counts.max())
    validated_share = (df["validation_status"] == "VALIDATED").mean()
    median_quality = df["overall_quality_score"].median()

    return (
        f"In the current filtered view, {top_group} is the most represented thematic area and {top_country} contributes the highest volume of evidence. "
        f"Extraction activity peaks in {peak_year} with {peak_year_count:,} records, while the median overall quality score is {median_quality:.1f}/100. "
        f"The validated share is {validated_share:.1%}, which helps frame how much of the visible evidence has been formally reviewed."
    )
