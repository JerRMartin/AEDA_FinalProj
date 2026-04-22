import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.utils import (
    APP_TEMPLATE,
    PRIMARY_ACCENT,
    QUALITY_SCALE,
    STATUS_COLOR_MAP,
    build_color_map,
)


def _empty_figure(title: str, message: str) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        template=APP_TEMPLATE,
        title=title,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        annotations=[
            dict(
                text=message,
                x=0.5,
                y=0.5,
                xref="paper",
                yref="paper",
                showarrow=False,
                font=dict(size=15),
            )
        ],
        height=420,
    )
    return fig


def create_bar_chart(df: pd.DataFrame, top_n: int = 10) -> go.Figure:
    chart_df = (
        df.groupby("data_point_name", as_index=False)
        .agg(observations=("extraction_id", "count"))
        .sort_values("observations", ascending=False)
        .head(top_n)
    )
    chart_df = chart_df.sort_values("observations", ascending=True)

    fig = px.bar(
        chart_df,
        x="observations",
        y="data_point_name",
        orientation="h",
        text="observations",
        color="observations",
        color_continuous_scale=QUALITY_SCALE,
        template=APP_TEMPLATE,
        labels={
            "observations": "Number of extraction records",
            "data_point_name": "Data point",
        },
        title="Most Frequent Indicators in the Filtered View",
    )
    fig.update_traces(
        hovertemplate="<b>%{y}</b><br>Observations: %{x:,}<extra></extra>",
        texttemplate="%{text:,}",
        textposition="outside",
        marker_line_width=0,
    )
    fig.update_layout(coloraxis_showscale=False, height=430)
    return fig


def create_donut_chart(df: pd.DataFrame) -> go.Figure:
    chart_df = (
        df["validation_status"]
        .value_counts(dropna=False)
        .rename_axis("validation_status")
        .reset_index(name="records")
    )
    fig = px.pie(
        chart_df,
        names="validation_status",
        values="records",
        hole=0.58,
        color="validation_status",
        color_discrete_map=STATUS_COLOR_MAP,
        template=APP_TEMPLATE,
        title="Validation Composition of Visible Records",
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hovertemplate="<b>%{label}</b><br>Records: %{value:,}<br>Share: %{percent}<extra></extra>",
    )
    fig.update_layout(
        height=430,
        legend_title_text="Validation status",
    )
    return fig


def create_distribution_chart(df: pd.DataFrame) -> go.Figure:
    fig = px.histogram(
        df,
        x="overall_quality_score",
        color="validation_status",
        nbins=18,
        barmode="overlay",
        opacity=0.72,
        color_discrete_map=STATUS_COLOR_MAP,
        template=APP_TEMPLATE,
        title="Distribution of Overall Quality Scores",
        labels={
            "overall_quality_score": "Overall quality score",
            "count": "Number of records",
        },
    )
    fig.update_traces(
        hovertemplate="Quality score bin: %{x}<br>Records: %{y:,}<br>Status: %{fullData.name}<extra></extra>"
    )
    fig.update_layout(height=420, legend_title_text="Validation status")
    return fig


def create_box_plot(df: pd.DataFrame) -> go.Figure:
    order = (
        df.groupby("data_group")["overall_quality_score"]
        .median()
        .sort_values(ascending=False)
        .index
        .tolist()
    )
    fig = px.box(
        df,
        x="data_group",
        y="overall_quality_score",
        color="data_group",
        category_orders={"data_group": order},
        color_discrete_map=build_color_map(order),
        template=APP_TEMPLATE,
        title="Quality Score Spread Across PRISM Data Groups",
        labels={
            "data_group": "Data group",
            "overall_quality_score": "Overall quality score",
        },
        points="outliers",
    )
    fig.update_traces(
        hovertemplate="<b>%{x}</b><br>Quality score: %{y:.1f}<extra></extra>"
    )
    fig.update_layout(height=430, showlegend=False)
    return fig


