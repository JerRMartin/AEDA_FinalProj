# PRISM Evidence Analytics Dashboard

This project delivers a polished Streamlit dashboard for exploratory analysis of the PRISM Database Export. The app is designed for academic presentation, with a narrative layout, interactive filters, dynamic KPI cards, and multiple chart types that support explanation in an AEDA final project report.

## Dashboard Purpose

The dashboard helps answer five core analytical questions:

1. What is the overall scale and quality of the PRISM evidence base?
2. Which indicators and thematic groups are most prevalent?
3. How are quality scores distributed across topics?
4. Do source credibility and overall quality move together?
5. How do evidence volume and mean quality evolve over time?

## Dataset Source

- Dataset name: `PRISM Database Export`
- Source type: local export bundled in this repository under `csv/`
- Export note: the repository README states the tables were exported on April 15, 2026
- Public dataset URL: not available in the provided export

Because no public source URL was included with the export, reproducibility is achieved by shipping the raw database table extracts directly in this project.

## Run Instructions

Install dependencies:

```bash
pip install -r requirements.txt
```

Launch the dashboard:

```bash
streamlit run app.py
```

## Project Structure

```text
prism_database_export/
├── app.py
├── assets/
│   └── theme.css
├── csv/
│   ├── data_extractions
│   ├── data_points
│   ├── documents
│   └── locations
├── src/
│   ├── charts.py
│   ├── data_loader.py
│   ├── metrics.py
│   ├── preprocessing.py
│   └── utils.py
├── requirements.txt
├── README.md
└── .streamlit/
    └── config.toml
```

## Reproducibility Notes

- The app reads the raw PRISM export tables directly from the repository.
- No absolute paths are used; all file access is relative to the project root.
- Streamlit caching is enabled for data loading and preprocessing to keep the UI responsive.
- The dashboard gracefully handles empty filtered states and non-numeric extraction values.

## Analytical Design Notes

The dashboard is intentionally organized as:

`summary -> composition -> distributions -> relationships -> trends -> insights`

Implemented rubric-aligned features include:

- 5 dynamic KPI cards
- 6 chart views across distribution, association, amounts, proportions, and evolution
- 5 interactive controls in the sidebar
- custom Plotly tooltips
- centrally managed accessible color palette
- chart titles, axis labels, legends, and explanatory captions
- downloadable filtered dataset for transparency during demonstrations
