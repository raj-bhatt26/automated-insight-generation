import os
import pandas as pd
import streamlit as st
import plotly.express as px
from analytics import DEFAULT_INDICATORS, load_and_validate, generate_insights

import os
import streamlit as st
import pandas as pd
import plotly.express as px

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

default_path = os.path.join(DATA_DIR, "healthcare.csv")

st.set_page_config(page_title="Automated Insight Generation", page_icon="📊", layout="wide")
st.title("📊 Automated Insight Generation")
st.caption("Healthcare district performance • Data-driven trends, outliers and correlations")

with st.sidebar:
    st.header("Data")
    uploaded = st.file_uploader("Upload healthcare CSV", type=["csv"])
    default_path = os.path.join(DATA_DIR, "healthcare.csv")
    st.caption("Upload your own CSV or use the included sample dataset.")

    st.header("Detection settings")
    trend_threshold = st.slider("Significant trend threshold (%)", 1, 100, 10)
    outlier_method = st.selectbox("Outlier method", ["IQR", "Z-score"])
    iqr_multiplier = st.slider("IQR multiplier", 0.5, 3.0, 1.5, 0.1)
    z_threshold = st.slider("Z-score threshold", 1.0, 5.0, 3.0, 0.5)
    corr_threshold = st.slider("Correlation threshold (|r|)", 0.1, 1.0, 0.70, 0.05)

try:
    source = uploaded if uploaded is not None else default_path
    df = load_and_validate(source)

except Exception as exc:
    st.error(f"Could not load the dataset: {exc}")
    st.exception(exc)
    st.stop()

st.subheader("1. Data validation")
c1, c2, c3 = st.columns(3)
c1.metric("Rows", f"{len(df):,}")
c2.metric("Districts", df["district"].nunique())
c3.metric("Months", df["month"].dt.to_period("M").nunique())
with st.expander("Preview data and validation report", expanded=False):
    st.write("First five rows")
    st.dataframe(df.head(), use_container_width=True)
    st.write("Data types and non-null counts")
    st.dataframe(pd.DataFrame({"dtype": df.dtypes.astype(str), "non_null": df.notna().sum(), "missing": df.isna().sum()}), use_container_width=True)
    st.write("Missing values per column")
    st.dataframe(df.isna().sum().rename("missing_count").to_frame(), use_container_width=True)

indicators = [c for c in DEFAULT_INDICATORS if c in df.columns]
insights, corr = generate_insights(
    df, indicators, trend_threshold, outlier_method, iqr_multiplier, z_threshold, corr_threshold
)

st.subheader("2. Filter insights")
selected_severities = st.multiselect(
    "Severity",
    ["High", "Medium", "Low"],
    default=["High", "Medium", "Low"]
)
f1, f2, f3 = st.columns(3)
district_options = sorted(df["district"].dropna().astype(str).unique().tolist())
selected_districts = f1.multiselect("District", district_options, default=district_options)
type_options = ["trend", "outlier", "correlation"]
selected_types = f2.multiselect("Insight type", type_options, default=type_options)
selected_indicators = f3.multiselect("Indicator", indicators, default=indicators)

filtered = insights.copy()
selected_severities = st.multiselect(
    "Severity",
    ["High", "Medium", "Low"],
    default=["High"]
)

if selected_severities:
    filtered = filtered[
        filtered["severity"].isin(selected_severities)
    ]
else:
    filtered = filtered.iloc[0:0]
if selected_districts:
    filtered = filtered[(filtered["entity"].isin(selected_districts)) | (filtered["type"] == "correlation")]
else:
    filtered = filtered.iloc[0:0]
if selected_types:
    filtered = filtered[filtered["type"].isin(selected_types)]
else:
    filtered = filtered.iloc[0:0]
if selected_indicators:
    filtered = filtered[filtered["indicator"].apply(lambda x: any(ind in str(x).split(":") for ind in selected_indicators) or str(x) in selected_indicators)]
else:
    filtered = filtered.iloc[0:0]
if selected_severities:
    filtered = filtered[filtered["severity"].isin(selected_severities)]
else:
    filtered = filtered.iloc[0:0]

st.subheader("3. Generated insights")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Insights shown", len(filtered))
m2.metric("High severity", int((filtered["severity"] == "High").sum()) if not filtered.empty else 0)
m3.metric("Medium severity", int((filtered["severity"] == "Medium").sum()) if not filtered.empty else 0)
m4.metric("Low severity", int((filtered["severity"] == "Low").sum()) if not filtered.empty else 0)

if filtered.empty:
    st.info("No insights match the current filters and thresholds. Try adjusting the filters.")
else:
    st.dataframe(filtered, use_container_width=True, hide_index=True)
    st.download_button("Download filtered insights CSV", filtered.to_csv(index=False).encode("utf-8"), "insights.csv", "text/csv")

st.subheader("4. Visualizations")
left, right = st.columns(2)
with left:
    severity_counts = filtered["severity"].value_counts().reindex(["Low", "Medium", "High"], fill_value=0).rename_axis("severity").reset_index(name="count")
    fig = px.bar(severity_counts, x="severity", y="count", title="Insight count by severity", text="count")
    st.plotly_chart(fig, use_container_width=True)
with right:
    st.write("Pearson correlation heatmap")
    if corr.empty:
        st.info("Not enough numeric data to calculate correlations.")
    else:
        fig_corr = px.imshow(corr, text_auto=".2f", aspect="auto", color_continuous_scale="RdBu_r", zmin=-1, zmax=1)
        st.plotly_chart(fig_corr, use_container_width=True)

st.subheader("5. District performance over time")
chart_indicator = st.selectbox("Choose indicator for line chart", indicators)
chart_districts = st.multiselect("Districts to plot", district_options, default=district_options[:min(5, len(district_options))])
chart_df = df[df["district"].astype(str).isin(chart_districts)]
if not chart_df.empty:
    fig_line = px.line(chart_df, x="month", y=chart_indicator, color="district", markers=True,
                       title=f"{chart_indicator.replace('_', ' ').title()} by district")
    st.plotly_chart(fig_line, use_container_width=True)
else:
    st.info("Select at least one district to show the line chart.")

st.subheader("6. Export outputs")
st.download_button("Download all insights CSV", insights.to_csv(index=False).encode("utf-8"), "insights.csv", "text/csv")
st.download_button("Download correlation matrix CSV", corr.to_csv().encode("utf-8"), "correlation_matrix.csv", "text/csv")
st.caption("Note: correlations are descriptive, not causal. They may be unstable when the dataset has few rows or months.")
