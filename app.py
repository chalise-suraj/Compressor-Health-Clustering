from __future__ import annotations

import json
import math
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


ROOT = Path(__file__).resolve().parent
PROCESSED = ROOT / "data" / "processed"
MONITORING_FILE = PROCESSED / "metropt_condition_monitoring_5min.csv"
FEATURES_FILE = PROCESSED / "metropt_window_features_5min.csv"
EVENTS_FILE = PROCESSED / "metropt_reported_event_summary_5min.csv"
TRANSITIONS_FILE = PROCESSED / "metropt_cluster_transitions_5min.csv"
MODEL_FILE = ROOT / "models" / "kmeans_metadata_5min.json"

THEMES = {
    "Field Notes": {
        "page": "#EAE8E0", "surface": "#F4F2EB", "text": "#252A28", "muted": "#646C66",
        "accent": "#B84C31", "sidebar": "#202725", "sidebar_text": "#F1F0E8",
        "input": "#303A36", "grid": "#34414A", "chart": "#17212A",
        "series": ["#55C2D1", "#F4B860", "#77C6A3", "#F07878", "#B5A0F2", "#E68BC3"],
        "scheme": "light",
    },
    "Glacier": {
        "page": "#E6EDF0", "surface": "#F3F7F8", "text": "#203039", "muted": "#5D7078",
        "accent": "#267C91", "sidebar": "#1C3038", "sidebar_text": "#ECF5F6",
        "input": "#2A4149", "grid": "#344A53", "chart": "#172931",
        "series": ["#59C6D5", "#F1B95C", "#8BC9A7", "#EF8278", "#B3A1E8", "#E698C4"],
        "scheme": "light",
    },
    "Juniper": {
        "page": "#E8EAE2", "surface": "#F3F4ED", "text": "#29312A", "muted": "#687164",
        "accent": "#657C56", "sidebar": "#252F29", "sidebar_text": "#F0F2E9",
        "input": "#354139", "grid": "#3A493F", "chart": "#1A2921",
        "series": ["#70C6BD", "#E6B75E", "#91C77D", "#EA8172", "#AAA0DF", "#DA91B0"],
        "scheme": "light",
    },
    "Silver & Cobalt": {
        "page": "#E8EAF0", "surface": "#F4F5F8", "text": "#252A35", "muted": "#626A7A",
        "accent": "#52699A", "sidebar": "#232B39", "sidebar_text": "#F3F4F8",
        "input": "#313B4D", "grid": "#3B465A", "chart": "#19212D",
        "series": ["#61C4D1", "#EAB65F", "#83BE9D", "#E77D78", "#A99CE2", "#D88FB7"],
        "scheme": "light",
    },
    "Graphite": {
        "page": "#24282B", "surface": "#303639", "text": "#F0F1EE", "muted": "#B9C0BF",
        "accent": "#9BA9A8", "sidebar": "#1C2022", "sidebar_text": "#F0F1EE",
        "input": "#2A3032", "grid": "#485052", "chart": "#1B2022",
        "series": ["#66C6D1", "#E9B66B", "#89C7A2", "#EC8278", "#B1A3E6", "#DF96BE"],
        "scheme": "dark",
    },
}
SENSOR_FIELDS = {
    "TP2 pressure": ("TP2__mean", "bar"),
    "TP3 pressure": ("TP3__mean", "bar"),
    "H1 pressure": ("H1__mean", "bar"),
    "Dryer pressure drop": ("DV_pressure__mean", "bar"),
    "Reservoir pressure": ("Reservoirs__mean", "bar"),
    "Oil temperature": ("Oil_temperature__mean", "°C"),
    "Motor current": ("Motor_current__mean", "A"),
}
REQUIRED_MONITORING = {
    "segment_id", "window_id", "window_start", "window_end", "cluster",
    "nearest_center_distance", "distance_threshold", "distance_alert",
    "persistent_unusual_behavior", "reported_event_ids",
}

