# Dashboard Analytics Guide

This document explains the analytical logic behind the PRISM Evidence Analytics Dashboard. It is intended as a companion to `README.md`, with more emphasis on why the dashboard was designed this way, how the data was prepared, and how each interactive component contributes to the overall analytical story.

## 1. Analytical Objective

The dashboard was built to explore the PRISM database as a structured evidence system rather than as a collection of isolated tables. The main objective is to help a viewer understand:

1. how large the evidence base is,
2. how evidence is distributed across topics and countries,
3. how record quality varies,
4. whether key quality-related variables are associated, and
5. how the evidence base changes over time.

The design follows an academic exploratory analysis workflow:

`summary -> composition -> distributions -> relationships -> trends -> insights`

This structure makes the dashboard easier to defend in a written report because each section answers a distinct analytical question.

## 2. Why This Data Model Was Chosen

From the PRISM export, the dashboard treats `data_extractions` as the central fact table because each row represents one extracted observation linked to:

- a source document,
- a specific data point or indicator,
- a geographic location,
- a year,
- and a set of quality and validation attributes.

The following table relationships are used in the dashboard:

- `data_extractions.file_id -> documents.id`
- `data_extractions.data_point_id -> data_points.id`
- `data_extractions.location_id -> locations.id`
- `locations.parent_id -> locations.id`

These joins allow the dashboard to combine observation-level evidence with metadata about source documents, indicator definitions, and geographic hierarchy.

## 3. Data Preparation Pipeline

The app uses the raw files in `csv/` directly and creates an analysis-ready dataset at runtime. This improves reproducibility because the dashboard does not depend on a manually edited external CSV.

### Cleaning and preprocessing steps

The preprocessing pipeline performs the following tasks:

- loads the raw PRISM tables from relative paths,
- converts numeric score fields to numeric types,
- parses dates where relevant,
- attempts to parse `value` into a numeric field called `numeric_value`,
- flags whether a record contains a usable numeric value,
- resolves location hierarchy so each record can be associated with a country,
- standardizes categorical labels such as `data_group`,
- handles missing values gracefully,
- creates a derived `quality_band` field from `overall_quality_score`,
- removes rows with no usable year for time-based analysis.

### Why `overall_quality_score` is central

The raw extracted `value` field is not always directly comparable because values may be:

- numeric or textual,
- in different units,
- from different data domains,
- or conceptually unrelated across indicators.

Because of that, the dashboard relies heavily on `overall_quality_score` and related PRISM quality dimensions as consistent analytical variables. These fields are much more appropriate for cross-record comparisons.

## 4. Dashboard Layout Rationale

The layout was intentionally designed to support explanation and interpretation.

### Header

The header introduces the dashboard purpose, identifies the dataset, and frames the app as a formal analytical product rather than a technical prototype.

### Sidebar filters

The sidebar makes the analytical scope explicit and keeps the main canvas focused on results. Filters were placed here because this is standard for Streamlit dashboards and supports clean visual hierarchy.

### KPI row

The KPI row appears first because it gives an immediate summary of scale, quality, and validation before the viewer interprets more detailed charts.

### Charts in sequence

The chart order follows a logic that is easy to justify academically:

1. composition and evidence volume,
2. quality distribution,
3. differences between groups,
4. associations between variables,
5. trends over time,
6. synthesized takeaways.

This is more defensible than showing unrelated charts without a narrative order.

## 5. Interactive Controls

The dashboard includes more than the minimum required interactivity. All filters update KPI cards, charts, and the insight text.

### Included filters

- year range slider,
- data group multiselect,
- country multiselect,
- validation status multiselect,
- numeric-only checkbox,
- Top-N slider for ranking charts,
- reset filters button.

### Why these filters are meaningful

- The year filter supports temporal scope control.
- The data group filter allows comparison across thematic domains.
- The country filter supports geographic exploration.
- The validation status filter helps compare reviewed versus unreviewed evidence.
- The numeric-only toggle isolates rows where raw values are quantitatively interpretable.
- The Top-N control improves readability for ranked charts.

These are analytically meaningful controls rather than cosmetic ones.

## 6. KPI Card Design

The dashboard includes five KPI cards:

1. `Observations`
2. `Median Quality`
3. `Validated Share`
4. `Mean Numeric Value`
5. `Top Country`

### Why these KPIs were chosen

- `Observations` provides scale.
- `Median Quality` is robust to outliers and summarizes record quality.
- `Validated Share` shows the degree of reviewed evidence in the filtered view.
- `Mean Numeric Value` gives a summary of parsed numeric evidence where available.
- `Top Country` identifies the dominant geographic contributor in the current slice.

Together, these metrics balance size, quality, verification, numerical content, and geographic emphasis.

## 7. Visualization Choices and Justification

The dashboard includes multiple chart types chosen to satisfy the course taxonomy while also supporting real analysis.

### 7.1 Amounts: Horizontal bar chart

**Chart:** Most frequent indicators in the filtered view

**Purpose:** shows which data points dominate the visible evidence.

