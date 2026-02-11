from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt


EXPORT_DIR = Path("exports")
EXPORT_DIR.mkdir(exist_ok=True)


def infer_column_types(df: pd.DataFrame) -> dict[str, list[str]]:
    # Try to parse date-like object columns (lightweight)
    date_cols: list[str] = []
    for c in df.columns:
        if df[c].dtype == "object":
            s = df[c].dropna().astype(str)
            if len(s) == 0:
                continue
            sample = s.sample(min(200, len(s)), random_state=0)
            parsed = pd.to_datetime(sample, errors="coerce", infer_datetime_format=True)
            if parsed.notna().mean() >= 0.8:
                date_cols.append(c)

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    # Categorical: non-numeric, non-date, with reasonable cardinality
    categorical_cols = [
        c for c in df.columns
        if c not in numeric_cols and c not in date_cols
    ]

    return {"numeric": numeric_cols, "categorical": categorical_cols, "date": date_cols}


def kpi_stats(df: pd.DataFrame) -> dict:
    missing_pct = float(df.isna().mean().mean() * 100) if len(df.columns) else 0.0
    return {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "missing_cells_pct": round(missing_pct, 2),
    }


def safe_filename(s: str) -> str:
    keep = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in s.strip())
    return keep[:80] if keep else "export"


def save_fig(fig, name: str) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = EXPORT_DIR / f"{safe_filename(name)}_{ts}.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    return path


def bar_top_categories(series: pd.Series, top_n: int) -> pd.Series:
    s = series.dropna().astype(str)
    vc = s.value_counts().head(top_n)
    return vc


st.set_page_config(page_title="CSV Insight Dashboard", layout="wide")
st.title("CSV Insight Dashboard")

with st.sidebar:
    st.header("Load data")
    uploaded = st.file_uploader("Upload a CSV", type=["csv"])
    st.caption("Or place a file in ./data and type its name below.")
    local_name = st.text_input("Local CSV filename (in ./data)", value="")

    st.divider()
    st.header("Options")
    sep = st.text_input("Delimiter", value=",", help="Use ';' for semicolon CSVs")
    encoding = st.text_input("Encoding", value="utf-8")
    max_rows_preview = st.slider("Preview rows", 10, 500, 50)

    st.divider()
    st.header("Exports")
    export_report = st.checkbox("Write insights.json", value=True)
    export_charts = st.checkbox("Enable chart export buttons", value=True)


def load_df() -> pd.DataFrame | None:
    try:
        if uploaded is not None:
            return pd.read_csv(uploaded, sep=sep, encoding=encoding)
        if local_name.strip():
            p = Path("data") / local_name.strip()
            if p.exists():
                return pd.read_csv(p, sep=sep, encoding=encoding)
            st.error(f"File not found: {p}")
            return None
        st.info("Upload a CSV or provide a local filename in ./data.")
        return None
    except Exception as e:
        st.error(f"Failed to load CSV: {type(e).__name__}: {e}")
        return None


df = load_df()
if df is None:
    st.stop()

types = infer_column_types(df)

# Sidebar controls for exploration
with st.sidebar:
    st.header("Explore")
    numeric_cols = types["numeric"]
    cat_cols = types["categorical"]
    date_cols = types["date"]

    metric = st.selectbox("Numeric metric", options=(numeric_cols or ["(none)"]))
    group_by = st.selectbox("Group by (categorical)", options=(["(none)"] + cat_cols))
    agg = st.selectbox("Aggregation", options=["mean", "median", "sum", "count"])

    # Simple filter: pick one categorical column and allowed values
    filter_col = st.selectbox("Filter column", options=(["(none)"] + cat_cols))
    filter_vals = None
    if filter_col != "(none)":
        uniq = sorted(df[filter_col].dropna().astype(str).unique().tolist())
        filter_vals = st.multiselect("Allowed values", options=uniq, default=uniq)

filtered = df
if filter_col != "(none)" and filter_vals is not None:
    filtered = filtered[filtered[filter_col].astype(str).isin(set(filter_vals))]