st.set_page_config(
    page_title="Compressor | Operations intelligence",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.set_option("client.showErrorDetails", "none")

with st.sidebar:
    selected_theme_name = st.selectbox(
        "Color palette", list(THEMES), index=0,
        help="Changes the interface palette. Text and input colors are paired for contrast.",
    )
theme = THEMES[selected_theme_name]
PALETTE = theme["series"]
BACKGROUND = theme["page"]
SURFACE = theme["chart"]
GRID = theme["grid"]
TEXT = "#E7EEF5"
MUTED = theme["muted"]

css = """
    <style>
    :root {
      color-scheme: __SCHEME__;
      --background-color: __PAGE__; --secondary-background-color: __SURFACE__;
      --text-color: __TEXT__; --primary-color: __ACCENT__;
      --page-bg: __PAGE__; --surface: __SURFACE__; --text: __TEXT__; --muted: __MUTED__;
      --accent: __ACCENT__; --sidebar: __SIDEBAR__; --sidebar-text: __SIDEBAR_TEXT__;
      --input: __INPUT__; --grid: __GRID__;
    }
    .stApp { background: var(--page-bg); color: var(--text); }
    [data-testid="stHeader"] { background: var(--page-bg); }
    [data-testid="stSidebar"] { background: var(--sidebar); border-right: 1px solid var(--grid); }
    [data-testid="stSidebar"] * { color: var(--sidebar-text); }
    [data-testid="stSidebar"] [data-testid="stDateInput"] input {
      color: var(--sidebar-text) !important; -webkit-text-fill-color: var(--sidebar-text) !important;
      background: var(--input) !important; border-color: var(--grid) !important;
    }
    [data-testid="stSidebar"] [data-testid="stDateInput"] button {
      color: var(--sidebar-text) !important; background: var(--input) !important;
    }
    [data-testid="stSidebar"] [data-baseweb="select"] > div {
      color: var(--sidebar-text) !important; background: var(--input) !important; border-color: var(--grid) !important;
    }
    [data-testid="stSidebar"] [data-baseweb="select"] input { color: var(--sidebar-text) !important; }
    [data-testid="stSidebar"] [data-testid="stCheckbox"] label,
    [data-testid="stSidebar"] [data-testid="stToggle"] label { color: var(--sidebar-text) !important; }
    .block-container { max-width: 1540px; padding-top: 1.4rem; padding-bottom: 3rem; }
    [data-testid="stMetric"] {
      background: var(--surface); color: var(--text); border: 1px solid var(--grid); border-top: 2px solid var(--accent);
      border-radius: 3px; padding: 13px 16px; min-height: 96px;
    }
    [data-testid="stMetricLabel"] { color: var(--muted); font-size: .76rem; letter-spacing: .035em; }
    [data-testid="stMetricValue"] { color: var(--text); font-family: Georgia, serif; font-size: 1.85rem; font-weight: 500; }
    div[data-testid="stTabs"] { border-bottom: 1px solid var(--grid); }
    div[data-testid="stTabs"] button { color: var(--muted); font-size: .92rem; font-weight: 600; }
    div[data-testid="stTabs"] button[aria-selected="true"] {
      color: var(--text); border-bottom-color: var(--accent);
    }
    .eyebrow { color: var(--accent); font: 700 .7rem/1.2 'Segoe UI', Arial, sans-serif;
      letter-spacing: .16em; text-transform: uppercase; margin-bottom: .7rem; }
    .hero-title { color: var(--text); font: 500 clamp(2.4rem, 4.6vw, 4.3rem)/.98 Georgia, 'Times New Roman', serif;
      letter-spacing: -.045em; margin: 0; }
    .hero-copy { color: var(--muted); font: 400 1rem/1.6 'Segoe UI', Arial, sans-serif; margin-top: .8rem; max-width: 45rem; }
    .status-pill { display: inline-block; color: var(--muted); border-left: 2px solid var(--accent);
      padding: .25rem 0 .25rem .65rem; font: 650 .69rem/1.2 'Segoe UI', Arial, sans-serif;
      letter-spacing: .13em; white-space: nowrap; }
    .section-kicker { color: var(--accent); text-transform: uppercase; letter-spacing: .15em;
      font: 700 .67rem/1.2 'Segoe UI', Arial, sans-serif; margin-bottom: .55rem; }
    .note-card { background: var(--sidebar); border-left: 3px solid var(--accent); border-radius: 2px;
      padding: 14px 18px; color: var(--sidebar-text); font: 400 .9rem/1.55 'Segoe UI', Arial, sans-serif; }
    .note-card strong { color: var(--sidebar-text); font-weight: 650; }
    [data-testid="stMain"] h1, [data-testid="stMain"] h2, [data-testid="stMain"] h3,
    [data-testid="stMain"] h4, [data-testid="stMain"] p, [data-testid="stMain"] li,
    [data-testid="stMain"] label { color: var(--text); }
    [data-testid="stPlotlyChart"] { background: __CHART__; border: 1px solid var(--grid); padding: 8px; }
    [data-testid="stDataFrame"] { border: 1px solid var(--grid); }
    button[kind="primary"] { background: var(--accent); border-color: var(--accent); }
    hr { border-color: var(--grid) !important; }
    html { scroll-behavior: smooth; }
    [data-testid="stPlotlyChart"] > div { transition: opacity .12s ease-in-out; }
    @media (max-width: 700px) {
      .block-container { padding: 1.1rem 1rem 2rem; }
      .hero-title { font-size: 2.55rem; }
      [data-testid="stMetricValue"] { font-size: 1.45rem; }
    }
    </style>
    """
for token, color in {
    "__SCHEME__": theme["scheme"], "__PAGE__": theme["page"], "__SURFACE__": theme["surface"],
    "__TEXT__": theme["text"], "__MUTED__": theme["muted"], "__ACCENT__": theme["accent"],
    "__SIDEBAR__": theme["sidebar"], "__SIDEBAR_TEXT__": theme["sidebar_text"],
    "__INPUT__": theme["input"], "__GRID__": theme["grid"], "__CHART__": theme["chart"],
}.items():
    css = css.replace(token, color)
st.markdown(css, unsafe_allow_html=True)


@st.cache_data(show_spinner="Loading saved analysis…")
def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    monitoring = pd.read_csv(MONITORING_FILE, parse_dates=["window_start", "window_end"])
    features = pd.read_csv(FEATURES_FILE)
    event_summary = pd.read_csv(EVENTS_FILE, parse_dates=["start", "end"])
    transitions = pd.read_csv(TRANSITIONS_FILE, index_col=0)
    metadata = json.loads(MODEL_FILE.read_text(encoding="utf-8"))

    missing = REQUIRED_MONITORING.difference(monitoring.columns)
    if missing:
        raise ValueError(f"Monitoring output is missing columns: {', '.join(sorted(missing))}")
    keys = ["segment_id", "window_id"]
    if not set(keys).issubset(features.columns):
        raise ValueError("Feature output needs segment_id and window_id columns.")
    if monitoring.duplicated(keys).any() or features.duplicated(keys).any():
        raise ValueError("Saved window files contain duplicate segment/window keys.")
    combined = monitoring.merge(features, on=keys, how="left", validate="one_to_one")
    return combined, event_summary, transitions, metadata


def chart_layout(fig: go.Figure, *, height: int = 360) -> go.Figure:
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
        font={"family": "Inter, Segoe UI, sans-serif", "color": TEXT, "size": 12},
        colorway=PALETTE,
        height=height,
        margin={"l": 58, "r": 24, "t": 78, "b": 52},
        legend={
            "orientation": "h", "y": 1.0, "yanchor": "top", "x": 0,
            "title": {"text": ""}, "bgcolor": "rgba(0,0,0,0)", "tracegroupgap": 8,
        },
        uirevision="compressor-dashboard",
        transition={"duration": 0},
        hoverlabel={"bgcolor": "#202D39", "bordercolor": GRID, "font": {"color": TEXT}},
    )
    fig.update_xaxes(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID)
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID)
    return fig


