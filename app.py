from __future__ import annotations

import json
import zipfile
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt


EXPORT_DIR = Path("exports")
EXPORT_DIR.mkdir(exist_ok=True)

LOGO_PATH = Path("assets/logo.png")
FAVICON_PATH = Path("assets/favicon.png")

ACCENT = "#DBA11C"


def infer_column_types(df: pd.DataFrame) -> dict[str, list[str]]:
    date_cols: list[str] = []
    for c in df.columns:
        if df[c].dtype == "object":
            s = df[c].dropna().astype(str)
            if len(s) == 0:
                continue
            sample = s.sample(min(200, len(s)), random_state=0)
            parsed = pd.to_datetime(
                sample, errors="coerce", infer_datetime_format=True)
            if parsed.notna().mean() >= 0.8:
                date_cols.append(c)

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    categorical_cols = [
        c for c in df.columns if c not in numeric_cols and c not in date_cols]
    return {"numeric": numeric_cols, "categorical": categorical_cols, "date": date_cols}


def kpi_stats(df: pd.DataFrame) -> dict:
    missing_pct = float(df.isna().mean().mean() *
                        100) if len(df.columns) else 0.0
    return {"rows": int(df.shape[0]), "columns": int(df.shape[1]), "missing_cells_pct": round(missing_pct, 2)}


def safe_filename(s: str) -> str:
    keep = "".join(ch if ch.isalnum() or ch in (
        "-", "_") else "_" for ch in s.strip())
    return keep[:80] if keep else "export"


def save_fig(fig, name: str) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = EXPORT_DIR / f"{safe_filename(name)}_{ts}.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    path_str = str(path)
    if path_str not in st.session_state["exported_files"]:
        st.session_state["exported_files"].append(path_str)
    return path


def bar_top_categories(series: pd.Series, top_n: int) -> pd.Series:
    s = series.dropna().astype(str)
    return s.value_counts().head(top_n)


st.set_page_config(
    page_title="Magic Data Visualizer",
    page_icon=str(FAVICON_PATH) if FAVICON_PATH.exists() else "📊",
    layout="wide",
)

# CSS polish (theme colors handled by .streamlit/config.toml)
st.markdown(
    f"""
    <style>
      .block-container {{
        padding-top: 1.6rem;
      }}
      /* Slightly nicer buttons */
      .stButton > button {{
        border-radius: 10px;
      }}
      /* Make header area breathe */
      .mdv-header {{
        margin-top: .25rem;
        margin-bottom: .75rem;
      }}
      .mdv-sub {{
        color: {ACCENT};
        margin-top: 0;
        margin-bottom: 0;
      }}
    </style>
    """,
    unsafe_allow_html=True,
)

# Session state
if "exported_files" not in st.session_state:
    st.session_state["exported_files"] = []
if "rendered_figs" not in st.session_state:
    st.session_state["rendered_figs"] = {}
if "last_zip" not in st.session_state:
    st.session_state["last_zip"] = None
if "last_zip_count" not in st.session_state:
    st.session_state["last_zip_count"] = 0