def create_scatter_chart(df: pd.DataFrame) -> go.Figure:
    scatter_df = df.dropna(
        subset=["data_source_score", "overall_quality_score", "data_group"]
    ).copy()
    if scatter_df.empty:
        return _empty_figure(
            "Source Credibility and Overall Quality Move Together",
            "No rows remain with the scores needed for the association view.",
        )
    scatter_df["data_completeness_score"] = scatter_df["data_completeness_score"].fillna(0)
    groups = sorted(scatter_df["data_group"].unique().tolist())

    fig = px.scatter(
        scatter_df,
        x="data_source_score",
        y="overall_quality_score",
        color="data_group",
        size="data_completeness_score",
        hover_name="data_point_name",
        color_discrete_map=build_color_map(groups),
        template=APP_TEMPLATE,
        title="Source Credibility and Overall Quality Move Together",
        labels={
            "data_source_score": "Data source score",
            "overall_quality_score": "Overall quality score",
            "data_completeness_score": "Completeness score",
            "data_group": "Data group",
        },
    )
    fig.update_traces(
        marker=dict(line=dict(width=0.4, color="white"), opacity=0.8),
        hovertemplate=(
            "<b>%{hovertext}</b><br>"
            "Data group: %{customdata[0]}<br>"
            "Country: %{customdata[1]}<br>"
            "Completeness score: %{customdata[2]:.1f}<br>"
            "Source score: %{x:.1f}<br>"
            "Quality score: %{y:.1f}<extra></extra>"
        ),
        customdata=np.stack(
            [
                scatter_df["data_group"],
                scatter_df["country_name"],
                scatter_df["data_completeness_score"],
            ],
            axis=-1,
        ),
    )
    fig.update_layout(height=450, legend_title_text="Data group")
    return fig


def create_correlation_heatmap(df: pd.DataFrame) -> go.Figure:
    corr_cols = [
        "data_source_score",
        "data_completeness_score",
        "geographic_level_score",
        "temporal_relevance_score",
        "inconsistency_score",
        "overall_quality_score",
    ]
    corr_df = df[corr_cols].dropna()
    if corr_df.empty:
        return _empty_figure(
            "Correlation Structure of PRISM Quality Dimensions",
            "No rows remain with complete score fields for the correlation matrix.",
        )
    corr = corr_df.corr(numeric_only=True).round(2)

    fig = go.Figure(
        data=go.Heatmap(
            z=corr.values,
            x=[
                "Source",
                "Completeness",
                "Geography",
                "Temporal",
                "Inconsistency",
                "Overall",
            ],
            y=[
                "Source",
                "Completeness",
                "Geography",
                "Temporal",
                "Inconsistency",
                "Overall",
            ],
            colorscale=QUALITY_SCALE,
            zmin=-1,
            zmax=1,
            text=corr.values,
            texttemplate="%{text}",
            hovertemplate="Correlation: %{z:.2f}<extra></extra>",
            colorbar=dict(title="r"),
        )
    )
    fig.update_layout(
        template=APP_TEMPLATE,
        title="Correlation Structure of PRISM Quality Dimensions",
        xaxis_title="Quality dimension",
        yaxis_title="Quality dimension",
        height=450,
    )
    return fig


def create_trend_chart(df: pd.DataFrame) -> go.Figure:
    chart_df = (
        df.groupby("year", as_index=False)
        .agg(
            observations=("extraction_id", "count"),
            avg_quality=("overall_quality_score", "mean"),
        )
        .sort_values("year")
    )

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=chart_df["year"],
            y=chart_df["observations"],
            name="Observations",
            mode="lines+markers",
            line=dict(color=PRIMARY_ACCENT, width=3),
            marker=dict(size=7),
            hovertemplate="Year: %{x}<br>Observations: %{y:,}<extra></extra>",
            yaxis="y1",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=chart_df["year"],
            y=chart_df["avg_quality"],
            name="Average quality",
            mode="lines+markers",
            line=dict(color="#2A9D8F", width=2.5, dash="dash"),
            marker=dict(size=6),
            hovertemplate="Year: %{x}<br>Average quality: %{y:.1f}<extra></extra>",
            yaxis="y2",
        )
    )
    fig.update_layout(
        template=APP_TEMPLATE,
        title="Annual Evidence Volume and Mean Quality",
        xaxis=dict(title="Observation year"),
        yaxis=dict(title="Number of extraction records"),
        yaxis2=dict(
            title="Average overall quality score",
            overlaying="y",
            side="right",
            range=[0, 100],
        ),
        legend=dict(title="Series", orientation="h", y=1.1, x=0),
        height=460,
    )
    return fig