def require_outputs() -> bool:
    expected = [MONITORING_FILE, FEATURES_FILE, EVENTS_FILE, TRANSITIONS_FILE, MODEL_FILE]
    absent = [p.relative_to(ROOT).as_posix() for p in expected if not p.is_file()]
    if absent:
        st.error("Saved analysis files are missing. Run notebooks 01–04 and save their outputs first.")
        st.code("\n".join(absent), language="text")
        return False
    return True


def event_spans(fig: go.Figure, start: pd.Timestamp, end: pd.Timestamp) -> None:
    spans = [
        ("Event 1", "2020-04-18 00:00", "2020-04-18 23:59"),
        ("Event 2", "2020-05-29 23:30", "2020-05-30 06:00"),
        ("Event 3", "2020-06-05 10:00", "2020-06-07 14:30"),
        ("Event 4", "2020-07-15 14:30", "2020-07-15 19:00"),
    ]
    for label, raw_start, raw_end in spans:
        left, right = pd.Timestamp(raw_start), pd.Timestamp(raw_end)
        if left <= end and right >= start:
            fig.add_vrect(
                x0=max(left, start), x1=min(right, end),
                fillcolor="#F07878", opacity=.13, line_width=0,
                annotation_text=label, annotation_position="top left",
            )


st.markdown('<div class="eyebrow">Independent condition study &nbsp; / &nbsp; MetroPT-3</div>', unsafe_allow_html=True)
header_left, header_right = st.columns([4, 1], vertical_alignment="center")
with header_left:
    st.markdown('<h1 class="hero-title">Reading the machine.</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="hero-copy">A field guide to compressor behavior. Explore learned operating states, reported events, and the windows that deserve a closer look.</p>',
        unsafe_allow_html=True,
    )