# KPIs
kpis = kpi_stats(filtered)
c1, c2, c3 = st.columns(3)
c1.metric("Rows", kpis["rows"])
c2.metric("Columns", kpis["columns"])
c3.metric("Missing cells (%)", kpis["missing_cells_pct"])

st.subheader("Preview")
st.dataframe(filtered.head(max_rows_preview), use_container_width=True)

# Insights dict for report
insights = {
    "generated_at": datetime.now().isoformat(timespec="seconds"),
    "settings": {
        "delimiter": sep,
        "encoding": encoding,
        "filter_col": filter_col,
        "filter_vals": filter_vals,
        "metric": metric,
        "group_by": group_by,
        "agg": agg,
    },
    "kpis": kpis,
    "columns": types,
}

st.divider()
left, right = st.columns(2)

with left:
    st.subheader("Numeric distribution")
    if metric != "(none)":
        s = pd.to_numeric(filtered[metric], errors="coerce").dropna()
        fig = plt.figure()
        plt.hist(s, bins=30)
        plt.xlabel(metric)
        plt.ylabel("Count")
        st.pyplot(fig)

        if export_charts and st.button("Export histogram"):
            p = save_fig(fig, f"hist_{metric}")
            st.success(f"Saved: {p}")
    else:
        st.info("No numeric columns detected.")

with right:
    st.subheader("Top categories")
    if cat_cols:
        cat = st.selectbox("Categorical column", options=cat_cols, key="cat_col_chart")
        topn = st.slider("Top N", 5, 30, 10)
        vc = bar_top_categories(filtered[cat], topn)

        fig2 = plt.figure()
        plt.bar(vc.index.astype(str), vc.values)
        plt.xticks(rotation=45, ha="right")
        plt.ylabel("Count")
        plt.xlabel(cat)
        st.pyplot(fig2)

        insights["top_categories"] = {"column": cat, "top_n": int(topn), "counts": vc.to_dict()}

        if export_charts and st.button("Export categories bar chart"):
            p = save_fig(fig2, f"bar_{cat}")
            st.success(f"Saved: {p}")
    else:
        st.info("No categorical columns detected.")

st.subheader("Grouped metric")
if metric != "(none)" and group_by != "(none)":
    g = filtered.copy()
    g[metric] = pd.to_numeric(g[metric], errors="coerce")
    grouped = g.groupby(group_by, dropna=False)[metric].agg(agg).sort_values(ascending=False).head(30)

    fig3 = plt.figure()
    plt.bar(grouped.index.astype(str), grouped.values)
    plt.xticks(rotation=45, ha="right")
    plt.xlabel(group_by)
    plt.ylabel(f"{agg}({metric})")
    st.pyplot(fig3)

    insights["grouped_metric"] = {
        "metric": metric,
        "group_by": group_by,
        "agg": agg,
        "top_30": grouped.to_dict(),
    }

    if export_charts and st.button("Export grouped metric chart"):
        p = save_fig(fig3, f"grouped_{metric}_by_{group_by}_{agg}")
        st.success(f"Saved: {p}")
else:
    st.info("Select a numeric metric and a group-by column to see a grouped chart.")

st.subheader("Correlation heatmap (numeric only)")
if len(types["numeric"]) >= 2:
    corr = filtered[types["numeric"]].corr(numeric_only=True)
    fig4 = plt.figure()
    plt.imshow(corr.values)
    plt.xticks(range(len(corr.columns)), corr.columns, rotation=45, ha="right")
    plt.yticks(range(len(corr.index)), corr.index)
    plt.colorbar()
    st.pyplot(fig4)

    insights["correlation"] = corr.round(4).to_dict()

    if export_charts and st.button("Export correlation heatmap"):
        p = save_fig(fig4, "corr_heatmap")
        st.success(f"Saved: {p}")
else:
    st.info("Need at least 2 numeric columns for correlation.")

# Write insights.json
if export_report:
    Path("insights.json").write_text(json.dumps(insights, indent=2, ensure_ascii=False), encoding="utf-8")
    st.caption("Wrote insights.json in the project root.")
