import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import STOPWORDS, WordCloud

from src.utils import (
    APP_TEMPLATE,
    HIGHLIGHT,
    PRIMARY_ACCENT,
    QUALITY_SCALE,
    SECONDARY_ACCENT,
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


# ── Chat Messages ──────────────────────────────────────────────────────────────

def create_messages_timeline(df: pd.DataFrame) -> go.Figure:
    timeline = (
        df.assign(date=pd.to_datetime(df["created_at"], utc=True).dt.date)
        .groupby("date", as_index=False)
        .size()
        .rename(columns={"size": "messages"})
    )
    fig = px.bar(
        timeline,
        x="date",
        y="messages",
        template=APP_TEMPLATE,
        title="Messages per Day",
        labels={"date": "Date", "messages": "Messages"},
        color_discrete_sequence=[PRIMARY_ACCENT],
    )
    fig.update_traces(hovertemplate="Date: %{x}<br>Messages: %{y:,}<extra></extra>")
    fig.update_layout(height=380)
    return fig


def create_message_sender_donut(df: pd.DataFrame) -> go.Figure:
    counts = (
        df["created_by"]
        .map(lambda x: "AI" if x == "AI" else "Human")
        .value_counts()
        .rename_axis("sender")
        .reset_index(name="count")
    )
    fig = px.pie(
        counts,
        names="sender",
        values="count",
        hole=0.58,
        color="sender",
        color_discrete_map={"AI": PRIMARY_ACCENT, "Human": SECONDARY_ACCENT},
        template=APP_TEMPLATE,
        title="AI vs. Human Messages",
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hovertemplate="<b>%{label}</b><br>Messages: %{value:,}<br>Share: %{percent}<extra></extra>",
    )
    fig.update_layout(height=380)
    return fig


def create_message_wordcloud(df: pd.DataFrame) -> go.Figure:
    text = " ".join(df["message"].dropna().astype(str))
    wc = WordCloud(
        width=800,
        height=380,
        background_color="white",
        stopwords=STOPWORDS,
        colormap="Blues",
        max_words=100,
        collocations=False,
    ).generate(text)

    fig = px.imshow(wc.to_array(), template=APP_TEMPLATE, title="Most Used Words in Messages")
    fig.update_layout(
        height=380,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        margin=dict(l=0, r=0, t=40, b=0),
    )
    fig.update_traces(hoverinfo="skip", hovertemplate=None)
    return fig


# ── Data Extractions ───────────────────────────────────────────────────────────

def create_extractions_by_year(df: pd.DataFrame) -> go.Figure:
    chart_df = (
        df.groupby("year", as_index=False)
        .size()
        .rename(columns={"size": "extractions"})
        .sort_values("year")
    )
    fig = px.bar(
        chart_df,
        x="year",
        y="extractions",
        template=APP_TEMPLATE,
        title="Extractions by Reported Year",
        labels={"year": "Year", "extractions": "Extractions"},
        color="extractions",
        color_continuous_scale=QUALITY_SCALE,
    )
    fig.update_traces(hovertemplate="Year: %{x}<br>Extractions: %{y:,}<extra></extra>")
    fig.update_layout(height=380, coloraxis_showscale=False)
    return fig


def create_extraction_validation_donut(df: pd.DataFrame) -> go.Figure:
    counts = (
        df["validation_status"]
        .value_counts(dropna=False)
        .rename_axis("status")
        .reset_index(name="count")
    )
    fig = px.pie(
        counts,
        names="status",
        values="count",
        hole=0.58,
        color="status",
        color_discrete_map=STATUS_COLOR_MAP,
        template=APP_TEMPLATE,
        title="Validation Status Breakdown",
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hovertemplate="<b>%{label}</b><br>Count: %{value:,}<extra></extra>",
    )
    fig.update_layout(height=380, legend_title_text="Status")
    return fig


def create_extraction_quality_histogram(df: pd.DataFrame) -> go.Figure:
    fig = px.histogram(
        df.dropna(subset=["overall_quality_score"]),
        x="overall_quality_score",
        nbins=20,
        template=APP_TEMPLATE,
        title="Overall Quality Score Distribution",
        labels={"overall_quality_score": "Overall quality score", "count": "Extractions"},
        color_discrete_sequence=[PRIMARY_ACCENT],
    )
    fig.update_traces(hovertemplate="Score bin: %{x}<br>Count: %{y:,}<extra></extra>")
    fig.update_layout(height=380)
    return fig


# ── Data Points ────────────────────────────────────────────────────────────────

def create_data_points_by_group(df: pd.DataFrame) -> go.Figure:
    chart_df = (
        df.groupby("data_group", as_index=False)
        .size()
        .rename(columns={"size": "count"})
        .sort_values("count", ascending=True)
    )
    fig = px.bar(
        chart_df,
        x="count",
        y="data_group",
        orientation="h",
        text="count",
        template=APP_TEMPLATE,
        title="Data Points by Group",
        labels={"count": "Data points", "data_group": "Data group"},
        color="count",
        color_continuous_scale=QUALITY_SCALE,
    )
    fig.update_traces(
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Count: %{x:,}<extra></extra>",
    )
    fig.update_layout(height=420, coloraxis_showscale=False)
    return fig


# ── Documents ──────────────────────────────────────────────────────────────────

def create_documents_by_filetype(df: pd.DataFrame) -> go.Figure:
    chart_df = (
        df["file_type"]
        .value_counts()
        .rename_axis("file_type")
        .reset_index(name="count")
    )
    fig = px.bar(
        chart_df,
        x="file_type",
        y="count",
        text="count",
        template=APP_TEMPLATE,
        title="Documents by File Type",
        labels={"file_type": "File type", "count": "Documents"},
        color="count",
        color_continuous_scale=QUALITY_SCALE,
    )
    fig.update_traces(
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Documents: %{y:,}<extra></extra>",
    )
    fig.update_layout(height=380, coloraxis_showscale=False)
    return fig


def create_documents_by_year(df: pd.DataFrame) -> go.Figure:
    chart_df = (
        df.dropna(subset=["reported_year"])
        .groupby("reported_year", as_index=False)
        .size()
        .rename(columns={"size": "count"})
        .sort_values("reported_year")
    )
    fig = px.bar(
        chart_df,
        x="reported_year",
        y="count",
        template=APP_TEMPLATE,
        title="Documents by Reported Year",
        labels={"reported_year": "Reported year", "count": "Documents"},
        color="count",
        color_continuous_scale=QUALITY_SCALE,
    )
    fig.update_traces(hovertemplate="Year: %{x}<br>Documents: %{y:,}<extra></extra>")
    fig.update_layout(height=380, coloraxis_showscale=False)
    return fig


def create_documents_by_country(df: pd.DataFrame, top_n: int = 15) -> go.Figure:
    chart_df = (
        df["organization_country"]
        .value_counts()
        .head(top_n)
        .rename_axis("country")
        .reset_index(name="count")
        .sort_values("count", ascending=True)
    )
    fig = px.bar(
        chart_df,
        x="count",
        y="country",
        orientation="h",
        text="count",
        template=APP_TEMPLATE,
        title=f"Top {top_n} Publisher Countries",
        labels={"count": "Documents", "country": "Country"},
        color="count",
        color_continuous_scale=QUALITY_SCALE,
    )
    fig.update_traces(
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Documents: %{x:,}<extra></extra>",
    )
    fig.update_layout(height=500, coloraxis_showscale=False)
    return fig


# ── Infrastructures ────────────────────────────────────────────────────────────

def create_infra_by_type(df: pd.DataFrame) -> go.Figure:
    chart_df = (
        df["infra_type"]
        .value_counts()
        .rename_axis("type")
        .reset_index(name="count")
        .sort_values("count", ascending=True)
    )
    fig = px.bar(
        chart_df,
        x="count",
        y="type",
        orientation="h",
        text="count",
        template=APP_TEMPLATE,
        title="Infrastructure by Type",
        labels={"count": "Sites", "type": "Infrastructure type"},
        color="count",
        color_continuous_scale=QUALITY_SCALE,
    )
    fig.update_traces(
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Sites: %{x:,}<extra></extra>",
    )
    fig.update_layout(height=400, coloraxis_showscale=False)
    return fig


def create_infra_by_status(df: pd.DataFrame) -> go.Figure:
    counts = (
        df["active_status"]
        .value_counts()
        .rename_axis("status")
        .reset_index(name="count")
    )
    fig = px.pie(
        counts,
        names="status",
        values="count",
        hole=0.58,
        color="status",
        color_discrete_map=build_color_map(counts["status"].tolist()),
        template=APP_TEMPLATE,
        title="Infrastructure Active Status",
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hovertemplate="<b>%{label}</b><br>Sites: %{value:,}<extra></extra>",
    )
    fig.update_layout(height=400)
    return fig


def create_infra_choropleth(df: pd.DataFrame) -> go.Figure:
    country_counts = (
        df["country_city"]
        .dropna()
        .str.split(",")
        .str[0]
        .str.strip()
        .value_counts()
        .rename_axis("country")
        .reset_index(name="sites")
    )
    fig = px.choropleth(
        country_counts,
        locations="country",
        locationmode="country names",
        color="sites",
        color_continuous_scale=QUALITY_SCALE,
        template=APP_TEMPLATE,
        title="Infrastructure Sites by Country",
        labels={"sites": "Sites", "country": "Country"},
    )
    fig.update_traces(
        hovertemplate="<b>%{location}</b><br>Sites: %{z:,}<extra></extra>",
    )
    fig.update_layout(
        height=500,
        coloraxis_colorbar=dict(title="Sites"),
        geo=dict(showframe=False, showcoastlines=True, projection_type="natural earth"),
        margin=dict(l=0, r=0, t=40, b=0),
    )
    return fig


# ── Locations ──────────────────────────────────────────────────────────────────

def create_locations_by_type(df: pd.DataFrame) -> go.Figure:
    counts = (
        df["type"]
        .value_counts()
        .rename_axis("type")
        .reset_index(name="count")
    )
    fig = px.pie(
        counts,
        names="type",
        values="count",
        hole=0.58,
        template=APP_TEMPLATE,
        title="Locations by Type",
        color_discrete_sequence=[PRIMARY_ACCENT, SECONDARY_ACCENT, HIGHLIGHT],
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hovertemplate="<b>%{label}</b><br>Count: %{value:,}<extra></extra>",
    )
    fig.update_layout(height=400)
    return fig


def create_locations_by_country_type(df: pd.DataFrame) -> go.Figure:
    chart_df = (
        df[df["aepw_country_type"].notna() & (df["aepw_country_type"] != "")]
        ["aepw_country_type"]
        .value_counts()
        .rename_axis("country_type")
        .reset_index(name="count")
        .sort_values("count", ascending=True)
    )
    if chart_df.empty:
        return _empty_figure(
            "Locations by AEPW Country Type",
            "No AEPW country type data available.",
        )
    fig = px.bar(
        chart_df,
        x="count",
        y="country_type",
        orientation="h",
        text="count",
        template=APP_TEMPLATE,
        title="Locations by AEPW Country Type*",
        subtitle="* AEPW country type is a classification of countries by the Aid Effectiveness Platform for the World (AEPW) while we are unaware of the specific criteria used for classification.",
        labels={"count": "Locations", "country_type": "AEPW country type"},
        color="count",
        color_continuous_scale=QUALITY_SCALE,
    )
    fig.update_traces(
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Locations: %{x:,}<extra></extra>",
    )
    fig.update_layout(height=380, coloraxis_showscale=False)
    return fig


# ── Projects ───────────────────────────────────────────────────────────────────

def create_projects_by_status(df: pd.DataFrame) -> go.Figure:
    chart_df = (
        df["project_status"]
        .value_counts()
        .rename_axis("status")
        .reset_index(name="count")
        .sort_values("count", ascending=True)
    )
    fig = px.bar(
        chart_df,
        x="count",
        y="status",
        orientation="h",
        text="count",
        template=APP_TEMPLATE,
        title="Projects by Status",
        labels={"count": "Projects", "status": "Status"},
        color="status",
        color_discrete_map=build_color_map(chart_df["status"].tolist()),
    )
    fig.update_traces(
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Projects: %{x:,}<extra></extra>",
    )
    fig.update_layout(height=360, showlegend=False)
    return fig


def create_projects_by_countries(df: pd.DataFrame) -> go.Figure:
    count = 10
    chart_df = (
        df["countries"]
        .dropna()
        .value_counts()
        .head(count)
        .rename_axis("country")
        .reset_index(name="count")
        .sort_values("count", ascending=True)
    )
    fig = px.bar(
        chart_df,
        x="count",
        y="country",
        orientation="h",
        text="count",
        template=APP_TEMPLATE,
        title="Top " + str(count) + " Countries by Project Count",
        labels={"count": "Projects", "country": "Country"},
        color="count",
        color_continuous_scale=QUALITY_SCALE,
    )
    fig.update_traces(
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Projects: %{x:,}<extra></extra>",
    )
    fig.update_layout(height=max(360, len(chart_df) * 28), coloraxis_showscale=False)
    return fig