with header_right:
    st.markdown('<div class="status-pill">HISTORICAL DATA<br>LOCAL ANALYSIS</div>', unsafe_allow_html=True)
st.write("")

if not require_outputs():
    st.stop()
try:
    data, event_summary, transitions, metadata = load_data()
except Exception:
    st.error("Could not load the saved outputs. Check that the notebook files are complete, then restart the dashboard.")
    st.stop()
if data.empty or data["window_start"].dropna().empty:
    st.warning("There are no assigned windows with valid timestamps in the saved monitoring output.")
    st.stop()

clusters = sorted(int(value) for value in data["cluster"].dropna().unique())
min_day, max_day = data["window_start"].min().date(), data["window_start"].max().date()
with st.sidebar:
    st.markdown("### Analysis controls", unsafe_allow_html=True)
    st.caption("METROPT-3 / 5-MINUTE WINDOWS")
    st.divider()
    st.markdown("#### Filters")
    date_range = st.date_input(
        "Analysis period", value=(min_day, max_day), min_value=min_day, max_value=max_day,
        help="Filters all charts and the window explorer by window start time.",
    )
    selected_clusters = st.multiselect("Operating clusters", clusters, default=clusters)
    show_events = st.toggle("Show reported event periods", value=True)
    alerts_only = st.toggle("Only unusual windows", value=False)
    st.divider()
    st.markdown("#### Model context")
    st.caption(f"Provisional K-Means · k={metadata.get('provisional_k', 'unknown')}")
    st.caption(f"Window size · {metadata.get('window', '5min')}")
    st.caption("Exploratory model · not a validated alarm system")

if date_range is None:
    first_day, last_day = min_day, max_day
elif isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    first_day, last_day = date_range
elif isinstance(date_range, (tuple, list)) and len(date_range) == 1:
    first_day = last_day = date_range[0]
elif isinstance(date_range, (tuple, list)) and len(date_range) == 0:
    first_day, last_day = min_day, max_day
else:
    first_day = last_day = date_range
range_start = pd.Timestamp(first_day)
range_end = pd.Timestamp(last_day) + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
filtered = data.loc[
    data["window_start"].between(range_start, range_end)
    & data["cluster"].isin(selected_clusters)
].copy()
if alerts_only:
    filtered = filtered.loc[
        filtered["distance_alert"].fillna(False)
        | filtered["persistent_unusual_behavior"].fillna(False)
    ].copy()

distance_alerts = int(filtered["distance_alert"].fillna(False).sum())
persistent = int(filtered["persistent_unusual_behavior"].fillna(False).sum())
event_windows = int(filtered["reported_event_ids"].fillna("").ne("").sum())
st.markdown('<div class="section-kicker">At a glance</div>', unsafe_allow_html=True)
kpis = st.columns(5)
kpis[0].metric("Windows in view", f"{len(filtered):,}")
kpis[1].metric("Clusters present", f"{filtered['cluster'].nunique()}")
kpis[2].metric("Distance alerts", f"{distance_alerts:,}")
kpis[3].metric("Persistent flags", f"{persistent:,}")
kpis[4].metric("Event-overlap windows", f"{event_windows:,}")
st.write("")

