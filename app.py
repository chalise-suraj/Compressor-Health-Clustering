from __future__ import annotations

import json
import math
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
MODEL_METADATA_PATH = PROJECT_ROOT / "models" / "kmeans_metadata_5min.json"
MONITORING_PATH = PROCESSED_DIR / "metropt_condition_monitoring_5min.csv"
FEATURES_PATH = PROCESSED_DIR / "metropt_window_features_5min.csv"
EVENT_SUMMARY_PATH = PROCESSED_DIR / "metropt_reported_event_summary_5min.csv"
TRANSITIONS_PATH = PROCESSED_DIR / "metropt_cluster_transitions_5min.csv"

CLUSTER_COLORS = ["#56B4E9", "#E69F00", "#009E73", "#D55E00", "#CC79A7", "#F0E442"]
SENSOR_OPTIONS = {
    "TP2 pressure (bar)": "TP2__mean",
    "TP3 pressure (bar)": "TP3__mean",
    "H1 pressure (bar)": "H1__mean",
    "Dryer pressure drop (bar)": "DV_pressure__mean",
    "Reservoir pressure (bar)": "Reservoirs__mean",
    "Oil temperature (°C)": "Oil_temperature__mean",
    "Motor current (A)": "Motor_current__mean",
}

st.set_page_config(
    page_title="Compressor Health Clustering",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .stApp { background: #151B23; color: #E6EDF3; }
    [data-testid="stSidebar"] { background: #202833; }
    [data-testid="stMetric"] { background: #202833; border: 1px solid #3B4653;
        padding: 0.8rem 1rem; border-radius: 0.6rem; }
    .block-container { padding-top: 1.5rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner="Loading saved monitoring outputs...")
def load_dashboard_data():
    monitoring = pd.read_csv(MONITORING_PATH, parse_dates=["window_start", "window_end"])
    features = pd.read_csv(FEATURES_PATH)
    merged = monitoring.merge(
        features,
        on=["segment_id", "window_id"],
        how="left",
        validate="one_to_one",
    )
    event_summary = pd.read_csv(EVENT_SUMMARY_PATH, parse_dates=["start", "end"])
    transitions = pd.read_csv(TRANSITIONS_PATH, index_col=0)
    model_metadata = json.loads(MODEL_METADATA_PATH.read_text(encoding="utf-8"))
    return merged, event_summary, transitions, model_metadata


def require_artifacts() -> bool:
    required = [
        MONITORING_PATH,
        FEATURES_PATH,
        EVENT_SUMMARY_PATH,
        TRANSITIONS_PATH,
        MODEL_METADATA_PATH,
    ]
    missing = [path for path in required if not path.is_file()]
    if missing:
        st.error("Monitoring outputs are not available yet.")
        st.markdown(
            "Run notebooks 01-04 in order and save their outputs. Missing files: "
            + ", ".join(f"`{path.relative_to(PROJECT_ROOT)}`" for path in missing)
        )
        return False
    return True


st.title("Compressor Operating Behavior")
st.caption("Historical offline monitoring prototype · MetroPT-3 air compressor")
st.info(
    "Clusters describe patterns in the recorded sensor features. They are not health grades, "
    "fault confirmations, or failure probabilities. This dashboard is not live monitoring."
)

if not require_artifacts():
    st.stop()

try:
    data, event_summary, transitions, model_metadata = load_dashboard_data()
except Exception as exc:  # Surface mismatched or incomplete saved outputs clearly.
    st.error(f"Could not load the saved project outputs: {exc}")
    st.stop()

if data.empty:
    st.warning("The saved monitoring table contains no assigned windows.")
    st.stop()

clusters = sorted(int(value) for value in data["cluster"].dropna().unique())
min_day = data["window_start"].min().date()
max_day = data["window_start"].max().date()

with st.sidebar:
    st.header("Filters")
    date_range = st.date_input(
        "Window start date",
        value=(min_day, max_day),
        min_value=min_day,
        max_value=max_day,
    )
    selected_clusters = st.multiselect("Clusters", options=clusters, default=clusters)
    show_events = st.checkbox("Show reported event periods", value=True)
    st.divider()
    st.caption(f"Saved model: provisional k={model_metadata.get('provisional_k', 'unknown')}")
    st.caption("Feature window: 5 minutes")

if date_range is None:
    start_day, end_day = min_day, max_day
elif isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_day, end_day = date_range
else:
    start_day = end_day = date_range
start_time = pd.Timestamp(start_day)
end_time = pd.Timestamp(end_day) + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
filtered = data.loc[
    data["window_start"].between(start_time, end_time)
    & data["cluster"].isin(selected_clusters)
].copy()

persistent_count = int(filtered["persistent_unusual_behavior"].fillna(False).sum())
distance_count = int(filtered["distance_alert"].fillna(False).sum())
event_overlap_count = int(filtered["reported_event_ids"].fillna("").ne("").sum())

metric_cols = st.columns(4)
metric_cols[0].metric("Assigned windows", f"{len(filtered):,}")
metric_cols[1].metric("Operating clusters", f"{filtered['cluster'].nunique()}")
metric_cols[2].metric("Distance alerts", f"{distance_count:,}")
metric_cols[3].metric("Persistent unusual windows", f"{persistent_count:,}")

if filtered.empty:
    st.warning("No assigned windows match the selected dates and clusters.")
    st.stop()

st.subheader("Operating-state timeline")
plot_data = filtered.sort_values("window_start")
if len(plot_data) > 12_000:
    stride = math.ceil(len(plot_data) / 12_000)
    sampled = plot_data.iloc[::stride]
    persistent_rows = plot_data.loc[plot_data["persistent_unusual_behavior"].fillna(False)]
    plot_data = pd.concat([sampled, persistent_rows]).drop_duplicates(
        ["segment_id", "window_id"]
    ).sort_values("window_start")
plot_data["cluster_label"] = plot_data["cluster"].astype(str)
fig = px.scatter(
    plot_data,
    x="window_start",
    y="cluster",
    color="cluster_label",
    color_discrete_sequence=CLUSTER_COLORS,
    render_mode="webgl",
    hover_data={
        "window_end": True,
        "nearest_center_distance": ":.2f",
        "distance_threshold": ":.2f",
        "reported_event_ids": True,
        "cluster": True,
    },
    labels={"window_start": "Window start", "cluster": "Arbitrary cluster ID", "cluster_label": "Cluster"},
)
fig.update_traces(marker={"size": 5, "opacity": 0.72})
persistent_rows = plot_data.loc[plot_data["persistent_unusual_behavior"].fillna(False)]
if not persistent_rows.empty:
    fig.add_trace(go.Scatter(
        x=persistent_rows["window_start"], y=persistent_rows["cluster"],
        mode="markers", name="Persistent unusual behavior",
        marker={"symbol": "x", "size": 11, "color": "#FF6B6B"},
        customdata=persistent_rows[["nearest_center_distance", "reported_event_ids"]],
        hovertemplate="Persistent unusual behavior<br>%{x}<br>Distance: %{customdata[0]:.2f}<br>Events: %{customdata[1]}<extra></extra>",
    ))
if show_events:
    event_periods = [
        ("Event 1", "2020-04-18 00:00", "2020-04-18 23:59"),
        ("Event 2", "2020-05-29 23:30", "2020-05-30 06:00"),
        ("Event 3", "2020-06-05 10:00", "2020-06-07 14:30"),
        ("Event 4", "2020-07-15 14:30", "2020-07-15 19:00"),
    ]
    for label, start, end in event_periods:
        event_start = pd.Timestamp(start)
        event_end = pd.Timestamp(end)
        if event_start <= end_time and event_end >= start_time:
            fig.add_vrect(
                x0=max(event_start, start_time), x1=min(event_end, end_time),
                fillcolor="#FF6B6B", opacity=0.12,
                line_width=0, annotation_text=label, annotation_position="top left",
            )
fig.update_layout(
    template="plotly_dark", height=430, margin={"l": 10, "r": 10, "t": 35, "b": 10},
    legend_title_text="Observed grouping",
)
st.plotly_chart(fig, use_container_width=True)

left, right = st.columns([1.4, 1])
with left:
    st.subheader("Daily cluster share")
    daily = filtered.assign(day=filtered["window_start"].dt.floor("D"))
    visible_clusters = sorted(int(value) for value in filtered["cluster"].unique())
    daily_counts = daily.groupby(["day", "cluster"]).size().unstack("cluster")
    full_days = pd.date_range(daily_counts.index.min(), daily_counts.index.max(), freq="D")
    daily_counts = daily_counts.reindex(index=full_days, columns=visible_clusters)
    observed_day = daily_counts.notna().any(axis=1)
    daily_counts.loc[observed_day] = daily_counts.loc[observed_day].fillna(0)
    daily_share = daily_counts.div(daily_counts.sum(axis=1), axis=0).where(observed_day)
    daily_long = daily_share.rename_axis("date").reset_index().melt(
        id_vars="date", var_name="cluster", value_name="share"
    )
    daily_long["cluster"] = daily_long["cluster"].astype(str)
    daily_fig = px.line(
        daily_long, x="date", y="share", color="cluster",
        color_discrete_sequence=CLUSTER_COLORS,
        labels={"date": "Date", "share": "Window share", "cluster": "Cluster"},
        category_orders={"cluster": [str(value) for value in visible_clusters]},
    )
    daily_fig.update_layout(template="plotly_dark", height=360, yaxis={"range": [0, 1]})
    st.plotly_chart(daily_fig, use_container_width=True)

with right:
    st.subheader("Sensor trend by cluster")
    available_sensors = {label: col for label, col in SENSOR_OPTIONS.items() if col in filtered.columns}
    if not available_sensors:
        st.info("No configured sensor summary columns are present in the saved feature table.")
    else:
        selected_sensor_label = st.selectbox("Sensor summary", list(available_sensors))
        sensor_column = available_sensors[selected_sensor_label]
        sensor_data = filtered[["window_start", "cluster", sensor_column]].dropna().sort_values("window_start").copy()
        sensor_data["cluster_label"] = sensor_data["cluster"].astype(str)
        if len(sensor_data) > 8_000:
            sensor_data = sensor_data.iloc[::math.ceil(len(sensor_data) / 8_000)]
        sensor_fig = px.scatter(
            sensor_data, x="window_start", y=sensor_column, color="cluster_label",
            color_discrete_sequence=CLUSTER_COLORS,
            labels={"window_start": "Window start", sensor_column: selected_sensor_label, "cluster_label": "Cluster"},
        )
        sensor_fig.update_traces(marker={"size": 5, "opacity": 0.65})
        sensor_fig.update_layout(template="plotly_dark", height=360)
        st.plotly_chart(sensor_fig, use_container_width=True)

st.subheader("Reported event comparison")
st.caption(
    "Event periods are source-document annotations, not row-level verified labels. "
    "All four periods fall in the training period for the saved model."
)
if event_summary.empty:
    st.info("No event summary is available.")
else:
    st.dataframe(event_summary, use_container_width=True, hide_index=True)

with st.expander("Cluster transition probabilities"):
    transition_display = transitions.copy()
    transition_display.index.name = "From cluster"
    transition_display.columns.name = "To cluster"
    st.dataframe(transition_display.style.format("{:.2f}"), use_container_width=True)

with st.expander("Window-level unusual behavior"):
    alert_rows = filtered.loc[
        filtered["distance_alert"].fillna(False)
        | filtered["persistent_unusual_behavior"].fillna(False)
    ].sort_values("nearest_center_distance", ascending=False)
    st.dataframe(
        alert_rows[["window_start", "cluster", "nearest_center_distance", "distance_threshold",
                    "distance_alert", "persistent_unusual_behavior", "reported_event_ids"]],
        use_container_width=True,
        hide_index=True,
    )

st.caption(
    "Distance alerts use cluster-specific 99th-percentile training references; persistent flags "
    "require three adjacent 5-minute windows. These are review rules, not validated alarm limits."
)
