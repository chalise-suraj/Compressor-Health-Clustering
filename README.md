# Compressor Health Clustering

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Streamlit-Interactive%20dashboard-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Streamlit dashboard">
  <img src="https://img.shields.io/badge/Model-K--Means-147D74?style=for-the-badge" alt="K-Means clustering">
  <img src="https://img.shields.io/badge/Status-Exploratory%20research%20prototype-B87924?style=for-the-badge" alt="Exploratory research prototype">
</p>

> **Project status: exploratory model + historical dashboard**
>
> The saved k=4 model groups operating patterns. It is **not a validated fault detector, health score, or failure predictor**.

This project analyzes the MetroPT-3 air-compressor sensor data. It turns the chronological sensor stream into five-minute windows, uses K-Means to group similar operating behavior, and reviews cluster changes and unusual windows alongside the documented event periods.

**Quick links:** [Project goal](Project_Goal.md) · [Model details](Model.md) · [Run the dashboard](#run-the-dashboard) · [Run the notebooks](#reproduce-the-notebooks) · [Limitations](#limitations)

## At a glance

| Data | Current model | Saved-run summary | Dashboard |
|---|---|---|---|
| 1,516,948 timestamped source rows | Provisional K-Means, k=4 | 50,584 five-minute windows; 50,437 assigned and 147 low-coverage windows left unassigned | Historical operating-state timeline, event review, sensor trends, unusual-window table, CSV export |
| 15 sensor signals plus timestamp | 37 engineered numeric features | 484 single-window distance alerts; 7 windows in persistent-alert runs | Date, cluster, alert, and palette controls |

These results describe this saved analysis. The cluster labels are arbitrary and do not rank compressor health.

## What does a “window” mean?

A **window** is one five-minute period of sensor readings. Notebook 02 summarizes readings in each period—for example, pressure averages and ranges, digital-state fractions, and state transitions. The model assigns each eligible window to an operating-pattern cluster.

The dataset’s observed median sample interval is 10 seconds, so a typical five-minute window contains about 30 rows. Windows are not formed across timestamp gaps greater than 30 seconds, and windows below the 80% coverage threshold are excluded from the initial model fit.

## Data source and preparation

The project uses the [MetroPT-3 dataset from the UCI Machine Learning Repository](https://archive.ics.uci.edu/dataset/791/metropt%2B3%2B). The raw CSV and its accompanying data-description PDF are stored under `data/raw/`. The original data are not modified.

The supplied CSV contains 1,516,948 rows, a timestamp, and 15 sensor signals. The observed cadence is about 10 seconds, despite the dataset description referring to a 1 Hz logging rate. There are 331 timestamp gaps longer than 30 seconds; these split the data into 332 continuous segments. The source contains no row-level failure labels.

## Modeling workflow

1. **Understand the data** — check schema, timestamps, sampling intervals, missing values, duplicates, sensor distributions, and reported event documentation.
2. **Design windows and features** — compare candidate non-overlapping durations, split at long gaps, and create sensor summaries while keeping timestamps and identifiers out of the model matrix.
3. **Compare cluster counts** — evaluate k=2–8 with inertia, sampled silhouette, cluster sizes, and stability; reserve the latest 20% of eligible windows as a chronological holdout.
4. **Fit the reusable pipeline** — fit median imputation and robust scaling on training data only, then fit K-Means and assign later holdout windows without refitting.
5. **Review behavior** — compare temporal cluster frequencies, score distance to cluster centers, flag persistent unusual windows, and make a retrospective comparison with the documented event dates.
6. **Explore saved results** — use the Streamlit dashboard to filter, inspect, and export the saved analysis.

Run notebooks in order because each stage reads files saved by the prior stage.

## Current model and results

The saved pipeline uses k=4 as a **provisional analysis choice**, not as a final model selection. In the candidate comparison, sampled training silhouette was highest at k=3 (0.9429), versus 0.9375 at k=4. The k=4 assignments were stable across the two tested initializations (ARI 1.0000), but initialization stability does not prove that k=4 is the best representation.

The cluster mix changes substantially in the chronological holdout: cluster 0 rises from 88.74% of training windows to 95.25% of holdout windows. Cluster 1 falls from 2,935 training windows to 8 holdout windows. Clusters 2 and 3 have nearly identical selected feature profiles. These are reasons to review the cluster count and temporal behavior—not evidence of a fault.

The monitoring rule generated 484 individual distance alerts. Seven windows belonged to runs meeting the three-adjacent-window persistence rule. None of the four documented events had a persistent alert during the event or in the 24 hours before it. All four events fall inside the training period, so this comparison is retrospective and in-sample, not independent validation.

See [Model.md](Model.md) for the methods, artifact names, detailed metrics, and interpretation limits.

## The interactive dashboard

The local Streamlit app reads saved files from `data/processed/` and model metadata from `models/`. It does not train the model or connect to live equipment.

It provides an operating-state timeline, daily or weekly cluster mix, selectable sensor trends, retrospective event review, and a filtered window table with CSV export. Sidebar controls filter the date range, clusters, and unusual windows. Several color palettes are available, including Graphite.

### Run the dashboard

From the project root in PowerShell, activate the virtual environment and start Streamlit:

```powershell
.\.venv\Scripts\Activate.ps1
streamlit run app.py
```

Open the local URL shown in the terminal. If you have an earlier server running, stop it with **Ctrl+C** before restarting so it loads the latest app and theme settings.

## Reproduce the notebooks

Use the project virtual environment, select it as the notebook kernel, and run each notebook from top to bottom. Save outputs after each notebook before moving to the next.

1. `notebooks/01_data_understanding.ipynb`
2. `notebooks/02_feature_engineering.ipynb`
3. `notebooks/03_kmeans_clustering.ipynb`
4. `notebooks/04_condition_monitoring.ipynb`

Notebook 02 creates the feature and metadata tables. Notebook 03 creates the fitted pipeline, model metadata, and cluster assignments. Notebook 04 creates the monitoring, event, and transition summaries used by the dashboard.

## Repository map

| Path | Contents |
|---|---|
| `data/raw/` | Original MetroPT-3 CSV and data-description PDF |
| `data/processed/` | Five-minute features, window metadata, assignments, and monitoring summaries |
| `notebooks/` | Data understanding, feature engineering, clustering, and condition monitoring |
| `models/` | Saved K-Means pipeline and model metadata |
| `reports/` | Analysis figures and generated reports |
| `app.py` | Offline Streamlit dashboard |
| `.streamlit/config.toml` | Default dashboard theme and client settings |
| `Model.md` | Model design, saved metrics, artifacts, and interpretation |
| `Project_Goal.md` | Project aim, scope, success criteria, and limitations |

## Project documents

- [Project goal](Project_Goal.md) — intended use, requirements, success criteria, roadmap, and project-wide limitations.
- [Model details](Model.md) — current pipeline, training/evaluation design, saved findings, and model-specific limitations.

## Limitations

- The dataset has coarse, retrospective event reports rather than row-level fault labels. One maintenance note in the source material has an inconsistent date.
- All four reported event periods are inside the training period, so the event comparison does not measure prospective warning performance.
- k=4 is provisional; k=3 had the highest sampled silhouette in the candidate comparison, and two k=4 profiles were nearly identical.
- Cluster IDs are arbitrary. Distance thresholds are exploratory 99th-percentile references, not validated alarm limits.
- The data cover one compressor over one historical period. Results do not establish generalization to other machines, time periods, or operating conditions.
- The dashboard is offline. Its alerts do not confirm faults, provide failure probabilities, or replace engineering review.