active_view = st.segmented_control(
    "Dashboard section", ["Overview", "Event review", "Window explorer"],
    horizontal=True, label_visibility="collapsed",
)
if active_view == "Overview":
    if filtered.empty:
        st.info("No windows match these filters. Adjust the date range or cluster selection in the sidebar.")
    else:
        st.markdown('<div class="section-kicker">Behavior over time</div>', unsafe_allow_html=True)
        st.subheader("Operating-state timeline")
        st.caption("Cluster IDs represent learned groups; their numeric order does not indicate health severity.")
        timeline = filtered.sort_values("window_start")
        if len(timeline) > 6_000:
            step = math.ceil(len(timeline) / 6_000)
            keep = timeline.loc[
                timeline["distance_alert"].fillna(False)
                | timeline["persistent_unusual_behavior"].fillna(False)
            ]
            timeline = pd.concat([timeline.iloc[::step], keep]).drop_duplicates(
                ["segment_id", "window_id"]
            ).sort_values("window_start")
        timeline["cluster_label"] = timeline["cluster"].astype(str)
        timeline_fig = px.scatter(
            timeline, x="window_start", y="cluster", color="cluster_label",
            color_discrete_sequence=PALETTE, render_mode="webgl",
            hover_data={
                "window_end": True, "nearest_center_distance": ":.2f",
                "distance_threshold": ":.2f", "reported_event_ids": True,
                "cluster": True, "cluster_label": False,
            },
            labels={"window_start": "Window start", "cluster": "Cluster ID", "cluster_label": "Cluster"},
        )
        timeline_fig.update_traces(marker={"size": 5, "opacity": .72})
        flagged = timeline.loc[timeline["persistent_unusual_behavior"].fillna(False)]
        if not flagged.empty:
            timeline_fig.add_trace(go.Scatter(
                x=flagged["window_start"], y=flagged["cluster"], mode="markers",
                name="Persistent flag", marker={"symbol": "x", "size": 11, "color": "#FF7777"},
                customdata=flagged[["nearest_center_distance", "reported_event_ids"]],
                hovertemplate="Persistent flag<br>%{x}<br>Distance: %{customdata[0]:.2f}<br>Event: %{customdata[1]}<extra></extra>",
            ))
        if show_events:
            event_spans(timeline_fig, range_start, range_end)
        chart_layout(timeline_fig, height=420)
        timeline_fig.update_layout(yaxis={"dtick": 1, "title": "Arbitrary cluster ID"})
        st.plotly_chart(timeline_fig, use_container_width=True)

        left, right = st.columns([1.15, 1])
        with left:
            st.markdown("#### Daily operating mix")
            granularity = st.segmented_control(
                "Time grouping", ["Daily", "Weekly"], default="Daily", label_visibility="collapsed"
            )
            freq = "D" if granularity == "Daily" else "W-SUN"
            grouped = filtered.assign(period=filtered["window_start"].dt.to_period(freq).dt.start_time)
            counts = grouped.groupby(["period", "cluster"]).size().rename("windows").reset_index()
            counts["share"] = counts["windows"] / counts.groupby("period")["windows"].transform("sum")
            counts["cluster_label"] = counts["cluster"].astype(str)
            mix_fig = px.area(
                counts, x="period", y="share", color="cluster_label",
                category_orders={"cluster_label": [str(c) for c in clusters if c in selected_clusters]},
                color_discrete_sequence=PALETTE,
                labels={"period": "Period", "share": "Share of assigned windows", "cluster_label": "Cluster"},
            )
            chart_layout(mix_fig, height=340)
            mix_fig.update_yaxes(tickformat=".0%", range=[0, 1])
            st.plotly_chart(mix_fig, use_container_width=True)
        with right:
            st.markdown("#### Sensor signature")
            choices = {label: item for label, item in SENSOR_FIELDS.items() if item[0] in filtered.columns}
            if choices:
                sensor_label = st.selectbox("Sensor feature", list(choices), label_visibility="collapsed")
                sensor_col, unit = choices[sensor_label]
                sensor_rows = filtered[["window_start", "cluster", sensor_col]].dropna().sort_values("window_start").copy()
                sensor_rows["cluster_label"] = sensor_rows["cluster"].astype(str)
                if len(sensor_rows) > 4_000:
                    sensor_rows = sensor_rows.iloc[::math.ceil(len(sensor_rows) / 4_000)]
                sensor_fig = px.scatter(
                    sensor_rows, x="window_start", y=sensor_col, color="cluster_label",
                    color_discrete_sequence=PALETTE,
                    labels={"window_start": "Window start", sensor_col: f"{sensor_label} ({unit})", "cluster_label": "Cluster"},
                )
                sensor_fig.update_traces(marker={"size": 5, "opacity": .62})
                chart_layout(sensor_fig, height=340)
                st.plotly_chart(sensor_fig, use_container_width=True)
            else:
                st.info("No recognized sensor summary features are present in the saved feature table.")

        st.markdown(
            '<div class="note-card"><strong>How to read this view:</strong> cluster changes show shifts in feature patterns, '
            'not confirmed faults. Distance alerts are exploratory review flags based on training references.</div>',
            unsafe_allow_html=True,
        )

