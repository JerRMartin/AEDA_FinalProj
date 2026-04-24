import pandas as pd

from src.utils import format_compact_number, format_percent


def _numeric_for(df: pd.DataFrame, point_name: str) -> pd.Series:
    return df.loc[
        (df["data_point_name"] == point_name) & df["numeric_value"].notna(),
        "numeric_value",
    ]


def compute_kpis(df: pd.DataFrame) -> list[dict[str, str]]:
    country_df = df[df["location_type"] == "Country"]

    # KPI 1 — Total Plastic Waste Generated (metric tons, country-level)
    pw_gen = _numeric_for(country_df, "Plastic Waste Generated")
    total_generated = pw_gen.sum() if not pw_gen.empty else float("nan")
    gen_countries = (
        country_df.loc[country_df["data_point_name"] == "Plastic Waste Generated", "country_name"]
        .nunique()
    )

    # KPI 2 — Total Plastic Waste Collected (metric tons, country-level)
    pw_col = _numeric_for(country_df, "Plastic Waste Collected")
    total_collected = pw_col.sum() if not pw_col.empty else float("nan")

    # KPI 3 — Leakage Rate = (Generated − Collected) / Generated
    if total_generated and total_generated > 0:
        leakage_rate = (total_generated - total_collected) / total_generated
    else:
        leakage_rate = float("nan")

    # KPI 4 — Recycling Rate: mean of "Plastic Waste % Collected For Recycling"
    recycling_pct = _numeric_for(df, "Plastic Waste % Collected For Recycling")
    mean_recycling = recycling_pct.mean() / 100 if not recycling_pct.empty else float("nan")

    # KPI 5 — SUP Share = SUP Consumed / Total Plastic Consumption
    sup_total = _numeric_for(df, "SUP Consumed").sum()
    plastic_total = _numeric_for(df, "Total Plastic Consumption").sum()
    sup_share = sup_total / plastic_total if plastic_total > 0 else float("nan")

    return [
        {
            "label": "PW Generated",
            "value": format_compact_number(total_generated),
            "delta": f"metric tons · {gen_countries} countries",
        },
        {
            "label": "PW Collected",
            "value": format_compact_number(total_collected),
            "delta": "metric tons · country-level",
        },
        {
            "label": "Leakage Rate",
            "value": format_percent(leakage_rate),
            "delta": "(Generated − Collected) / Generated",
        },
        {
            "label": "Recycling Rate",
            "value": format_percent(mean_recycling),
            "delta": "Mean % collected for recycling",
        },
        {
            "label": "SUP Share",
            "value": format_percent(sup_share),
            "delta": "SUP / Total Plastic Consumption",
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