**Why this works:** a ranked horizontal bar chart is readable for long indicator names and makes category comparison straightforward.

### 7.2 Proportions: Donut chart

**Chart:** Validation composition of visible records

**Purpose:** communicates the relative share of validated versus unvalidated records.

**Why this works:** a donut chart is appropriate here because the number of categories is very small and the main message is proportional composition.

### 7.3 Distribution: Histogram

**Chart:** Distribution of overall quality scores

**Purpose:** shows concentration, spread, and possible clustering in quality scores.

**Why this works:** a histogram is the standard choice for continuous score distributions.

### 7.4 Distribution by group: Box plot

**Chart:** Quality score spread across PRISM data groups

**Purpose:** compares median, spread, and outliers across thematic groups.

**Why this works:** a box plot is stronger than a bar chart for showing variation, not just central tendency.

### 7.5 Association: Scatter plot

**Chart:** Source credibility and overall quality move together

**Purpose:** explores whether higher source credibility tends to align with higher overall quality.

**Why this works:** a scatter plot is appropriate for comparing two quantitative variables and also allows encoding group and completeness through color and size.

### 7.6 Association: Correlation heatmap

**Chart:** Correlation structure of PRISM quality dimensions

**Purpose:** summarizes relationships among score-based quality fields.

**Why this works:** a heatmap gives a compact overview of pairwise correlations and supports discussion of which dimensions move together.

### 7.7 Evolution: Dual-axis line chart

**Chart:** Annual evidence volume and mean quality

**Purpose:** shows how extraction activity changes over time while also tracking average quality.

**Why this works:** combining volume and mean quality supports a richer temporal interpretation than a single trend line alone.

## 8. Tooltips, Labels, and Legibility

The dashboard uses custom Plotly tooltips to make interactive inspection more informative. Tooltips were designed to show meaningful context such as:

- indicator name,
- country,
- data group,
- score values,
- record counts,
- relative share.

All charts also include:

- explanatory titles,
- labeled axes,
- legends when grouping is used,
- short captions underneath the charts.

This was done to ensure the dashboard is easy to interpret without requiring code knowledge.

## 9. Color and Visual Design System

The app uses a centralized and consistent color system defined in `src/utils.py`.

### Design principles used

- one primary dark blue accent for authority and consistency,
- limited secondary accent colors,
- muted neutrals for supporting elements,
- consistent category-to-color mapping,
- accessible contrast on a light academic background,
- restrained use of highlight colors.

### Why this matters

Consistent coloring improves readability and makes the dashboard look intentional and professional. It also makes the report easier to discuss because the same color meanings recur across views.

## 10. Storytelling Features

The dashboard was not built as a chart gallery. It includes explicit storytelling elements:

- introductory purpose statement,
- analytical overview section,
- chart captions explaining why each chart exists,
- dynamic summary banner showing filter scope,
- dynamic key insight sentence based on the current filtered state,
- “How to Read This Dashboard” guidance near the bottom.

These features make the app easier to present live and easier to justify in a report.

## 11. Reproducibility and Code Quality

The project was designed to be reproducible and academically clean.

### Reproducibility features

- relative paths only,
- raw data stored in the repository,
- `requirements.txt` included,
- single-command launch via `streamlit run app.py`,
- modular code structure,
- cached data loading and preprocessing.

### Code organization

The code is split into focused modules:

- `app.py` for layout and orchestration,
- `src/data_loader.py` for loading and cached access,
- `src/preprocessing.py` for cleaning and joins,
- `src/metrics.py` for KPI and insight logic,
- `src/charts.py` for reusable visual functions,
- `src/utils.py` for constants, formatting, and shared helpers.

This structure makes the project easier to explain, maintain, and extend.

## 12. Limitations and Interpretation Notes

The dashboard is strong for exploratory analysis, but several limitations should be acknowledged in an academic setting:

- the raw `value` field is heterogeneous and not always directly comparable,
- some metadata fields in the source export are incomplete,
- quality scores are framework-dependent and reflect PRISM scoring logic,
- some creator/updater identifiers in the broader export do not cleanly map to current user IDs,
- the dashboard is exploratory, not causal.

These are not defects in the dashboard design; they are realistic data limitations that should be stated clearly in the final report.

## 13. Suggested Report Language

You can adapt the following explanation in your write-up:

> The dashboard was designed around the `data_extractions` table as the central analytical unit, enriched with document, indicator, and location metadata through relational joins. Visualizations were selected to cover the main taxonomy categories required by the course while also supporting an interpretable analytical narrative. The final interface emphasizes reproducibility, clear labeling, accessible color design, interactive filtering, and concise insight generation.

## 14. Final Summary

The dashboard is intended to be more than a technical requirement submission. It is a structured exploratory analytical product that:

- satisfies the course dashboard requirements,
- exceeds the minimum interactivity and chart coverage,
- supports academic storytelling,
- is reproducible from the raw export,
- and is organized in a way that is easy to defend in a final project report.

If needed, this document can also be adapted into:

- a methodology section,
- a dashboard design justification section,
- or presentation speaker notes.