elif active_view == "Event review":
    st.markdown('<div class="section-kicker">Retrospective annotations</div>', unsafe_allow_html=True)
    st.subheader("Reported event review")
    st.caption("These source-document event periods are not row-level verified labels. All four overlap the model training period.")
    if event_summary.empty:
        st.info("The saved run contains no event summary rows.")
    else:
        visible_events = event_summary.loc[
            (event_summary["start"] <= range_end) & (event_summary["end"] >= range_start)
        ].copy()
        if alerts_only:
            st.info("The unusual-window filter applies to window-level charts and tables; event records remain source annotations.")
        if visible_events.empty:
            st.info("No annotated event period overlaps the selected date range.")
        else:
            st.dataframe(
                visible_events.rename(columns={
                    "event_id": "Event", "reported_type": "Reported type", "start": "Start",
                    "end": "End", "overlapping_windows": "Overlapping windows",
                    "distance_alert_windows": "Distance alerts", "persistent_unusual_windows": "Persistent flags",
                    "median_center_distance": "Median distance",
                }).style.format({"Median distance": "{:.2f}"}),
                use_container_width=True, hide_index=True,
            )
            event_total = int(visible_events["overlapping_windows"].sum())
            alert_total = int(visible_events["distance_alert_windows"].sum())
            persistent_total = int(visible_events["persistent_unusual_windows"].sum())
            ec = st.columns(3)
            ec[0].metric("Windows overlapping events", f"{event_total:,}")
            ec[1].metric("Distance alerts in events", f"{alert_total:,}")
            ec[2].metric("Persistent flags in events", f"{persistent_total:,}")
    with st.expander("Interpretation and caveats"):
        st.markdown(
            "The event windows are retrospective annotations copied from the project reference material. "
            "The source contains an inconsistent maintenance-date note for event 2. The saved distance threshold "
            "is a cluster-specific 99th-percentile reference, not an engineering alarm limit."
        )

else:
    st.markdown('<div class="section-kicker">Window-level inspection</div>', unsafe_allow_html=True)
    st.subheader("Explore assigned windows")
    st.caption("Filter the dashboard first, then inspect or export the matching 5-minute windows.")
    if filtered.empty:
        st.info("No windows match the current filters.")
    else:
        export_cols = [
            col for col in ["window_start", "window_end", "segment_id", "window_id", "partition", "cluster",
                            "coverage_fraction", "nearest_center_distance", "distance_threshold", "distance_alert",
                            "persistent_unusual_behavior", "reported_event_ids"]
            if col in filtered.columns
        ]
        details = filtered[export_cols].copy()
        if "nearest_center_distance" in details and "distance_threshold" in details:
            safe_threshold = details["distance_threshold"].where(details["distance_threshold"].ne(0))
            details["distance_ratio"] = details["nearest_center_distance"] / safe_threshold
            details = details.sort_values("distance_ratio", ascending=False, na_position="last")
        max_rows = min(500, len(details))
        row_limit = st.slider("Rows to display", min_value=25, max_value=max(25, max_rows), value=min(100, max(25, max_rows)), step=25)
        st.dataframe(details.head(row_limit), use_container_width=True, hide_index=True)
        st.download_button(
            "Download filtered windows (CSV)",
            data=details.to_csv(index=False).encode("utf-8"),
            file_name="compressor_filtered_windows.csv", mime="text/csv",
            type="primary",
        )
        st.caption(f"Showing {min(row_limit, len(details)):,} of {len(details):,} filtered windows. Download includes all filtered rows.")

st.divider()
footer_left, footer_right = st.columns([3, 1])
with footer_left:
    st.caption("Compressor Health Clustering · MetroPT-3 · Local saved outputs")
with footer_right:
    st.caption("Exploratory · Not live monitoring")
