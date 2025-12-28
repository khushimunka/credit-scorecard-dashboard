import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from score_engine import run_model

st.set_page_config(page_title="AI Credit Scorecard", layout="wide")
st.title("AI-Based Credit Scorecard Dashboard (Lender View)")

# Load
df = pd.read_csv("inputs_newgen.csv")
df["value"] = pd.to_numeric(df["value"], errors="coerce")

# Sidebar editor
st.sidebar.header("Edit Inputs")
group_choice = st.sidebar.selectbox("Select input group", ["quant", "qual"])

subset = df[df["group"] == group_choice].copy()
for i, row in subset.iterrows():
    df.loc[i, "value"] = st.sidebar.number_input(
        row["metric"], value=float(row["value"]), step=0.1
    )

# Run model
res = run_model(df)

# Top KPIs
c1, c2, c3, c4 = st.columns(4)
c1.metric("Quantitative Score (0–100)", res["quant_score"])
c2.metric("Qualitative Score (0–100)", res["qual_score"])
c3.metric("Final Composite Score", res["final_score"])
c4.metric("Decision", res["decision"])

st.divider()

# --- Two score panels ---
left, right = st.columns(2)

with left:
    st.subheader("Quantitative Drivers (Weighted)")
    q_tbl = pd.DataFrame({
        "Metric": list(res["q_subs"].keys()),
        "Sub-Score (0-100)": list(res["q_subs"].values()),
        "Weight": [res["q_w"][k] for k in res["q_subs"].keys()],
        "Weighted Contribution": [res["q_contrib"][k] for k in res["q_subs"].keys()]
    }).sort_values("Weighted Contribution", ascending=False)

    st.dataframe(q_tbl, use_container_width=True)

    fig_q = px.bar(q_tbl, x="Weighted Contribution", y="Metric", orientation="h")
    st.plotly_chart(fig_q, use_container_width=True)

with right:
    st.subheader("Qualitative Drivers (Weighted)")
    qual_tbl = pd.DataFrame({
        "Metric": list(res["qual_subs"].keys()),
        "Sub-Score (0-100)": list(res["qual_subs"].values()),
        "Weight": [res["qual_w"][k] for k in res["qual_subs"].keys()],
        "Weighted Contribution": [res["qual_contrib"][k] for k in res["qual_subs"].keys()]
    }).sort_values("Weighted Contribution", ascending=False)

    st.dataframe(qual_tbl, use_container_width=True)

    fig_qual = px.bar(qual_tbl, x="Weighted Contribution", y="Metric", orientation="h")
    st.plotly_chart(fig_qual, use_container_width=True)

st.divider()

# Radar chart (at-a-glance shape)
st.subheader("Risk Profile Radar (Sub-scores)")
radar_labels = ["Liquidity", "Coverage", "Leverage", "Margins", "Growth", "Cashflows", "Governance", "Management", "Tech", "Client Risk"]
radar_values = [
    res["q_subs"].get("Current Ratio", 0),
    res["q_subs"].get("Interest Coverage", 0),
    res["q_subs"].get("Debt-to-Equity", 0),
    res["q_subs"].get("EBITDA Margin (%)", 0),
    res["q_subs"].get("Revenue Growth YoY (%)", 0),
    res["q_subs"].get("Operating Cash Flow / EBITDA", 0),
    res["qual_subs"].get("Governance & Transparency (1-5)", 0),
    res["qual_subs"].get("Management Capability (1-5)", 0),
    res["qual_subs"].get("Technology & Innovation (1-5)", 0),
    res["qual_subs"].get("Customer Concentration Risk (1-5)", 0),
]
radar_values += [radar_values[0]]
radar_labels += [radar_labels[0]]

fig_radar = go.Figure()
fig_radar.add_trace(go.Scatterpolar(r=radar_values, theta=radar_labels, fill="toself"))
fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0,100])), showlegend=False)
st.plotly_chart(fig_radar, use_container_width=True)

st.divider()

# Covenants section
st.subheader("Recommended Covenants / Conditions")
for i, cov in enumerate(res["covenants"], 1):
    st.write(f"{i}. {cov}")

st.caption("Note: This is an explainable scorecard for academic use. In real lending, thresholds, weights, and covenants are calibrated using historical default data and RBI-aligned credit policy.")