# Header (logo + title)
h1, h2 = st.columns([1.5, 8.5], vertical_alignment="center")
with h1:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), use_container_width=True)
with h2:
    st.markdown(
        """
        <div class="mdv-header">
          <h1 style="margin:0;">Magic Data Visualizer</h1>
          <p class="mdv-sub">Generic CSV Insight Dashboard • Auto Profiling • Smart Presets</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()

# Sidebar
with st.sidebar:
    st.header("Load data")
    uploaded = st.file_uploader("Upload a CSV", type=["csv"])
    st.caption("Or place a file in ./data and type its name below.")
    local_name = st.text_input("Local CSV filename (in ./data)", value="")

    st.divider()
    st.header("Options")
    sep = st.text_input("Delimiter", value=",",
                        help="Use ';' for semicolon CSVs")
    encoding = st.text_input("Encoding", value="utf-8")
    max_rows_preview = st.slider("Preview rows", 10, 500, 50)

    st.divider()
    st.header("Exports")
    export_report = st.checkbox("Write insights.json", value=True)
    export_charts = st.checkbox("Enable chart export buttons", value=True)

    st.divider()
    st.subheader("Export All")
    if st.button("Export all charts (ZIP)", key="export_all_zip"):
        figs = st.session_state.get("rendered_figs", {})
        if figs:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_path = EXPORT_DIR / f"exports_{ts}.zip"

            saved_paths: list[str] = []
            for key, figure in figs.items():
                p = save_fig(figure, f"all_{key}")
                saved_paths.append(str(p))

            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for sp in saved_paths:
                    zf.write(sp, Path(sp).name)

            st.session_state["last_zip"] = str(zip_path)
            st.session_state["last_zip_count"] = len(saved_paths)
        else:
            st.warning(
                "No charts available. Load a CSV and ensure charts are displayed.")

    if st.session_state["last_zip"] and Path(st.session_state["last_zip"]).exists():
        zp = Path(st.session_state["last_zip"])
        st.success(f"Zipped {st.session_state['last_zip_count']} chart(s)")
        st.download_button(
            "Download ZIP",
            data=zp.read_bytes(),
            file_name=zp.name,
            mime="application/zip",
            key="dl_zip",
        )


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

# Sidebar explore controls
with st.sidebar:
    st.header("Explore")
    numeric_cols = types["numeric"]
    cat_cols = types["categorical"]

    metric = st.selectbox(
        "Numeric metric", options=(numeric_cols or ["(none)"]))
    group_by = st.selectbox("Group by (categorical)",
                            options=(["(none)"] + cat_cols))
    agg = st.selectbox("Aggregation", options=[
                       "mean", "median", "sum", "count"])

    filter_col = st.selectbox("Filter column", options=(["(none)"] + cat_cols))
    filter_vals = None
    if filter_col != "(none)":
        uniq = sorted(df[filter_col].dropna().astype(str).unique().tolist())
        filter_vals = st.multiselect(
            "Allowed values", options=uniq, default=uniq)

filtered = df
if filter_col != "(none)" and filter_vals is not None:
    filtered = filtered[filtered[filter_col].astype(
        str).isin(set(filter_vals))]

# KPIs
kpis = kpi_stats(filtered)
c1, c2, c3 = st.columns(3)
c1.metric("Rows", kpis["rows"])
c2.metric("Columns", kpis["columns"])
c3.metric("Missing cells (%)", kpis["missing_cells_pct"])

st.subheader("Preview")
st.dataframe(filtered.head(max_rows_preview), use_container_width=True)

# Column profile
st.subheader("Column Profile")
_nonnull = filtered.notna().sum()
_total = len(filtered)
_nuniq = filtered.nunique()
_dtypes = filtered.dtypes.astype(str)
_numeric_cols_set = set(filtered.select_dtypes(include="number").columns)

_profile_records: list[dict] = []
for col in filtered.columns:
    first_valid = filtered[col].dropna().iloc[0] if _nonnull[col] > 0 else None
    sample = str(first_valid)[:50] if first_valid is not None else None
    is_num = col in _numeric_cols_set
    _profile_records.append(
        {
            "column_name": col,
            "dtype": _dtypes[col],
            "non_null_count": int(_nonnull[col]),
            "missing_pct": round((_total - int(_nonnull[col])) / _total * 100, 2) if _total else 0.0,
            "unique_values": int(_nuniq[col]),
            "sample_value": sample,
            "min": float(filtered[col].min()) if is_num else None,
            "max": float(filtered[col].max()) if is_num else None,
        }
    )

profile_df = pd.DataFrame(_profile_records)
st.dataframe(profile_df, use_container_width=True)

# Insights dict
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
    "column_profile": _profile_records,
}

# Reset rendered figs for this run
st.session_state["rendered_figs"] = {}

# Quick insights (HR presets)
_cols = set(filtered.columns)
_has_sal_dept = {"Salary", "Department"} <= _cols
_has_dept = "Department" in _cols
_has_attrition = {"EmploymentStatus", "Department"} <= _cols
_has_engage = {"EngagementSurvey", "PerformanceScore"} <= _cols

if any([_has_sal_dept, _has_dept, _has_attrition, _has_engage]):
    st.divider()
    st.subheader("Quick Insights (Auto-Detected)")
    qi_l, qi_r = st.columns(2)

    with qi_l:
        if _has_sal_dept and st.checkbox("Salary by Department (Mean)", key="qi_sal"):
            sal = (
                filtered.assign(Salary=pd.to_numeric(
                    filtered["Salary"], errors="coerce"))
                .groupby("Department")["Salary"]
                .mean()
                .sort_values(ascending=False)
            )
            fig_qs = plt.figure()
            plt.bar(sal.index.astype(str), sal.values)
            plt.xticks(rotation=45, ha="right")
            plt.xlabel("Department")
            plt.ylabel("Mean Salary")
            st.session_state["rendered_figs"]["qi_salary_by_dept"] = fig_qs
            st.pyplot(fig_qs)
            insights["quick_salary_by_dept"] = sal.round(2).to_dict()
            if export_charts and st.button("Export salary chart", key="exp_qs"):
                st.success(f"Saved: {save_fig(fig_qs, 'qi_salary_by_dept')}")

        if _has_dept and st.checkbox("Headcount by Department", key="qi_hc"):
            hc = filtered["Department"].value_counts()
            fig_qh = plt.figure()
            plt.bar(hc.index.astype(str), hc.values)
            plt.xticks(rotation=45, ha="right")
            plt.xlabel("Department")
            plt.ylabel("Headcount")
            st.session_state["rendered_figs"]["qi_headcount"] = fig_qh
            st.pyplot(fig_qh)
            insights["quick_headcount_by_dept"] = hc.to_dict()
            if export_charts and st.button("Export headcount chart", key="exp_qh"):
                st.success(
                    f"Saved: {save_fig(fig_qh, 'qi_headcount_by_dept')}")

    with qi_r:
        if _has_attrition and st.checkbox("Attrition by Department", key="qi_att"):
            att = (
                filtered.assign(
                    _non_active=(filtered["EmploymentStatus"].astype(
                        str).str.strip().str.lower() != "active").astype(int)
                )
                .groupby("Department")["_non_active"]
                .mean()
                .mul(100)
                .sort_values(ascending=False)
            )
            fig_qa = plt.figure()
            plt.bar(att.index.astype(str), att.values)
            plt.xticks(rotation=45, ha="right")
            plt.xlabel("Department")
            plt.ylabel("Non-Active (%)")
            st.session_state["rendered_figs"]["qi_attrition"] = fig_qa
            st.pyplot(fig_qa)
            insights["quick_attrition_by_dept"] = att.round(2).to_dict()
            if export_charts and st.button("Export attrition chart", key="exp_qa"):
                st.success(
                    f"Saved: {save_fig(fig_qa, 'qi_attrition_by_dept')}")

        if _has_engage and st.checkbox("Engagement vs Performance", key="qi_eng"):
            eng = filtered[["EngagementSurvey",
                            "PerformanceScore"]].dropna().copy()
            eng["EngagementSurvey"] = pd.to_numeric(
                eng["EngagementSurvey"], errors="coerce")
            labels = sorted(eng["PerformanceScore"].dropna().unique(), key=str)
            groups = [eng.loc[eng["PerformanceScore"] == lbl,
                              "EngagementSurvey"].dropna().values for lbl in labels]

            fig_qe = plt.figure()
            plt.boxplot(groups, labels=[str(lbl) for lbl in labels])
            plt.xticks(rotation=45, ha="right")
            plt.xlabel("PerformanceScore")
            plt.ylabel("EngagementSurvey")
            st.session_state["rendered_figs"]["qi_engagement"] = fig_qe
            st.pyplot(fig_qe)
            summary = eng.groupby("PerformanceScore")[
                "EngagementSurvey"].describe().round(4)
            insights["quick_engagement_vs_performance"] = summary.to_dict()
            if export_charts and st.button("Export engagement chart", key="exp_qe"):
                st.success(
                    f"Saved: {save_fig(fig_qe, 'qi_engagement_vs_performance')}")

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
        st.session_state["rendered_figs"]["histogram"] = fig
        st.pyplot(fig)
        if export_charts and st.button("Export histogram"):
            st.success(f"Saved: {save_fig(fig, f'hist_{metric}')}")
    else:
        st.info("No numeric columns detected.")

with right:
    st.subheader("Top categories")
    if cat_cols:
        cat = st.selectbox("Categorical column",
                           options=cat_cols, key="cat_col_chart")
        topn = st.slider("Top N", 5, 30, 10)
        vc = bar_top_categories(filtered[cat], topn)

        fig2 = plt.figure()
        plt.bar(vc.index.astype(str), vc.values)
        plt.xticks(rotation=45, ha="right")
        plt.ylabel("Count")
        plt.xlabel(cat)
        st.session_state["rendered_figs"]["categories"] = fig2
        st.pyplot(fig2)

        insights["top_categories"] = {
            "column": cat, "top_n": int(topn), "counts": vc.to_dict()}

        if export_charts and st.button("Export categories bar chart"):
            st.success(f"Saved: {save_fig(fig2, f'bar_{cat}')}")
    else:
        st.info("No categorical columns detected.")

st.subheader("Grouped metric")
if metric != "(none)" and group_by != "(none)":
    g = filtered.copy()
    g[metric] = pd.to_numeric(g[metric], errors="coerce")
    grouped = g.groupby(group_by, dropna=False)[metric].agg(
        agg).sort_values(ascending=False).head(30)

    fig3 = plt.figure()
    plt.bar(grouped.index.astype(str), grouped.values)
    plt.xticks(rotation=45, ha="right")
    plt.xlabel(group_by)
    plt.ylabel(f"{agg}({metric})")
    st.session_state["rendered_figs"]["grouped_metric"] = fig3
    st.pyplot(fig3)

    insights["grouped_metric"] = {
        "metric": metric, "group_by": group_by, "agg": agg, "top_30": grouped.to_dict()}

    if export_charts and st.button("Export grouped metric chart"):
        st.success(
            f"Saved: {save_fig(fig3, f'grouped_{metric}_by_{group_by}_{agg}')}")
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
    st.session_state["rendered_figs"]["correlation"] = fig4
    st.pyplot(fig4)

    insights["correlation"] = corr.round(4).to_dict()

    if export_charts and st.button("Export correlation heatmap"):
        st.success(f"Saved: {save_fig(fig4, 'corr_heatmap')}")
else:
    st.info("Need at least 2 numeric columns for correlation.")

if export_report:
    Path("insights.json").write_text(json.dumps(
        insights, indent=2, ensure_ascii=False), encoding="utf-8")
    st.caption("Wrote insights.json in the project root.")