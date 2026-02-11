# Magic Data Visualizer

*A reusable, browser-based CSV analysis tool built with Streamlit. Provides automatic column profiling, smart visualization presets, and one-click export functionality. Built with Python and Pandas as part of the **Codecademy AI Maker Bootcamp**.*

---

## Features

- **CSV ingestion** -- upload via browser or load from the local `./data` folder
- **Automatic column type detection** -- numeric, categorical, and date columns identified on load
- **KPI overview** -- row count, column count, and missing-cell percentage at a glance
- **Column profiling table** -- dtype, null counts, unique values, min/max, and sample values per column
- **Numeric distribution** -- histogram for any selected numeric column
- **Categorical top-N analysis** -- bar chart of the most frequent values in any categorical column
- **Grouped metric aggregation** -- mean, median, sum, or count of a numeric metric grouped by a categorical column
- **Correlation heatmap** -- pairwise correlation matrix for all numeric columns
- **Smart HR presets** -- one-click insights for Salary by Department, Headcount, Attrition, and Engagement vs Performance (auto-detected when matching columns exist)
- **Individual chart export** -- save any chart as a PNG from the dashboard
- **Export all charts as ZIP** -- bundle every rendered chart into a single downloadable archive
- **JSON insights report** -- structured `insights.json` written automatically with all computed metrics
- **Safe, browser-based UI** -- no manual matplotlib coding required; all interaction happens in the browser

---

## Live Demo

[https://magic-data-visualizer.streamlit.app/](https://magic-data-visualizer.streamlit.app/)

---

## Installation and Local Run

### 1. Clone the repository

```bash
git clone https://github.com/<your-org>/data-visualiser.git
cd data-visualiser
```

### 2. Create and activate a virtual environment

Windows:

```bash
python -m venv venv
```

```bash
venv\Scripts\activate
```

macOS / Linux:

```bash
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

Start the application using either method:

```bash
# Option 1 -- launch helper (starts server and opens browser automatically)
py run.py

# Option 2 -- run Streamlit directly
py -m streamlit run app.py
```

The dashboard opens automatically at `http://localhost:8501`.

---

## Deployment

The application is deployed via **Streamlit Community Cloud**:

- Connected directly to the GitHub repository
- No separate backend or server infrastructure required
- Hosted at a public URL accessible to anyone with the link
- Automatic redeployment on push to the main branch

---

## Theme and Branding

Custom favicon and branded header logo are included in the `assets/` directory. Theme settings are defined in `.streamlit/config.toml`.

---

## Tech Stack

| Component   | Details                     |
|-------------|-----------------------------|
| Python      | 3.12+                       |
| Streamlit   | Web framework and UI        |
| Pandas      | Data loading and analysis   |
| Matplotlib  | Chart rendering             |
| zipfile     | ZIP archive creation (stdlib) |
| json        | Insights report serialization (stdlib) |

---

## Project Context

Magic Data Visualizer was built as a demo-ready, reusable data exploration tool. The primary goals are:

- **Usability** -- load any CSV and get immediate visual insights with zero configuration
- **Safety** -- all processing runs in-browser; no data leaves the local environment unless explicitly deployed
- **Automation** -- column types, KPIs, and profiling are computed automatically on every load

Designed to quickly generate actionable insights from arbitrary CSV files without writing code.

---
